import os
import sys
from dataclasses import dataclass, field
from typing import List, Union, Dict, Callable

import pickle
if 'bpy' in sys.modules:
    import bpy
    from bpy.types import (
        NodeLink, 
        ShaderNode, 
        Node, 
        NodeTree, 
        NodeSocket, 
        NodeInputs, 
        NodeOutputs, 
        ShaderNodeGroup
    )
    from node_tree_tools import ( 
        create_inodesocket_output, 
        create_inodesocket_input, 
        extract_group_inputs, 
        extract_group_outputs
    )
    from utils import md5

else:
    from dummy_bpy_classes import (
        NodeLink, 
        ShaderNode, 
        Node, NodeTree, 
        NodeSocket, 
        NodeInputs, 
        NodeOutputs,
        ShaderNodeGroup
    )

from enums import BpyShaderNode, NodeSocketCommonEnum
from socket_types import SOutput, SInput
from serializer import (
    SNode, 
    SLink, 
    SNodeMixRGB, 
    SNodeMix, 
    SNodeSeparateColor, 
    SNodeSeparateRGB, 
    SNodeColorRamp, 
    SNodeInvert, 
    SNodeCombineRGB, 
    SNodeCombineColor,
    SNodeNormalMap, 
    SNodeBsdfPrincipled, 
    SNodeGroupInput, 
    SNodeGroupOutput, 
    SNodeReroute, 
    SShaderNode, 
    SShaderNodeMath
)

def soutput_add_to_tree(soutput: SOutput, node_tree: NodeTree) -> None:
    socket = create_inodesocket_output(soutput, node_tree)
    socket.description = soutput.description

def sinput_add_to_tree(sinput: SInput, node_tree: NodeTree, fn_create_socket) -> None:
    socket = fn_create_socket(sinput, node_tree)
    if not socket:
        return
    if hasattr(sinput, "instance_value") and sinput.instance_value:
        socket.default_value = sinput.instance_value
    elif sinput.default_value:
        socket.default_value = sinput.default_value
    socket.description = sinput.description
    if sinput.value_range:
        socket.min_value, socket.max_value = sinput.value_range

def sinput_add_to_tree_norm(sinput: SInput, node_tree: NodeTree) -> None:
    sinput_add_to_tree(sinput, node_tree, create_inodesocket_input)

def sinput_add_to_tree_custom(sinput: SInput, node_tree: NodeTree) -> None:
    sinput_add_to_tree(sinput, node_tree, create_inodesocket_input)

def get_socket_name_type(socket_collection: Union[NodeOutputs, NodeInputs], name: str, bpy_type_name: str) -> Union[None, NodeSocket]:
    result: NodeSocket = None
    if not name or not bpy_type_name:
        return result
    for socket in socket_collection:
        if(socket.name == name and socket.bl_idname == bpy_type_name):
            result = socket
            break
    if not result:
        result = socket_collection[name]
    return result

@dataclass
class MatDesc:
    name: str
    postfix: str
    nodes: List[SNode] = field(default_factory=list)
    links: List[SLink] = field(default_factory=list)
    inputs: List[SInput] = field(default_factory=list)
    outputs: List[SOutput] = field(default_factory=list)
    version: int = -1
    blend_file_md5: str = ''

    def strap_tree(self, node_tree_type: BpyShaderNode, postfix: str, sinput_fn: Callable[[SInput, NodeTree], None]) -> NodeTree:
        name_with_postfix: str = self.name + postfix if postfix else self.name
        pbr_tree: NodeTree = bpy.data.node_groups.get(self.name)
        if pbr_tree:
            return pbr_tree
        node_tree: NodeTree = bpy.data.node_groups.new(name_with_postfix, node_tree_type)
        nodes: Dict[str, Node] = self.create_nodes(node_tree)
        for input in self.inputs:
            sinput_fn(input, node_tree)
        for output in self.outputs:
            soutput_add_to_tree(output, node_tree)
        links = self.create_links(node_tree, nodes)
        return node_tree

    def create_with_postfix(self, postfix: str) -> NodeTree:
        return self.strap_tree(BpyShaderNode.NODE_TREE, postfix, sinput_add_to_tree_custom)

    
    def create_custom_with_postfix(self, postfix: str) -> NodeTree:
        return self.strap_tree(BpyShaderNode.NODE_TREE, postfix, sinput_add_to_tree_custom)

    def create(self) -> NodeTree:
        self.postfix = ''
        return self.create_with_postfix(self.postfix)
    
    def create_custom(self) -> NodeTree:
        self.postfix = ''
        return self.create_custom_with_postfix(self.postfix)
    
    def create_nodes(self, node_tree: NodeTree) -> Dict[str, Node]:
        nodes: Dict[str, Node] = {}
        for node in self.nodes:
            bpy_node: Node = node.create(node_tree)
            nodes[node.name] = bpy_node
        return nodes
    
    def create_links(self, node_tree: NodeTree, nodes: Dict[str, Node]) -> List[NodeLink]:
        links: List[NodeLink] = []
        for link in self.links:
            bpy_link: NodeLink = link.create(node_tree, nodes)
            links.append(bpy_link)
        return links

