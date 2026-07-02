import os
import re
import sys
from dataclasses import dataclass
from typing import List, Union, Dict, Sequence, Tuple, Optional, Any
import traceback

import enums
from socket_types import SInput, SOutput
from version_specific import create_node_in_node_tree
if 'bpy' in sys.modules:
    from bpy.types import NodeLink, ShaderNode, Node, NodeTree, NodeSocket, NodeInputs, NodeOutputs, ColorRamp
    import bpy
    from mathutils import Color
    from utils import last_braces_re_c, type_helper
else: 
    from dummy_bpy_classes import (
        Color,
        NodeLink, 
        ShaderNode, 
        Node, NodeTree, 
        NodeSocket, 
        NodeInputs, 
        NodeOutputs,
    )

@dataclass
class ramp_type:
    color_mode: str
    hue_interpolation: str
    interpolation: str
    elements: List[Tuple[float, Color]]

def copy_attrs(source, destination, attrs: List[str]) -> None:
    for attrib in attrs:

        value = getattr(source, attrib)
        if type(value) is ramp_type and hasattr(destination, 'color_ramp'):
            ramp: ramp_type = value
            setattr(destination.color_ramp, 'color_mode', ramp.color_mode)
            setattr(destination.color_ramp, 'hue_interpolation', ramp.hue_interpolation)
            setattr(destination.color_ramp, 'interpolation', ramp.interpolation)
            for idx, elem in enumerate(ramp.elements):
                if idx == 0 or (idx == len(ramp.elements) - 1):
                    new_elem = destination.color_ramp.elements[idx]
                    new_elem.position = elem[0]
                    new_elem.color = elem[1]
                else:
                    new_elem = destination.color_ramp.elements.new(elem[0])
                    new_elem.color = elem[1]
        elif type(value) is ColorRamp and hasattr(source, 'color_ramp'):
            ramp = ramp_type(value.color_mode, value.hue_interpolation, value.interpolation, [(elem.position, elem.color[:]) for elem in value.elements])
            setattr(destination, attrib, ramp)
        elif attrib == 'subsurface_method' and value == 'RANDOM_WALK_SKIN' and bpy.app.version[0] == 3:
            setattr(destination, attrib, 'RANDOM_WALK')
        else:
            setattr(destination, attrib, type_helper(value))

class SNode:
    def __init__(self, node: ShaderNode, attrs: List[str]) -> None:
        self.attrs = [
            "bl_idname",
            "color",
            "height",
            "hide",
            "label",
            "select",
            "show_options",
            "show_preview", 
            "location",
            "mute",
            "name",
            "show_texture",
            "use_custom_color",
            "width"
        ]
        self.attrs += attrs
        copy_attrs(node, self, self.attrs)
        self.input_defaults = [(x.name, type_helper(x.default_value)) for x in node.inputs if hasattr(x, 'default_value')]

    def create(self, node_tree: NodeTree) -> Node:        
        node = create_node_in_node_tree(self.bl_idname, node_tree)
        
        copy_attrs(self, node, self.attrs)

        inputs_with_defs = [x for x in node.inputs if hasattr(x, 'default_value')]
        inputs_names = [x.name for x in inputs_with_defs]
        defs_names = [x[0] for x in self.input_defaults]
        if inputs_names == defs_names:
            for i in zip(inputs_with_defs, self.input_defaults):
                try:
                    i[0].default_value = i[1][1]
                except ValueError:
                    # It seems reroute node takes default value from connected nodes.
                    pass
                except TypeError:
                    # It seems reroute node takes default value from connected nodes.
                    pass
        
        return node
    
class SNodeMixRGB(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, ["blend_type", "use_alpha", "use_clamp"])

class SNodeMix(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, ["blend_type", "clamp_factor", "clamp_result", "data_type", "factor_mode"])

class SNodeSeparateColor(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, ["mode"])

class SNodeSeparateRGB(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, [])

