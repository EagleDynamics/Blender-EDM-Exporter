import re
import math
from typing import List, Union, Tuple, Union, Sequence, Callable

from mathutils import Vector, Matrix
from bpy.types import (
    Object,
    Material,
    ShaderNodeGroup,
)

import utils
from logger import log
import animation as anim
from mesh_builder import get_mesh
from objects_custom_props import get_edm_props 
from pyedm_platform_selector import pyedm
from materials.material_interface import IMaterial
from materials.material_wrap import (
    TextureDesk,
    ValueDesk,
    g_missing_texture_name,
)
from materials.material_fake_common import (
    FakeLightIndex, 
    FakeLightDelay, 
    parse_faces, 
    get_pos, 
    get_delay_anim_list,
)
from enums import (
    ObjectTypeEnum,
    BpyNodeSocketType,
    NodeSocketCommonEnum,
    NodeSocketInFakeSpotEnum,
)

FAKE_SPOT_MATERIAL_NAME = 'EDM_Fake_Spot_Material'

ObjectCheckFn = Callable[[Object], bool]

fake_light_dir_re_c = re.compile(r'^([Ll]ight_[Dd]ir(ection)?|[Ll][Dd])')
def fake_light_obj_test(obj: Object) -> bool:
    is_type_match: bool = obj.type == ObjectTypeEnum.EMPTY
    is_name_match: bool = re.match(fake_light_dir_re_c, obj.name)
    return is_type_match and is_name_match

def get_first_children(object_children: Sequence[Object], obj_fn: ObjectCheckFn) -> Union[Object, None]:
    if not object_children:
        return None
    for child_obj in object_children:
        is_obj_match: bool = obj_fn(child_obj)
        if is_obj_match:
            return child_obj
    return None

def get_children(object_children: Sequence[Object], obj_fn: ObjectCheckFn) -> List[Object]:
    result: List[Object] = []
    if not object_children:
        return result
    for child_obj in object_children:
        is_obj_match: bool = obj_fn(child_obj)
        if is_obj_match:
            result.append(child_obj)
    return result

def check_fake_light_direction(object: Object) -> None:
    chilren_dir: List[Object] = get_children(object.children, fake_light_obj_test)

    if len(chilren_dir) > 1:
        log.warning(f"{object.name} fake spot light has more then one child direction objects.")
        for chold_obj in chilren_dir:
            log.warning(f"{chold_obj.name} -- fake spot light child direction.")

## return coordinates (x, y, z) of light in local space. 
## later in shader we will transform this vector to 
##                           1) world space (analogue to object.matrix_world)
##                           2) dcs space (see ROOT_TRANSFORM_MATRIX)
def get_fake_light_direction(object: Object) -> Tuple[float, float, float]:
    # take only x-coordinate
    light_direction: Tuple[float, float, float] = (1.0, 0.0, 0.0)
    
    check_fake_light_direction(object)
    light_dir_obj = get_first_children(object.children, fake_light_obj_test)
    if light_dir_obj:
        local_matrix: Matrix = light_dir_obj.matrix_local
    else:
        return light_direction
        
    loc, rot, sca = local_matrix.decompose()
    rot_mat = rot.to_matrix()
    trans_ld: Vector = rot_mat @ Vector(light_direction)
    return trans_ld.to_tuple()