def create_snode(node: ShaderNode) -> Union[SNode, None]:
    if node.bl_idname == BpyShaderNode.MIX_RGB:
        return SNodeMixRGB(node)
    if node.bl_idname == BpyShaderNode.MIX:
        return SNodeMix(node)
    if node.bl_idname == BpyShaderNode.SEPARATE_COLOR:
        return SNodeSeparateColor(node)
    if node.bl_idname == BpyShaderNode.SEPARATE_RGB:
        return SNodeSeparateRGB(node)
    if node.bl_idname == BpyShaderNode.COLOR_RAMP:
        return SNodeColorRamp(node)
    if node.bl_idname == BpyShaderNode.INVERT:
        return SNodeInvert(node)
    if node.bl_idname == BpyShaderNode.COMBINE_RGB:
        return SNodeCombineRGB(node)
    if node.bl_idname == BpyShaderNode.COMBINE_COLOR:
        return SNodeCombineColor(node)
    if node.bl_idname == BpyShaderNode.NORMAL_MAP:
        return SNodeNormalMap(node)
    if node.bl_idname == BpyShaderNode.BSDF_PRINCIPLED:
        return SNodeBsdfPrincipled(node)
    if node.bl_idname == BpyShaderNode.NODE_GROUP_INPUT:
        return SNodeGroupInput(node)
    if node.bl_idname == BpyShaderNode.NODE_GROUP_OUTPUT:
        return SNodeGroupOutput(node)
    if node.bl_idname == BpyShaderNode.NODE_REROUTE:
        return SNodeReroute(node)
    if node.bl_idname == BpyShaderNode.SHADER_NODE:
        return SShaderNode(node)
    if node.bl_idname == BpyShaderNode.SHADER_NODE_MATH:
        return SShaderNodeMath(node)

    return None
    
def collect_links(sockets: Union[NodeInputs, NodeOutputs], links: List[SLink]) -> None:
    for socket in (s for s in sockets if s.name):
        for link in socket.links:
            shader_link = SLink(link)
            if shader_link not in links:
                links.append(shader_link)

def collect_nodetree_links(node_tree: NodeTree, links: List[SLink]) -> None:
    for link in node_tree.links:
        shader_link = SLink(link)
        if shader_link not in links:
            links.append(shader_link)

def serialize_group(node_group: ShaderNodeGroup, blend_file_path: str) -> bytes:
    mat_desc = MatDesc(node_group.node_tree.name, [], [], [], -1)
    mat_desc.inputs: List[SInput] = extract_group_inputs(node_group)
    mat_desc.outputs: List[SOutput] = extract_group_outputs(node_group)
    for node in node_group.node_tree.nodes:
        snode: SNode = create_snode(node)
        mat_desc.nodes.append(snode)
        collect_nodetree_links(node_group.node_tree, mat_desc.links)

    for input in mat_desc.inputs:
        if input.name == NodeSocketCommonEnum.VERSION:
            mat_desc.version = input.default_value
            break
    mat_desc.blend_file_md5 = md5(blend_file_path)
    dump = pickle.dumps(mat_desc)
    return dump