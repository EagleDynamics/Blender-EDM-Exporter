import re
from pathlib import Path
from typing import Union, List, Dict

import bpy
from bpy.types import (
    Material,
    Node,
    NodeSocket,
    ShaderNode,
    ShaderNodeGroup,
    ShaderNodeTexImage,
    ShaderNodeUVMap,
    ShaderNodeMapping,
    NodeTree
)

import serializer
from utils import make_socket_map, make_acro_map, check_ex

from enums import (
    BpyNodeSocketType,
    NodeSocketInDefaultEnum,
    ShaderNodeTexImageOutParams,
    ShaderNodeMappingInParams
)


def socket_have_in_links(socket: NodeSocket) -> bool:
    return socket and socket.links is not None and not len(socket.links) == 0

def get_node_from_socket(socket: NodeSocket, tt: type) -> Union[Node, None]:
    sil = socket_have_in_links(socket)
    return socket.links[0].from_node if sil and type(socket.links[0].from_node) is tt else None

def node_have_in_links(node: ShaderNode) -> bool:
    return node and node.inputs is not None and socket_have_in_links(node.inputs[0])

def get_connected_node(node: ShaderNode, tt: type) -> Union[ShaderNode, None]:
    return get_node_from_socket(node.inputs[0], tt) if node_have_in_links(node) else None

def get_node_re(material: Material, node_name_regex) -> Union[ShaderNode, None]:
    if not node_name_regex or not material:
        return None

    use_nodes: bool = material.use_nodes and bool(material.node_tree)
    if not use_nodes:
        return None
    
    for bpy_node in material.node_tree.nodes:
        if re.match(node_name_regex, bpy_node.name):
            return bpy_node

    return None

def get_list_edm_node_group_re(custom_group_regex) -> List[NodeTree]:
    node_group_list: List[NodeTree] = []
    for node_tree in bpy.data.node_groups:
        if re.match(custom_group_regex, node_tree.name):
            node_group_list.append(node_tree)

    return node_group_list

g_missing_texture_name: str = '__EMPTY__'

class AttachedTextureStruct:
    @staticmethod
    def build_from_socket(node_socket: NodeSocket):
        node: ShaderNodeTexImage = get_node_from_socket(node_socket, ShaderNodeTexImage)
        if not node:
            return None
        return AttachedTextureStruct(node)
    
    def __init__(self, node: ShaderNodeTexImage) -> None:
        self.texture_node: ShaderNodeTexImage = node
        self.texture_socket: NodeSocket = self.texture_node.outputs[ShaderNodeTexImageOutParams.COLOR]
        self.attached: bool = False
        if node.image:
            self.attached = True
            self.texture_name: str = Path(Path(node.image.name).stem).stem
        else:
            self.texture_name: str = g_missing_texture_name
        self.uv_move_node: ShaderNodeMapping = get_connected_node(node, ShaderNodeMapping)
        self.uv_move_loc_anim_path: str = self.uv_move_node.inputs[ShaderNodeMappingInParams.LOCATION].path_from_id('default_value') if self.uv_move_node else None
        self.uv_move_rot_anim_path: str = self.uv_move_node.inputs[ShaderNodeMappingInParams.ROTATION].path_from_id('default_value') if self.uv_move_node else None
        self.uv_move_sc_anim_path: str = self.uv_move_node.inputs[ShaderNodeMappingInParams.SCALE].path_from_id('default_value') if self.uv_move_node else None
        self.uv_node: ShaderNodeUVMap = get_connected_node(node, ShaderNodeUVMap)
        if not self.uv_node:
            self.uv_node = get_connected_node(self.uv_move_node, ShaderNodeUVMap)
        self.uv_name: str = self.uv_node.uv_map if self.uv_node else None

    def get_uv_map(self, default_uv_map) -> str:
        return self.uv_node.uv_map if self.uv_node and self.uv_node.uv_map else default_uv_map
    
def remove_item(collection, item):
     item_in = collection[item.name]
     collection.remove(item_in)

def remove_item_by_name(collection, name: str):
     item_in = collection.get(name)
     if item_in:
        collection.remove(item_in)

def search_out_socket(node_group: ShaderNodeGroup, name: str, type: str) -> Union[NodeSocket, None]:
    for out_socket in node_group.outputs:
        if out_socket.name == name and out_socket.bl_idname == type:
            return out_socket
    return None

