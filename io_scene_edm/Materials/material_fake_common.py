## common methods for fake lights export
import math 
import numpy as np
import re

from typing import List, Union, Tuple, Union, Sequence, Callable
from enums import ObjectTypeEnum, EDMPropsSpecialTypeStr

import animation as anim
import bpy
from bpy.types import Object, Mesh, MeshVertex, MeshVertices
from mathutils import Vector, Quaternion, Matrix

from objects_custom_props import get_edm_props
from logger import log
from math_tools import ROOT_TRANSFORM_MATRIX
import utils

FakeLightIndex = int
FakeLightDelay = float
FakeLightIdxToFrameList = List[Tuple[FakeLightIndex, anim.KeyFramePoints]]

## constants
POINTS_COUNT = 4 ## each face has 4 vertices (this is expected)
DIM = 3 ## dimention


def is_fake_light(object: bpy.types.Object) -> bool:
    edm_props = get_edm_props(object)
    if object.type == ObjectTypeEnum.MESH and edm_props.SPECIAL_TYPE in ('FAKE_LIGHT'):
        return True
    return False

def get_delay_anim_list(lights_anim_delay_list: List[FakeLightDelay], key_list: anim.KeyFramePoints) -> FakeLightIdxToFrameList:
    fake_lights_anim_list: List[FakeLightIndex, anim.KeyFramePoints] = []
    if not key_list:
        return fake_lights_anim_list
    first_key_frame: anim.KeyFramePoint = key_list[0]
    for fake_light_index in range(0, len(lights_anim_delay_list)):
        delay: float = lights_anim_delay_list[fake_light_index]
        new_key_frame_points: anim.KeyFramePoints = []
        for key_frame_index in range(0, len(key_list)):
            key_frame: anim.KeyFramePoint = key_list[key_frame_index]
            #old_key_fame_time = key_frame[0]
            old_key_fame_time = key_frame[0] - first_key_frame[0]
            old_key_fame_point = key_frame[1]
            new_key_fame_time: float = np.clip(old_key_fame_time + delay, -1.0, 1.0)
            #new_key_fame_time_normalized: float = (new_key_fame_time + 1.0) * 0.5
            new_key_fame_time_normalized: float = new_key_fame_time * 0.5
            new_key: anim.KeyFrameTime = new_key_fame_time_normalized
            new_key_frame_points.append((new_key, old_key_fame_point))
        fake_lights_anim_list.append((fake_light_index, new_key_frame_points))
    return fake_lights_anim_list

def get_pos(vertex: MeshVertex) -> Tuple[float, float, float]:
    pos_x: float = vertex.co[0]
    pos_y: float = vertex.co[1]
    pos_z: float = vertex.co[2]
    return pos_x, pos_y, pos_z

def get_pos_list(vertices_list: MeshVertices) -> List[Tuple[float, float, float]]:
    pos_list: List[Tuple[float, float, float]] = []
    for vertex in vertices_list:
        pos1 = get_pos(vertex)
        pos_list.append(pos1)
    return pos_list

ObjectCheckFn = Callable[[Object], bool]

fake_light_dir_re_c = re.compile(r'^([Ll]ight_[Dd]ir(ection)?|[Ll][Dd])')
def fake_light_obj_test(obj: Object) -> bool:
    is_type_match: bool = obj.type == ObjectTypeEnum.EMPTY
    is_name_match: bool = re.match(fake_light_dir_re_c, obj.name)
    return is_type_match and is_name_match

## convert normal vector from blender coordinate system to edm coordinate system
def convert_coordinates(normals: np.array, object: Object) -> Tuple[float, float, float]:
    
    #normals = np.matmul(normals, np.array(ROOT_TRANSFORM_MATRIX.to_3x3() @ object.matrix_world.to_3x3()))
    normals = [tuple(vec) for vec in normals]
    return normals
    
