import re
import bpy
import os.path
import hashlib
from mathutils import Color, Vector, Euler
from bpy.utils import register_class, unregister_class
from typing import List
from dataclasses import dataclass
from logger import log
from bpy.types import Object, bpy_prop_array, ShaderNodeGroup, ShaderNodeCustomGroup
from typing import List, Union, Tuple, Union, Sequence, Callable, Dict
from bpy.types import Node

def make_socket_map(node_group: ShaderNodeGroup) -> Dict[str, Dict[str, str]]:
    if not hasattr(node_group, 'enum_names'):
        return {}
    names_map: Dict[str, Dict[str, str]] = {}
    for item in node_group.bl_rna.properties['enum_names'].enum_items:
        if names_map.get(item.name):
            mat_item: Dict[str, str] = names_map[item.name]
            mat_item.update({item.description : item.identifier})
        else:
            mat_item: Dict[str, str] = {item.description : item.identifier}
        names_map.update({item.name : mat_item})
    return names_map

def make_acro_map(node_group: ShaderNodeGroup) -> Dict[str, str]:
    acro_map: Dict[str, str] = {}
    for key in node_group.bl_rna.properties.keys():
        item = node_group.bl_rna.properties[key]
        if hasattr(item, 'rna_type') and item.rna_type.identifier == 'EnumProperty':
            acro_map.update({ item.name : item.identifier })
    return acro_map

def check_ex(socket_map: Dict[str, Dict[str, str]], tree_name: str, socket_name: str) -> bool:
    if not socket_map or not socket_name:
        return False
    if not socket_map.get(tree_name):
        return False
    if not socket_map[tree_name].get(socket_name):
        return False
    return True

def type_helper(v):
    if type(v) is Vector:
        return v.to_tuple()
    
    if type(v) is Color:
        return v[:]
    
    if type(v) is Euler:
        return v[:]
    
    if type(v) is bpy_prop_array:
        return v[:]
    
    return v

def print_node(node: Node):
    if not node:
        return
    log.info(node.name)
    log.info(f'  Inputs:')
    for i in node.inputs:
        if hasattr(i, 'default_value'):
            log.info(f'    {i.name} ({type_helper(i.default_value)})')
        else:
            log.info(f'    {i.name}')
    log.info(f'  Outputs:')
    for i in node.outputs:
        log.info(f'    {i.name}')

def print_nodes(nodes: List[Node]):
    for i in nodes:
        print_node(i)

def md5(fname) -> str:
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

lod_re_c = re.compile(r'[A-Za-z0-9_-]*LOD_(\d+)_(\d+)')
arg_re_c = re.compile(r'^(\d+)(_.+)?')

last_braces_re_c = re.compile(r'.*\[(\d+)\]$')

class EDMPath:
    scripts_path: str = bpy.utils.user_resource(resource_type='SCRIPTS', path="addons")
    plugin_name: str = 'io_scene_edm'
    full_plugin_path: str = os.path.join(scripts_path, plugin_name)

def get_is_dev_env() -> bool:
    return False

def register_bpy_class(cls):
    
    if issubclass(cls, ShaderNodeCustomGroup) and cls.is_registered_node_type():
        log.debug(f'SKIP Registered {cls.bl_idname}.')
        return  
    
    register_class(cls)
    log.debug(f'Registered {cls.bl_idname}.')

def unregister_bpy_class(cls):
    # Blender crashes if we unregister ShaderNodeCustomGroup. #TODO ?
    
    if issubclass(cls, ShaderNodeCustomGroup):
        log.debug(f'SKIP Unregistered {cls.bl_idname}.')
        return
    
    unregister_class(cls)
    log.debug(f'Unregistered {cls.bl_idname}.')

def float_close(value1: float, value2: float) -> bool:
    return abs(value2 - value1)  < 1.0e-5

def cmp(value1: float, value2: float) -> bool:
    return float_close(value1, value2)

def cmp_vec2(value1: Tuple[float, float], value2: Tuple[float, float]) -> bool:
    return float_close(value1[0], value2[0]) and float_close(value1[1], value2[1])

def cmp_vec3(value1: Tuple[float, float, float], value2: Tuple[float, float, float]) -> bool:
    return float_close(value1[0], value2[0]) and float_close(value1[1], value2[1]) and float_close(value1[2], value2[2])

def cmp_vec4(value1: Tuple[float, float, float, float], value2: Tuple[float, float, float, float]) -> bool:
    return float_close(value1[0], value2[0]) and float_close(value1[1], value2[1]) and float_close(value1[2], value2[2]) and float_close(value1[3], value2[3])

@dataclass
class Lod:
    id: int
    dist: float

def extract_lod(name):
    m = re.match(lod_re_c, name)
    if not m:
        return None
    
    return Lod(int(m.group(1)), float(m.group(2)))

# Returns if obj has parent as parent despite the distance.
def is_parent(obj: Object, parent: Object) -> bool:
    while obj.parent:
        if obj.parent.name == parent.name:
            return True
        obj = obj.parent
    return False

# Returns if obj has parent as parent despite the distance.
def get_full_name(obj: Object) -> str:
    name = ''
    while obj.parent:
        name = os.path.join(obj.parent, name)
    return os.path.join(name, obj.name)

# Returns -1 on failure.
def extract_arg_number(str_name: str) -> int:
    m = re.match(arg_re_c, str_name)
    if not m:
        return -1
    
    return int(m.group(1))

def get_animation_argument(name, allowed_args=None):
    arg = extract_arg_number(name)
    if arg < 0 or (allowed_args and arg not in allowed_args):
        return -1

    return arg

def is_list_unique_sub(list: List, sub_obj, attr_name) -> bool:
    for i in list:
        ct = 0
        for j in list:
            if getattr(getattr(i, sub_obj), attr_name) == getattr(getattr(j, sub_obj), attr_name):
                ct += 1
        if ct > 1:
            return False
        
    return True

def get_not_unique_attr(list: List, sub_obj, attr_name) -> bool:
    for i in list:
        ct = 0
        for j in list:
            if getattr(getattr(i, sub_obj), attr_name) == getattr(getattr(j, sub_obj), attr_name):
                ct += 1
        if ct > 1:
            return getattr(getattr(i, sub_obj), attr_name)
        
    return None

def print_parents(obj):
    res = []
    p = obj
    while p:
        res.append(p.name)
        p = p.parent

    log.debug(' --> '.join(res))

def print_matrix(name, mat):
    log.debug(f'{name}:\n{str(mat)}')

dmg_vertex_group_re_c = re.compile(r'^DMG_(\d+)$')
def get_dmg_vert_group_arg(vertex_group_name):
    m = re.match(dmg_vertex_group_re_c, vertex_group_name)
    if not m:
        return -1
    
    return int(m.group(1))

def has_object(context):
    if not context.object:
        return False

    object: Object = context.object
        
    is_selected: bool = object.select_get()
    if not is_selected:
        return False

    if not hasattr(object, 'EDMProps'):
        return False

    return True