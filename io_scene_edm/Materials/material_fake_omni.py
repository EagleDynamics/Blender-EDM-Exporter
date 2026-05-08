from typing import List, Tuple

from bpy.types import (
    Material,
    ShaderNodeGroup,
)

import utils
import animation as anim
from logger import log
from mesh_builder import get_mesh
from objects_custom_props import get_edm_props 
from pyedm_platform_selector import pyedm
from materials.material_interface import IMaterial
from materials.material_wrap import (
    TextureDesk,
    ValueDesk,
    g_missing_texture_name
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
    NodeSocketInFakeOmniEnum
)

FAKE_OMNI_MATERIAL_NAME = 'EDM_Fake_Omni_Material'

class OmniFakeLightsMaterial(IMaterial):
    name = FAKE_OMNI_MATERIAL_NAME  
    description_file_name = f'data/{FAKE_OMNI_MATERIAL_NAME}.pickle'
    node_group_name = 'EdmFakeOmniShaderNodeType'

    class Textures:
        def __init__(self, node_group: ShaderNodeGroup) -> None:
            self.emissive_map       = TextureDesk(node_group, NodeSocketInFakeOmniEnum.EMISSIVE, BpyNodeSocketType.COLOR)

    class Values:
        def __init__(self, node_group: ShaderNodeGroup) -> None:
            self.luminance          = ValueDesk(node_group, NodeSocketInFakeOmniEnum.LUMINANCE, BpyNodeSocketType.FLOAT, 1.0)
            self.min_size_pixels    = ValueDesk(node_group, NodeSocketInFakeOmniEnum.MIN_SIZE_PIXELS, BpyNodeSocketType.FLOAT, 4.0)
            self.max_distance       = ValueDesk(node_group, NodeSocketInFakeOmniEnum.MAX_DISTANCE, BpyNodeSocketType.FLOAT, 1000.0)
            self.shift_to_camera    = ValueDesk(node_group, NodeSocketInFakeOmniEnum.SHIFT_TO_CAMERA, BpyNodeSocketType.FLOAT, 0.0)
            self.version            = ValueDesk(node_group, NodeSocketCommonEnum.VERSION, BpyNodeSocketType.INTEGER, -1)

    def __init__(self, bpy_material: Material, node_group: ShaderNodeGroup):
        self.bpy_material = bpy_material
        self.node_group = node_group
        self.is_valid = not self.node_group == None
        
        self.textures = OmniFakeLightsMaterial.Textures(self.node_group)
        self.values = OmniFakeLightsMaterial.Values(self.node_group)

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
        
        is_color_texture: bool = not self.textures.emissive_map.texture == None
        if is_color_texture:
            light_texture: str = self.textures.emissive_map.texture.texture_name
        else:
            light_texture: str = g_missing_texture_name
            log.warning(f"{object.name} fake omni must have emissive texture.")
        
        min_size_pixels: float = self.values.min_size_pixels.value
        max_distance: float = self.values.max_distance.value
        shift_to_camera: float = self.values.shift_to_camera.value
        luminance: float = self.values.luminance.value

        brightness_animation_path: str = 'EDMProps.ANIMATED_BRIGHTNESS'
        is_brightness_animated: bool = anim.has_path_anim(object.animation_data, brightness_animation_path)
        brightness_arg_n: int = utils.extract_arg_number(object.animation_data.action.name) if is_brightness_animated else -1

        # only if surface mode is off
        if not edm_props.SURFACE_MODE:            
            uv_start: Tuple[float, float] = edm_props.UV_LB[0], edm_props.UV_LB[1]
            uv_end: Tuple[float, float] = edm_props.UV_RT[0], edm_props.UV_RT[1]
            light_size: float = edm_props.SIZE 
    
        fake_lights: List[pyedm.FakeOmniLight] = []
        is_vertex_group_set: bool = False
        
        if object.type == ObjectTypeEnum.MESH:
            bpy_mesh = get_mesh(object)

            if edm_props.SURFACE_MODE:  
                centers, normals, light_sizes, uv_layers = parse_faces(bpy_mesh, object)   
                uvs = uv_layers['front']

                for center, light_size, uv in zip(centers, light_sizes, uvs):
                    ## create omni light
                    edm_fake_omni = pyedm.FakeOmniLight()
                    edm_fake_omni.setSize(float(light_size))
                    edm_fake_omni.setPos(tuple(center))
                    (pt1, pt2) = tuple(map(tuple, uv))
                    edm_fake_omni.setUV(pt1, pt2)
                    fake_lights.append(edm_fake_omni)      
            else:
                lights_anim_delay_list: List[FakeLightDelay] = []
                FakeLightIndex = 0
                for vertex in bpy_mesh.vertices:
                    pos: Tuple[float, float, float] = get_pos(vertex)
                    edm_fake_omni = pyedm.FakeOmniLight()
                    edm_fake_omni.setSize(light_size)
                    edm_fake_omni.setPos(pos)
                    edm_fake_omni.setUV(uv_start, uv_end)
                    fake_lights.append(edm_fake_omni)
                    if len(vertex.groups) > 0:
                        is_vertex_group_set = True
                        lights_anim_delay_list.append(vertex.groups[0].weight)
                    else:
                        lights_anim_delay_list.append(0.0)
                    FakeLightIndex += 1
        elif object.type == ObjectTypeEnum.CURVE:
            pass

        if is_brightness_animated and brightness_arg_n == -1 and is_vertex_group_set:
            log.warning(f"{object.name} fake omni light has geometry animation but brightness action name not has arg.")

        edm_luminance_prop = pyedm.PropertyFloat(luminance)
        
        if is_brightness_animated and brightness_arg_n != -1 and is_vertex_group_set:
            if object.type == edm_props.SURFACE_MODE:
                log.debug("vertex groups are not supported for surface mode right now.")
            else:
                edm_render_node = pyedm.AnimatedFakeOmniLight(object.name)
                key_list: anim.KeyFramePoints = anim.extract_anim_float(object.animation_data.action, brightness_animation_path)
                fake_lights_anim_list: List[FakeLightIndex, anim.KeyFramePoints] = get_delay_anim_list(lights_anim_delay_list, key_list)
                edm_render_node.setAnimationArg(brightness_arg_n)
                edm_render_node.setLightsAnimation(fake_lights_anim_list)
        elif is_brightness_animated and brightness_arg_n != -1 and not is_vertex_group_set:
            edm_render_node = pyedm.FakeOmniLights(object.name)
            key_list: anim.KeyFramePoints = anim.extract_anim_float(object.animation_data.action, brightness_animation_path)
            key_list = [(i[0], i[1] * luminance) for i in key_list]
            edm_luminance_prop = pyedm.PropertyFloat(brightness_arg_n, key_list)
        else:
            edm_render_node = pyedm.FakeOmniLights(object.name)

        edm_render_node.setMinSizeInPixels(min_size_pixels)
        edm_render_node.setShiftToCamera(shift_to_camera)
        edm_render_node.setLuminance(edm_luminance_prop)
        edm_render_node.setTexture(light_texture)
        edm_render_node.setMaxDistance(max_distance)
        edm_render_node.set(fake_lights)

        return edm_render_node
        
    @classmethod
    def process_links(cls, old_links, version, group_node_type_name):
        return old_links
    
    @classmethod
    def restore_defaults(cls, old_sockest, new_node_group, drop_down_values, old_version, material_name):
        pass