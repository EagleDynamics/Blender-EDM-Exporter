from dataclasses import dataclass

@dataclass
class SOutput:
    bl_socket_idname: str
    name: str
    description: str

@dataclass
class SInput:
    bl_socket_idname: str
    name: str
    description: str
    default_value: any
    value_range: tuple
    instance_value: any
    enum_values: list