def search_in_socket(node_group: ShaderNodeGroup, name: str, type: str) -> Union[NodeSocket, None]:
    for in_socket in node_group.inputs:
        if in_socket.name == name and in_socket.bl_idname == type:
            return in_socket

    # Useful for debugging.
    # print(name, type)
    # print([(x.name, x.type) for x in node_group.inputs])

    return None

class TextureDesk:
    def __init__(self, node_group: ShaderNodeGroup, socket_name: str, socket_type: str) -> None:
        self.socket_name: str = socket_name
        self.socket_type: str = socket_type
        self.apply(node_group)
        self.update()

    def apply(self, node_group: ShaderNodeGroup):
        self.socket: NodeSocket = search_in_socket(node_group, self.socket_name, self.socket_type)

    def update(self):
        self.texture = AttachedTextureStruct.build_from_socket(self.socket)
        if self.socket_type == BpyNodeSocketType.COLOR:
            self.default_color = serializer.type_helper(self.socket.default_value) if self.socket else (0.0, 0.0, 0.0, 1.0)
        elif self.socket_type == BpyNodeSocketType.FLOAT:
            self.default_color = (0.0, 0.0, 0.0, serializer.type_helper(self.socket.default_value)) if self.socket else (0.0, 0.0, 0.0, 1.0)
        else:
            self.default_color = serializer.type_helper(self.socket.default_value) if self.socket else (0.0, 0.0, 0.0, 1.0)
        self.color_anim_path: str = self.socket.path_from_id('default_value') if self.socket else None

class ValueDeskBase:
    def __init__(self, node_group: ShaderNodeGroup, socket_name: NodeSocketInDefaultEnum, socket_type: BpyNodeSocketType) -> None:
        self.node_group: ShaderNodeGroup = node_group
        self.socket_map: Dict[str, Dict[str, str]] = make_socket_map(node_group)
        self.socket_acro_map: Dict[str, str] = make_acro_map(node_group)
        self.tree_name: str = node_group.node_tree.name
        self.socket_name: str = socket_name.value
        self.socket_type: str = socket_type.value

    def setCommonSocketsValues(self, def_value):
        self.apply(self.node_group)
        self.def_value = serializer.type_helper(self.socket.default_value) if self.socket and self.socket.default_value else def_value
        self.anim_path: str = self.socket.path_from_id('default_value') if self.socket else None

    def apply(self, node_group: ShaderNodeGroup):
        self.socket: NodeSocket = search_in_socket(node_group, self.socket_name, self.socket_type)


class ValueDesk(ValueDeskBase):
    def __init__(self, node_group: ShaderNodeGroup, socket_name: NodeSocketInDefaultEnum, socket_type: BpyNodeSocketType, def_value):
        super().__init__(node_group, socket_name, socket_type)
        
        if check_ex(self.socket_map, self.tree_name, self.socket_name):
            enum_name: str = self.socket_map[self.tree_name][socket_name]
            self.def_value = getattr(node_group, enum_name)
            self.anim_path: str = ''
        else:
            super().setCommonSocketsValues(def_value)
        self.update()

    def update(self):
        if hasattr(self.node_group, self.socket_type):
            self.value = getattr(self.node_group, self.socket_type)
        else:
            self.value = self.socket.default_value if self.socket and self.socket.default_value else self.def_value

class ValueDeskDropDown(ValueDeskBase):
    def __init__(self, node_group: ShaderNodeGroup, socket_name: NodeSocketInDefaultEnum, socket_type: BpyNodeSocketType, def_value) -> None:
        super().__init__(node_group, socket_name, socket_type)
        if check_ex(self.socket_map, self.tree_name, self.socket_name):
                prop_name: str = self.socket_acro_map.get(socket_name.value)
                self.def_value = getattr(node_group, prop_name)
                self.anim_path: str = ''
        else:
            super().setCommonSocketsValues(def_value)
        self.update()

    def update(self):
        if hasattr(self.node_group, self.socket_type):
            prop_name: str = self.socket_acro_map.get(self.socket_name)
            self.value = getattr(self.node_group, prop_name)
        else:
            self.value = self.socket.default_value if self.socket and self.socket.default_value else self.def_value

