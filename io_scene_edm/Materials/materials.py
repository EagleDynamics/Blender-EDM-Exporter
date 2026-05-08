import os
import re
import pickle
from types import MappingProxyType
from typing import Dict, List, Set, Union, Pattern

import bpy
from bpy.types import (
    Node,
    Material,
    ShaderNodeGroup,
    ShaderNodeOutputMaterial,
)

from logger import log
from utils import md5, EDMPath
from enums import BpyShaderNode
from serializer_tools import MatDesc
from materials.material_interface import IMaterial
from materials.material_default import DefaultMaterial
from materials.material_deck import DeckMaterial
from materials.material_fake_omni import OmniFakeLightsMaterial
from materials.material_fake_spot import SpotFakeLightsMaterial
from materials.material_glass import GlassMaterial
from materials.material_mirror import MirrorMaterial

## unmutable dictionary of all possible materials.
MATERIALS: Dict[str, IMaterial] = MappingProxyType(
    {
        DefaultMaterial.name: DefaultMaterial,
        DeckMaterial.name: DeckMaterial,
        OmniFakeLightsMaterial.name: OmniFakeLightsMaterial,
        SpotFakeLightsMaterial.name: SpotFakeLightsMaterial,
        GlassMaterial.name: GlassMaterial,
        MirrorMaterial.name: MirrorMaterial
    }
)

## only edm group names
_node_groups_names_edm: Set[str] = set()
for mat in MATERIALS.values():
    _node_groups_names_edm.add(mat.node_group_name)

## group names 
_node_groups_names: Set[str] = _node_groups_names_edm | {'EdmMatrialShaderNodeType', BpyShaderNode.NODE_GROUP}

## is node edm
def isNodeEdm(bl_idname: str) -> bool:  
    return bl_idname in _node_groups_names

def isNodeEdmCustom(bl_idname: str) -> bool:  
    return bl_idname in _node_groups_names_edm

## check if material is edm material. if true - return bpy_node
def getEdmMaterialNode(mat: Material, pattern_regex: Pattern[str] | None = None) -> Node | None:
    for bpy_node in mat.node_tree.nodes:
        if isNodeEdm(bpy_node.bl_idname):     
   
            if not bpy_node.node_tree and hasattr(bpy_node, 'bl_label'):
                bpy_node.node_tree = bpy.data.node_groups.get(bpy_node.bl_label)
            
            if not bpy_node.node_tree:
                continue

            if pattern_regex:
                return bpy_node if re.match(pattern_regex, bpy_node.node_tree.name) else None
            return bpy_node  
        
    return None

def debug_node_properties(bpy_node):
    log.info(f"=== Debug node: {bpy_node.name} (type: {bpy_node.bl_idname}) ===")
    for attr_name in dir(bpy_node):
        if attr_name.startswith('_'): 
            continue
        try:
            attr_value = getattr(bpy_node, attr_name, None)
            if isinstance(attr_value, (str, int, float, bool)) or attr_value is None:
                log.info(f"  {attr_name}: {attr_value}")
        except:
            pass

## node groups methods:
def get_material_output_nodes(material: Material) -> List[ShaderNodeOutputMaterial]:
    use_nodes: bool = material.use_nodes and bool(material.node_tree)
    if not use_nodes:
        return []
    out_nodes_list: List[ShaderNodeOutputMaterial] = []
    for bpy_node in material.node_tree.nodes:
        if bpy_node.bl_idname == BpyShaderNode.OUTPUT_MATERIAL:
            out_nodes_list.append(bpy_node)
    return out_nodes_list

def get_material_output(material: Material) -> Union[ShaderNodeOutputMaterial, None]:
    if not material:
        return None
    out_nodes_list: List[ShaderNodeOutputMaterial] = get_material_output_nodes(material)
    if len(out_nodes_list) == 0:
        return None
    for bpy_node in out_nodes_list:
        if bpy_node.is_active_output:
            return bpy_node
    return None

def get_edm_node_group_from_node(bpy_node: Node, custom_group_name: str) -> Union[ShaderNodeGroup, None]:
    if not bpy_node:
        return None
    
    for socket in bpy_node.inputs:
        for link in socket.links:
            linked_node: Node = link.from_node
            if ( isNodeEdm(linked_node.bl_idname) and 
                linked_node.node_tree and 
                linked_node.node_tree.name == custom_group_name ):
                return linked_node
            for linked_node_socket in linked_node.inputs:
                for linked_node_link in linked_node_socket.links:
                    return get_edm_node_group_from_node(linked_node_link.from_node, custom_group_name)
    
    return None