## method returns dict of uv coordinates. 
def parse_uv_coords(bpy_mesh: Mesh, indxs: np.array):
    nVertex_in_face = 4
    uv_coords_dim = 2
    faces_count = len(bpy_mesh.polygons)

    # check texture layers names
    max_possible_layers = 2
    uv_layers = bpy_mesh.uv_layers
    if len(uv_layers) > max_possible_layers:
        log.fatal(f'Too much texture layers. {max_possible_layers} layers is maximum')
    
    is_two_side = False
    if len(uv_layers) == max_possible_layers:
        is_two_side = True

    # dict where values are texture map names from blender
    layers_uv_names = {}
    front_name = 'front' # key in the dict
    back_name = 'back' # 1) key in the dict 2) key word to search in uv_layers name
    if is_two_side:
        back_indx = [i for i, s in enumerate(uv_layers) if back_name in s.name.lower()]
        if len(back_indx) == 0:
            log.fatal(f'Cound not find texture layer for back side. Check the name of texture, it must contain f"{back_name}" suffix.')
        
        layers_uv_names[front_name] = uv_layers[max_possible_layers - back_indx[0] - 1].name        
        layers_uv_names[back_name] = uv_layers[back_indx[0]].name
    else:
        layers_uv_names[front_name] = uv_layers[0].name
    
    uvs = {}
    for uv_key, uv_name in layers_uv_names.items():
        uv_loop = uv_layers[uv_name]
        if len(uv_loop.uv) == 0:
            uvs[uv_key] = np.array([], dtype=np.float32)
            continue
        # maximum number of uv coords = faces_count * nVertex_in_face * uv_coords_dim, but it could be less in some cases.
        buf = np.empty(faces_count * nVertex_in_face * uv_coords_dim, dtype=np.float32)
        
        # parse uv coords values
        uv_loop.uv.foreach_get('vector', buf)
        buf = np.reshape(buf, (buf.size // uv_coords_dim, uv_coords_dim))

        # match vertex indices and uv-map values
        uv_coords = np.zeros(shape=(faces_count * nVertex_in_face, uv_coords_dim),  dtype=np.float32)
        for i in indxs:
            uv_coords[i] = buf[i]
            
        uv_coords = np.reshape(uv_coords, (faces_count, nVertex_in_face, uv_coords_dim))

        # uv_coords[faces_count, 4, 2] contains uv-map values for all 4 vertices of each face. 
        # but to export we need just 2 points - bottom left and top right.
        # that is why we need res_map[faces_count, 2, 2].
        res_map = np.zeros(shape=(faces_count, 2, uv_coords_dim), dtype=np.float32)
        for i in range(faces_count):
            x_min = np.min(uv_coords[i, :, 0], axis=0)
            x_max = np.max(uv_coords[i, :, 0], axis=0)
            y_min = np.min(uv_coords[i, :, 1], axis=0)
            y_max = np.max(uv_coords[i, :, 1], axis=0)

            res_map[i] = np.array([[x_min, y_min], [x_max, y_max]])
        
        uvs[uv_key] = res_map    
   
    return uvs

def parse_normals(faces_count: int, bpy_mesh: Mesh, object: Object):
    normals = np.empty(faces_count * DIM, dtype=np.float32)
    bpy_mesh.polygons.foreach_get('normal', normals) 
    normals = np.reshape(normals, (faces_count, DIM), order='C')

    normals = convert_coordinates(normals, object)

    return normals

## parse faces of object and return center of each face, normal vectors, size of light.
def run_parsing(bpy_mesh: Mesh, object: Object):
    faces_count = len(bpy_mesh.polygons)

    normals = parse_normals(faces_count, bpy_mesh, object)

    centers = np.empty(faces_count * DIM, dtype=np.float32)
    bpy_mesh.polygons.foreach_get('center', centers) 
    centers = np.reshape(centers, (faces_count, DIM), order='C')

    # to apply texture we need to extract verticies
    vert_count = len(bpy_mesh.vertices)
    vertices = np.empty(vert_count * DIM, dtype=np.float32)
    bpy_mesh.vertices.foreach_get('co', vertices) 
    vertices = np.reshape(vertices, (vert_count, DIM), order='C')

    # for each face get np.array with indxes of vertices in this face.
    indxs = np.empty(faces_count * POINTS_COUNT, dtype=np.int32)
    bpy_mesh.polygons.foreach_get('vertices', indxs)
    uvs = parse_uv_coords(bpy_mesh, indxs)

    # calculate diagonal of each polygon by finding light_sizes=maximum(|p0-p1|, |p0-p2|, |p0-p3|)
    indxs = np.reshape(indxs, (POINTS_COUNT, faces_count), order='F')
    sides_polygons = np.zeros(shape=(faces_count, 3))
    for i in range(0, POINTS_COUNT-1):
        sides_polygons[:, i] = np.linalg.norm(vertices[indxs[0]] - vertices[indxs[i+1]], axis=1)

    light_sizes = np.max(sides_polygons, axis=1)

    return centers, normals, light_sizes, uvs

def parse_faces(bpy_mesh: Mesh, object: Object):
    try: 
        return run_parsing(bpy_mesh, object)
    except:
        log.fatal(f'Could not parse {bpy_mesh.name} mesh')

class FakeLightChildPanel(bpy.types.Panel):
    bl_label = "Fake light type Properties"
    bl_idname = "OBJECT_PT_fake_light_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_edm_data"

    @classmethod
    def poll(cls, context):
        if not utils.has_object(context):
            return

        object: Object = context.object
        props = get_edm_props(object)

        result = props.SPECIAL_TYPE in (EDMPropsSpecialTypeStr.FAKE_LIGHT) and not(object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP)
        return result

    def draw(self, context):
        if not utils.has_object(context):
            return

        layout = self.layout
        object: Object = context.object
        props = get_edm_props(object)
        
        box = layout.row()
        row = box.row()
        row.prop(props, "SURFACE_MODE")

        if not props.SURFACE_MODE:
            row = box.row()
            row.prop(props, "TWO_SIDED")

        if not props.SURFACE_MODE:
            box = layout.box()

            row = box.row()
            row.prop(props, "UV_LB")

            row = box.row()
            row.prop(props, "UV_RT")

            if props.TWO_SIDED:
                row = box.row()
                row.prop(props, "UV_LB_BACK")

                row = box.row()
                row.prop(props, "UV_RT_BACK")

            row = layout.row()
            row.prop(props, "SIZE")
        
        row = layout.row()        
        row.prop(props, "ANIMATED_BRIGHTNESS")