class SNodeColorRamp(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, ["color_ramp"])

    def make_atrib(self, destination, attrib, value):
        if type(value) is ramp_type and hasattr(destination, 'color_ramp'):
            ramp: ramp_type = value
            setattr(destination.color_ramp, 'color_mode', ramp.color_mode)
            setattr(destination.color_ramp, 'hue_interpolation', ramp.hue_interpolation)
            setattr(destination.color_ramp, 'interpolation', ramp.interpolation)
            for idx, elem in enumerate(ramp.elements):
                if idx == 0 or (idx==len(ramp.elements)-1):
                    new_elem = destination.color_ramp.elements[idx]
                    new_elem.position = elem[0]
                    new_elem.color = elem[1]
                else:
                    new_elem = destination.color_ramp.elements.new(elem[0])
                    new_elem.color = elem[1]
        elif type(value) is ColorRamp:
            ramp = ramp_type(value.color_mode, value.hue_interpolation, value.interpolation, [(elem.position, elem.color[:]) for elem in value.elements])
            setattr(destination, attrib, ramp)
        else:
            setattr(destination, attrib, type_helper(value))

class SNodeInvert(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, [])

class SNodeCombineRGB(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, [])

class SNodeCombineColor(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, ["mode"])

class SNodeNormalMap(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, ["space", "uv_map"])

class SNodeBsdfPrincipled(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, ["distribution", "subsurface_method"])

class SNodeGroupInput(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, [])

class SNodeGroupOutput(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, [])

class SNodeReroute(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, [])

class SShaderNode(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, [])

class SShaderNodeMath(SNode):
    def __init__(self, node: ShaderNode) -> None:
        super().__init__(node, ['operation', 'use_clamp'])

def get_socket_name_type(socket_collection: Union[NodeOutputs, NodeInputs], name: str, bpy_type_name: str, socket_idx: int) -> Union[None, NodeSocket]:
    result: NodeSocket = None
    if socket_idx and socket_idx >= 0 and socket_idx < len(socket_collection):
        result = socket_collection[socket_idx]
        if result.name == name and result.bl_idname == bpy_type_name:
            return result

    if not name or not bpy_type_name:
        return result
    for socket in socket_collection:
        if(socket.name == name and socket.bl_idname == bpy_type_name):
            result = socket
            break
    if not result:
        name_re_c = re.compile(f'.*{str(name)}.*')
        for socket in socket_collection:
            socket_re_c = re.compile(f'.*{str(socket.name)}.*')
            if((re.match(name_re_c, socket.name) or re.match(socket_re_c, name)) and socket.bl_idname == bpy_type_name):
                result = socket
                break
    if not result:
        result = socket_collection.get(name)
    return result

class SLink:
    def __init__(self, link: NodeLink) -> None:
        from_socket_path: str = link.from_socket.path_from_id()
        from_socket_m = re.match(last_braces_re_c, from_socket_path)
        from_socket_idx = int(from_socket_m.group(1)) if from_socket_m else -1
    
        to_socket_path: str = link.to_socket.path_from_id()
        to_socket_m = re.match(last_braces_re_c, to_socket_path)
        to_socket_idx = int(to_socket_m.group(1)) if to_socket_m else -1

        self.from_node = link.from_node.name
        self.from_socket = link.from_socket.name
        self.from_idname = link.from_socket.bl_idname
        self.from_type = link.from_node.bl_idname
        self.from_socket_idx = from_socket_idx
        self.is_muted = link.is_muted
        self.is_valid = link.is_valid
        self.to_node = link.to_node.name
        self.to_socket = link.to_socket.name
        self.to_idname = link.to_socket.bl_idname
        self.to_type = link.to_node.bl_idname
        self.to_socket_idx = to_socket_idx

    def create(self, node_tree: NodeTree, nodes: Dict[str, Node]):
        a: ShaderNode = nodes.get(self.from_node)
        b: ShaderNode = nodes.get(self.to_node)
        link: NodeLink = None
        if a and b:
            socket_from: NodeSocket = get_socket_name_type(a.outputs, self.from_socket, self.from_idname, self.from_socket_idx)
            socket_to: NodeSocket = get_socket_name_type(b.inputs, self.to_socket, self.to_idname, self.to_socket_idx)
            # socket_from: NodeSocket = a.outputs[self.from_socket_idx]
            # socket_to: NodeSocket = b.inputs[self.to_socket_idx]
            if socket_from and socket_to:
                link = node_tree.links.new(socket_from, socket_to)
        return link
    
    def __str__(self) -> str:
        return f'{self.from_node}: {self.from_socket} --> {self.to_node}: {self.to_socket}'
    
    def __eq__(self, v):
        for i in self.__dict__.keys():
            if getattr(self, i) != getattr(v, i):
                return False
        return True

## sockest_list: List[SInput]
def get_first_socket_by_name(sockest_list, name: str):
    for socket in sockest_list:
        if socket.name == name:
            return socket
    return None