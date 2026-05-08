from bpy.types import (
    NodeTree, 
    ShaderNodeGroup
)

from typing import List, Union, Tuple
from utils import type_helper
from socket_types import SOutput, SInput
from enums import (
    SocketItemTypeEnum, 
    SocketItemInOutTypeEnum,
    BpyNodeSocketType,
    DROP_DOWN_LISTS
)

def get_version(node_tree: NodeTree) -> int:
    if not node_tree:
        return 0
    version_socket = node_tree.interface.items_tree.get('Version')
    if not version_socket:
        return 0
    
    return version_socket.default_value

def create_inodesocket_output(self, node_tree: NodeTree):
    if self.bl_socket_idname == BpyNodeSocketType.INTEGER:
        socket = node_tree.interface.new_socket(self.name, socket_type=BpyNodeSocketType.FLOAT, in_out=SocketItemInOutTypeEnum.OUTPUT)
    else:
        socket = node_tree.interface.new_socket(self.name, socket_type=self.bl_socket_idname, in_out=SocketItemInOutTypeEnum.OUTPUT)
    return socket

def create_inodesocket_input(sinput: SInput, node_tree: NodeTree):
    if sinput.bl_socket_idname in DROP_DOWN_LISTS:
        return None
    if sinput.bl_socket_idname in (BpyNodeSocketType.INTEGER):
        socket = node_tree.interface.new_socket(sinput.name, socket_type=BpyNodeSocketType.FLOAT, in_out=SocketItemInOutTypeEnum.INPUT)
    else:
        socket = node_tree.interface.new_socket(sinput.name, socket_type=sinput.bl_socket_idname, in_out=SocketItemInOutTypeEnum.INPUT)
    return socket

def extract_group_outputs(node_group: ShaderNodeGroup) -> List[SOutput]:
    outputs: List[SOutput] = []
    for output in [item for item in node_group.node_tree.interface.items_tree if item.item_type == SocketItemTypeEnum.SOCKET and item.in_out == SocketItemInOutTypeEnum.OUTPUT]:
        socket_type: str = node_group.outputs[output.name].bl_idname if hasattr(node_group.outputs[output.name], 'bl_idname') else output.bl_socket_idname
        outputs.append(
            SOutput (
                socket_type,
                output.name,
                output.description
            )
        )
    return outputs

## create socket input
def create_sinput( bl_socket_idname: str, name: str, description: str, 
                        default_value: any, value_range: tuple, instance_value: any, enum_values: list) -> SInput:
    
    sinput = SInput( bl_socket_idname, name, description, default_value, value_range, instance_value, enum_values )
    return sinput

def extract_group_inputs(node_group: ShaderNodeGroup) -> List[SInput]:
    inputs: List[SInput] = []
    if not node_group:
        return inputs
        
    for input in [item for item in node_group.node_tree.interface.items_tree if item.item_type == SocketItemTypeEnum.SOCKET and item.in_out == SocketItemInOutTypeEnum.INPUT]:
        default_value = type_helper(input.default_value) if hasattr(input, 'default_value') else None
        min_max_tuple = (type_helper(input.min_value), type_helper(input.max_value)) if hasattr(input, 'min_value') else None
        instance_value = type_helper(node_group.inputs[input.name].default_value) if hasattr(node_group.inputs.get(input.name), 'default_value') else None
        socket_type: str = node_group.inputs[input.name].bl_idname if hasattr(node_group.inputs.get(input.name), 'bl_idname') else input.bl_socket_idname
        input_type: str = node_group.inputs[input.name].bl_rna.properties['default_value'].rna_type.identifier if hasattr(input, 'default_value') else None
        enum_values: List[str] = None
        if input_type and input_type == 'EnumProperty':
            enum_values: List[Tuple[str, str, str, str]] = []
            for item in node_group.inputs[input.name].bl_rna.properties['default_value'].enum_items:
                enum_values.append((item.identifier, item.name, item.description, item.value))
        
        sinput = create_sinput(socket_type, input.name, input.description, default_value, min_max_tuple, instance_value, enum_values)
        inputs.append(sinput)

    ## It is needed when you want to save drop-down lists for newly created material.
    ## Code below shows how to save GLASS TYPE in pickle.
    if node_group.node_tree.name == 'EDM_Glass_Material':

        sinput_shadow_caster: SInput = create_sinput(
            'EdmGlassSocketShadowCasterType',
            'Shadow Caster',
            '',
            'SHADOW_CASTER_YES',
            None,
            'SHADOW_CASTER_YES',
            [
                ('SHADOW_CASTER_YES',   "YES",          "Cast Shadows",         0),
                ('SHADOW_CASTER_NO',    "NO",           "Don't cast shadows",   1),
                ('SHADOW_CASTER_ONLY',  "ONLY_SHADOW",  "Cast shadows only",    2)
            ]
        )

        sinput_trancparency: SInput = create_sinput(
            'EdmGlassTransparencySocketType', #'EdmGlassTransparencySocketType',
            'Transparency',
            '',
            'ALPHA_BLENDING',
            None,
            'ALPHA_BLENDING',
            [
                ('ALPHA_BLENDING',      "Alpha Blending",               "", 0),
                ('SUM_BLENDING',        "Sum Blending",                 "", 1),
                ('SHADOWED_BLENDING',   "Shadowed Blending",            "", 2)
            ]
        )

        sinput_glass: SInput = create_sinput(
            'EdmSocketGlassType',
            'Glass Type',
            '',
            'GLASS_INSTRUMENTAL',
            None,
            'GLASS_INSTRUMENTAL',
            [
                ('GLASS_INSTRUMENTAL',   "Instrumental",    "GLASS INSTRUMENTAL",   0),
                ('GLASS_COCKPIT',        "Cockpit ",        "GLASS COCKPIT",       1)
            ]
        )
        
        inputs.append(sinput_shadow_caster)
        inputs.append(sinput_trancparency)
        inputs.append(sinput_glass)
    
    return inputs
