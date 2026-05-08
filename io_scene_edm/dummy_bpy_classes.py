## This file contains dummy bpy classes.
## It is needed only for scripts run outside the blender plugin. 

from typing import Sequence, Any

class Color:
    b: float
    g: float
    h: float
    hsv: Sequence[float]
    is_frozen: bool
    is_valid: bool
    is_wrapped: bool
    owner: Any
    r: float
    s: float
    v: float

class ShaderNode:
    pass

class NodeTree:
    pass

class Node:
    pass

class NodeOutputs:
    pass

class NodeInputs:
    pass

class NodeSocket:
    pass

class NodeLink:
    pass

class InterfaceNodeSocket:
    pass

class ShaderNodeGroup:
    pass

class NodeTreeInterfaceSocket:
    pass