def get_edm_node_group_from_node_re(bpy_node: Node, custom_group_regex) -> Union[ShaderNodeGroup, None]:
    if not bpy_node or not custom_group_regex:
        return None
    for socket in bpy_node.inputs:
        for link in socket.links:
            linked_node: Node = link.from_node
            if ( isNodeEdm(linked_node.bl_idname) and 
                linked_node.node_tree and 
                re.match(custom_group_regex, linked_node.node_tree.name) ):
                return linked_node
            
            for linked_node_socket in linked_node.inputs:
                for linked_node_link in linked_node_socket.links:
                    return get_edm_node_group_from_node_re(linked_node_link.from_node, custom_group_regex)
    
    return None

def get_edm_node_group(material: Material, custom_group_name: str) -> Union[ShaderNodeGroup, None]:
    if not custom_group_name or not material:
        return None

    use_nodes: bool = material.use_nodes and bool(material.node_tree)
    if not use_nodes:
        return None
    
    material_output_node: ShaderNodeOutputMaterial = get_material_output(material)
    group_node_by_link: Union[ShaderNodeGroup, None] = get_edm_node_group_from_node(material_output_node, custom_group_name)
    if group_node_by_link:
        return group_node_by_link
    
    bpy_node = getEdmMaterialNode(material, re.compile(custom_group_name))
    return bpy_node

def get_edm_node_group_re(material: Material, custom_group_regex) -> Union[ShaderNodeGroup, None]:
    if not custom_group_regex or not material:
        return None

    use_nodes: bool = material.use_nodes and bool(material.node_tree)
    if not use_nodes:
        return None
    
    material_output_node: ShaderNodeOutputMaterial = get_material_output(material)
    group_node_by_link: Union[ShaderNodeGroup, None] = get_edm_node_group_from_node_re(material_output_node, custom_group_regex)
    if group_node_by_link:
        return group_node_by_link

    bpy_node = getEdmMaterialNode(material, custom_group_regex)
    return bpy_node

def filter_materials(edm_group_name: str) -> List[bpy.types.Material]:
    out: List[bpy.types.Material] = []
    for mat in bpy.data.materials:
        use_nodes = mat.use_nodes and mat.node_tree
        if not use_nodes:
            continue
        
        bpy_node = getEdmMaterialNode(mat, re.compile(edm_group_name))
        if bpy_node:
            out.append(mat)

    return out

## if edm_group_copied_regex is not None, 
## we assume that names like EDM_Default_Material.001, EDM_Default_Material.002 are not broken.
## blender adds .001, .002, etc to node group name when you copy object by ctrl+c ctrl+v.
def filter_materials_re(edm_group_regex, edm_group_copied_regex=None) -> List[bpy.types.Material]:
    out: List[bpy.types.Material] = []
    if not edm_group_regex:
        return out
    if not hasattr(bpy.data, "materials"):
        return out
    for mat in bpy.data.materials:
        use_nodes = mat.use_nodes and mat.node_tree
        if not use_nodes:
            continue
        
        bpy_node = getEdmMaterialNode(mat)
        if bpy_node is None:
            continue

        ## for not to add copied material names to list.
        if edm_group_copied_regex and re.match(edm_group_copied_regex, bpy_node.node_tree.name):
            continue
        if re.match(edm_group_regex, bpy_node.node_tree.name):
            out.append(mat)
                
    return out

def check_if_referenced_file(blend_file_name):
    bf = os.path.splitext(os.path.basename(blend_file_name))[0].lower()

    for m in MATERIALS.keys():
        if m.lower() == bf:
            return True
    return False


def check_md5(material_name: str, material_desc: MatDesc):
    node_tree_name = re.compile(f'[A-Za-z0-9_.-]*{material_name}[A-Za-z0-9_.-]*')
    mat_list: List[bpy.types.Material] = filter_materials_re(node_tree_name)
    if mat_list:
        blend_file_name: str = 'data/' + str(material_name) + '.blend'
        blend_file_path: str = os.path.join(EDMPath.full_plugin_path, blend_file_name)
        blend_file_md5: str = md5(blend_file_path)
        if hasattr(material_desc, 'blend_file_md5') and material_desc.blend_file_md5 != blend_file_md5:
           log.fatal(f"Hash of material file {blend_file_path} is invalid.")


def build_material_descriptions() -> Dict[str, MatDesc]:    
    material_descs: Dict[str, MatDesc] = {}

    for name, mat in MATERIALS.items():
        f = None
        try:
            pickle_file_name: str = os.path.join(EDMPath.full_plugin_path, mat.description_file_name)
            f = open(pickle_file_name, 'rb')
            material_descs[name] = pickle.load(f)            
        except OSError as exc:
            log.error(f"Error: Can't open {name}.pikle. Error message: {exc}.")
            continue
        except (pickle.UnpicklingError, AttributeError) as exc:
            log.error(f"Error: Broken {name}.pikle, please update it by exporting {name}.blend material.\nError message: {exc}.")
            continue
        finally:
            if f:
                f.close()

    return material_descs