## Fake Spot light material
class SpotFakeLightsMaterial(IMaterial):
    name = FAKE_SPOT_MATERIAL_NAME
    description_file_name = f'data/{FAKE_SPOT_MATERIAL_NAME}.pickle'
    node_group_name = 'EdmFakeSpotShaderNodeType'

    class Textures:
        def __init__(self, node_group: ShaderNodeGroup) -> None:
            self.emissive   = TextureDesk(node_group, NodeSocketInFakeSpotEnum.EMISSIVE, BpyNodeSocketType.COLOR)

    class Values:
        def __init__(self, node_group: ShaderNodeGroup) -> None:
            self.luminance          = ValueDesk(node_group, NodeSocketInFakeSpotEnum.LUMINANCE, BpyNodeSocketType.FLOAT, 1.0)
            self.min_size_pixels    = ValueDesk(node_group, NodeSocketInFakeSpotEnum.MIN_SIZE_PIXELS, BpyNodeSocketType.FLOAT, 4.0)
            self.max_distance       = ValueDesk(node_group, NodeSocketInFakeSpotEnum.MAX_DISTANCE, BpyNodeSocketType.FLOAT, 1000.0)
            self.shift_to_camera    = ValueDesk(node_group, NodeSocketInFakeSpotEnum.SHIFT_TO_CAMERA, BpyNodeSocketType.FLOAT, 0.0)
            self.phi                = ValueDesk(node_group, NodeSocketInFakeSpotEnum.PHI, BpyNodeSocketType.FLOAT, 45.0)
            self.theta              = ValueDesk(node_group, NodeSocketInFakeSpotEnum.THETA, BpyNodeSocketType.FLOAT, 25.0)
            self.version            = ValueDesk(node_group, NodeSocketCommonEnum.VERSION, BpyNodeSocketType.INTEGER, -1)

    def __init__(self, bpy_material: Material, node_group: ShaderNodeGroup):
        self.bpy_material = bpy_material
        self.node_group = node_group
        self.is_valid = not self.node_group == None
        
        self.textures = SpotFakeLightsMaterial.Textures(self.node_group)
        self.values = SpotFakeLightsMaterial.Values(self.node_group)

        if self.is_valid:
            # apply
            for attr in self.textures.__dict__.keys():
                getattr(self.textures, attr).apply(self.node_group)
            for attr in self.values.__dict__.keys():
                getattr(self.values, attr).apply(self.node_group)

            # update
            for i in self.textures.__dict__.keys():
                getattr(self.textures, i).update()
            for i in self.values.__dict__.keys():
                getattr(self.values, i).update() 

    def build_blocks(self, object, mesh_storage):
        edm_props = get_edm_props(object)

        is_color_texture: bool = not self.textures.emissive.texture == None
        if is_color_texture:
            light_texture: str = self.textures.emissive.texture.texture_name
        else:
            light_texture: str = g_missing_texture_name
            log.warning(f"{object.name} fake spot must have emissive texture.")
        
        min_size_pixels: float = self.values.min_size_pixels.value
        max_distance: float = self.values.max_distance.value
        shift_to_camera: float = self.values.shift_to_camera.value
        luminance: float = self.values.luminance.value
        
        brightness_animation_path: str = 'EDMProps.ANIMATED_BRIGHTNESS'
        is_brightness_animated: bool = anim.has_path_anim(object.animation_data, brightness_animation_path)
        brightness_arg_n: int = utils.extract_arg_number(object.animation_data.action.name) if is_brightness_animated else -1
        
        # spot light characteristics
        phi: float = self.values.phi.value
        theta: float = self.values.theta.value
        cone_setup: Tuple[float, float, float] = (
            math.cos(math.radians(theta)),  #cos of inner cone angle
            math.cos(math.radians(phi)),    #cos of outer cone angle
            0.05                            #min attenuation value
        )

        light_direction = None
        if not edm_props.SURFACE_MODE:
            two_sided: bool = edm_props.TWO_SIDED
            uv_start: Tuple[float, float] = edm_props.UV_LB[0], edm_props.UV_LB[1]
            uv_end: Tuple[float, float] = edm_props.UV_RT[0], edm_props.UV_RT[1]
            uv_start_back: Tuple[float, float] = edm_props.UV_LB_BACK[0], edm_props.UV_LB_BACK[1]
            uv_end_back: Tuple[float, float] = edm_props.UV_RT_BACK[0], edm_props.UV_RT_BACK[1]
            light_size: float = edm_props.SIZE 
            
            # single light direction   
            light_direction = get_fake_light_direction(object) #: Tuple[float, float, float]

        fake_lights: List[pyedm.FakeSpotLight] = []
        lights_anim_delay_list: List[FakeLightDelay] = [] # only for rabbit lights
        is_vertex_group_set: bool = False
        
        if object.type == ObjectTypeEnum.MESH:
            FakeLightIndex = 0
            bpy_mesh = get_mesh(object)

            if edm_props.SURFACE_MODE:
                centers, normals, light_sizes, uv_layers = parse_faces(bpy_mesh, object)
                uvs_front = uv_layers['front']

                for i, (center, light_size, uv_f) in enumerate(zip(centers, light_sizes, uvs_front)):
                    edm_fake_spot = pyedm.FakeSpotLight()
                    edm_fake_spot.setSize(float(light_size))
                    edm_fake_spot.setPos(tuple(center))
                    (pt1, pt2) = tuple(map(tuple, uv_f))
                    edm_fake_spot.setUV(pt1, pt2)         
                    if len(uv_layers) > 1:
                        edm_fake_spot.setBackSide(True)
                        (pt1, pt2) = tuple(map(tuple, uv_layers['back'][i]))
                        edm_fake_spot.setBackUV(pt1, pt2)
                    else:
                        edm_fake_spot.setBackSide(False)
                    edm_fake_spot.setDirection(normals[i]) # here local space 
                    
                    fake_lights.append(edm_fake_spot)

                    lights_anim_delay_list.append(0.0)
                    FakeLightIndex += 1
            else:
                for vertex in bpy_mesh.vertices:
                    pos: Tuple[float, float, float] = get_pos(vertex)
                    edm_fake_spot = pyedm.FakeSpotLight()
                    edm_fake_spot.setSize(light_size)
                    edm_fake_spot.setPos(pos)
                    edm_fake_spot.setUV(uv_start, uv_end)
                    edm_fake_spot.setBackSide(two_sided)
                    edm_fake_spot.setBackUV(uv_start_back, uv_end_back)
                    edm_fake_spot.setDirection(light_direction)
                    fake_lights.append(edm_fake_spot)
                    if len(vertex.groups) > 0:
                        is_vertex_group_set = True
                        lights_anim_delay_list.append(vertex.groups[0].weight)
                    else:
                        lights_anim_delay_list.append(0.0)
                    FakeLightIndex += 1
        elif object.type == ObjectTypeEnum.CURVE:
            pass

        if is_brightness_animated and brightness_arg_n == -1 and is_vertex_group_set:
            log.warning(f"{object.name} fake spot light has geometry animation but brightness action name not has arg.")
        
        ## no animation or rabbit lights
        edm_luminance_prop = pyedm.PropertyFloat(luminance)
            
        ## light animation: rabbit lights
        if is_brightness_animated and brightness_arg_n != -1 and is_vertex_group_set:
            edm_render_node = pyedm.AnimatedFakeSpotLight(object.name)
            key_list: anim.KeyFramePoints = anim.extract_anim_float(object.animation_data.action, brightness_animation_path)
            fake_lights_anim_list: List[FakeLightIndex, anim.KeyFramePoints] = get_delay_anim_list(lights_anim_delay_list, key_list)
            edm_render_node.setAnimationArg(brightness_arg_n)
            edm_render_node.setLightsAnimation(fake_lights_anim_list)
        ## light animation: flashing lamp
        elif is_brightness_animated and brightness_arg_n != -1 and not is_vertex_group_set:
            edm_render_node = pyedm.FakeSpotLights(object.name)
            ## keys of 'object luminance'
            key_list: anim.KeyFramePoints = anim.extract_anim_float(object.animation_data.action, brightness_animation_path)
            ## 'object luminance' is just a scale. so we need "key * 'luminance'"
            key_list = [(i[0], i[1] * luminance) for i in key_list]
            edm_luminance_prop = pyedm.PropertyFloat(brightness_arg_n, key_list)
        ## no animation
        else:
            edm_render_node = pyedm.FakeSpotLights(object.name)

        edm_render_node.setMinSizeInPixels(min_size_pixels)
        edm_render_node.setShiftToCamera(shift_to_camera)
        edm_render_node.setLuminance(edm_luminance_prop)
        edm_render_node.setConeSetup(cone_setup)
        edm_render_node.setMaxDistance(max_distance)    
        edm_render_node.setTexture(light_texture)
        edm_render_node.set(fake_lights)

        return edm_render_node
    
    @classmethod
    def process_links(cls, old_links, version, group_node_type_name):
        return old_links
    
    @classmethod
    def restore_defaults(cls, old_sockest, new_node_group, drop_down_values, old_version, material_name):
        pass
