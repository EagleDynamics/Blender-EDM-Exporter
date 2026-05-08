from bpy.types import NodeTree, ShaderNodeGroup
from serializer import SOutput, SInput
from typing import List,Tuple
from utils import type_helper
from logger import log
from enums import SocketItemTypeEnum, SocketItemInOutTypeEnum, BpyNodeSocketType

from bpy.types import NodeSocketInterface
from bpy.types import NodeTree

def get_version(node_tree: NodeTree) -> int:
    if not node_tree:
        return 0
    
    version_socket: NodeSocketInterface = node_tree.inputs.get('Version')
    if not version_socket:
        return 0
    
    return version_socket.default_value

def create_inodesocket_output(soutput: SOutput, node_tree: NodeTree) -> NodeSocketInterface:
    socket: NodeSocketInterface = node_tree.outputs.new(soutput.bl_socket_idname, soutput.name)
    return socket

def extract_group_outputs(node_group: ShaderNodeGroup) -> List[SOutput]:
    outputs: List[SOutput] = []
    for output in node_group.node_tree.outputs:
        socket_type: str = node_group.outputs[output.name].bl_idname if hasattr(node_group.outputs[output.name], 'bl_idname') else output.bl_socket_idname
        outputs.append(
            SOutput (
                socket_type,
                output.name,
                output.description
            )
        )
    return outputs

def create_inodesocket_input(sinput: SInput, node_tree: NodeTree) -> NodeSocketInterface:
    socket: NodeSocketInterface = node_tree.inputs.new(sinput.bl_socket_idname, sinput.name)
    return socket

def create_custom_inodesocket_input(sinput: SInput, node_tree: NodeTree) -> NodeSocketInterface:
    if sinput.bl_socket_idname in (BpyNodeSocketType.TRANSPARENCY, BpyNodeSocketType.DECK_TRANSPARENCY, BpyNodeSocketType.SHADOWCASTER):
        return None
    else:
        socket: NodeSocketInterface = node_tree.inputs.new(sinput.bl_socket_idname, sinput.name)
    return socket


def extract_group_inputs(node_group: ShaderNodeGroup) -> List[SInput]:
    inputs: List[SInput] = []
    if not node_group:
        return inputs
    
    for input in node_group.node_tree.inputs:
        default_value = type_helper(input.default_value) if hasattr(input, 'default_value') else None
        min_max_tuple = (type_helper(input.min_value), type_helper(input.max_value)) if hasattr(input, 'min_value') else None
        instance_value = type_helper(node_group.inputs[input.name].default_value) if hasattr(input, 'default_value') else None
        socket_type: str = node_group.inputs[input.name].bl_idname if hasattr(node_group.inputs[input.name], 'bl_idname') else input.bl_socket_idname
        input_type: str = node_group.inputs[input.name].bl_rna.properties['default_value'].rna_type.identifier if hasattr(input, 'default_value') else None
        enum_values: List[str] = None
        if socket_type == 'NodeSocketUndefined':
            log.info("Socket " + input.name + " at " + node_group.node_tree.name + " has undefined or unregistered type.")
        if input_type and input_type == 'EnumProperty':
            enum_values: List[Tuple[str, str, str, str]] = []
            for item in node_group.inputs[input.name].bl_rna.properties['default_value'].enum_items:
                enum_values.append((item.identifier, item.name, item.description, item.value))
        inputs.append(
            SInput(
                socket_type,
                input.name,
                input.description,
                default_value,
                min_max_tuple,
                instance_value,
                enum_values
            )
        )
    return inputs
