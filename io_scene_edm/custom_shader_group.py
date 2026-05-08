## Disclaimer: all new bpy.props.EnumProps need to be added to 'ENUM_PROPS_NAMES'

import bpy

from typing import List, Dict, Tuple
from serializer_tools import MatDesc
from bpy.types import ShaderNode, ShaderNodeCustomGroup, Operator, ShaderNodeGroup
from constants import (
    ShadowCasterEnumItems, 
    TransparencyEnumItems, 
    TransparencyGlassEnumItems,
    DeckTransparencyEnumItems, 
    GlassEnumItems
)
from materials.materials import (
    MATERIALS,
    build_material_descriptions, 
    isNodeEdm
)
from objects_custom_props import EDM_PropsEnumValues
from utils import make_socket_map

MaterialNameType = str
SocketNameType = str
SocketType = str

# -> List[identifier, name, description, idx]
def get_enum_items(material_descs: Dict[str, MatDesc]) -> Dict[MaterialNameType, Dict[SocketNameType, List[Tuple[str, str, str, int]]]]:
    items: Dict[MaterialNameType, Dict[SocketNameType, List[Tuple[str, str, str, int]]]] = {}
    for mat_name in material_descs.keys():
        material_desc: MatDesc = material_descs[mat_name]
        socket_items: Dict[SocketNameType, List[Tuple[str, str, str, int]]] = {}
        for input in [i for i in material_desc.inputs if hasattr(i, 'enum_values') and i.enum_values]:
            item = {input.bl_socket_idname : [enum for enum in input.enum_values]}
            socket_items.update(item)
        mat_item = {mat_name : socket_items}
        items.update(mat_item)
    return items

def get_enum_names(material_descs: Dict[str, MatDesc]) -> Dict[MaterialNameType, Dict[SocketNameType, str]]:
    names: Dict[MaterialNameType, Dict[SocketNameType, str]] = {}
    for mat_name in material_descs.keys():
        material_desc: MatDesc = material_descs[mat_name]
        socket_items: Dict[SocketNameType, str] = {}
        for input in [i for i in material_desc.inputs if hasattr(i, 'enum_values') and i.enum_values]:
            item = {input.bl_socket_idname : input.name}
            socket_items.update(item)
        mat_item = {mat_name : socket_items}
        names.update(mat_item)
    return names

def get_enum_names_map(names: Dict[MaterialNameType, Dict[SocketNameType, str]]) -> List[Tuple[SocketType, MaterialNameType, SocketNameType, int]]:
    list_enum: List[Tuple[str, str, str, int]] = []
    idx: int = 0
    for mat_name in names.keys():
        socket_map: Dict[SocketNameType, str] = names[mat_name]
        for socket_name in socket_map.keys():
            name: str = socket_map[socket_name]
            list_enum.append((socket_name, mat_name, name, idx))
            idx = idx + 1
    return list_enum

def has_edm_group(context):
    if not context.active_node:
        return False

    node: ShaderNode = context.active_node
        
    is_selected: bool = node.select
    if not is_selected:
        return False
    
    if not isNodeEdm(node.bl_idname):
        return False
    
    group: ShaderNodeGroup = node
    if not group.node_tree:
        return False
    
    node_tree_name: str = group.node_tree.name
    if node_tree_name not in MATERIALS:
        return False

    return True

class PANEL_OT_EDM_add_material_enum(Operator):
    bl_idname = "panel.edm_add_material_enum"
    bl_label = "Add Enum"
    bl_description = "Click to add another new enumeration"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

class PANEL_OT_EDM_delete_socket(Operator):
    bl_idname = "panel.edm_delete_socket"
    bl_label = "Delete Socket"
    bl_description = "Click to delete socket"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

class PANEL_OT_EDM_add_socket(Operator):
    bl_idname = "panel.edm_add_socket"
    bl_label = "Add Socket"
    bl_description = "Click to add another new socket"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

class PANEL_OT_EDM_delete_enum_value(Operator):
    bl_idname = "panel.edm_delete_enum_value"
    bl_label = "Delete Value"
    bl_description = "Click to delete value from enumeration"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

class PANEL_OT_EDM_add_enum_value(Operator):
    bl_idname = "panel.edm_add_enum_value"
    bl_label = "Add Value"
    bl_description = "Click to add another new value to enumeration"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

class EPSHADER_PT_EnumPanel(bpy.types.Panel):
    bl_label = "EDM Enum Tool"
    bl_idname = "EPSHADER_PT_EnumPanel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "EDM Enum Tool"

    def __init__(self) -> None:
        super().__init__()
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()
        self.prop_names = get_enum_items(self.material_desc)

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        custom_names: EDM_PropsEnumValues = context.scene.EDMEnumItems

        layout = self.layout

        top_box = layout.box()
        top_row1 = top_box.row()
        top_row1.operator(PANEL_OT_EDM_add_material_enum.bl_idname)
        top_row1.prop(data=custom_names, property='mat_name_prop', text="")

        for mat_name in self.prop_names.keys():
            mat_box = layout.box()
            
            split1 = mat_box.split(factor=0.33)
            left_col1 = split1.column()
            right_col1 = split1.column()
            right_col1.label(text=mat_name)

            row2 = mat_box.row()
            row2.operator(PANEL_OT_EDM_add_socket.bl_idname)
            row2.prop(data=custom_names, property='socket_name_prop', text="")
            for socket_name in self.prop_names[mat_name].keys():
                socket_box = mat_box.box()

                split1 = socket_box.split(factor=0.33)
                left_col1 = split1.column()
                right_col1 = split1.column()
                right_col1.label(text=socket_name)

                for enum_name in self.prop_names[mat_name][socket_name]:
                    row1 = socket_box.row()
                    row1.label(text=enum_name[0])
                    row1.operator(PANEL_OT_EDM_delete_enum_value.bl_idname)

        return

class GPSHADER_PT_GroupPanel(bpy.types.Panel):
    bl_label = "EDM Group Props"
    bl_idname = "GPSHADER_PT_GroupPanel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "EDM Group Props"

    material_desc: Dict[str, MatDesc]
    prop_names: Dict[MaterialNameType, Dict[SocketNameType, List[Tuple[str, str, str, int]]]]
    names: Dict[str, Dict[str, str]]
    
    def __init__(self) -> None:
        super().__init__()
        self.material_desc = build_material_descriptions()
        self.prop_names = get_enum_items(self.material_desc)
        self.names: Dict[str, Dict[str, str]] = get_enum_names(self.material_desc)

    @classmethod
    def poll(cls, context):
        if not has_edm_group(context):
            return False
        return True

    def draw(self, context):
        layout = self.layout
        
        group: ShaderNode = context.active_node
        node_tree_name: str = group.node_tree.name

        box = layout.box()
        for socket_name in self.prop_names[node_tree_name].keys():
            ename: str = self.names[node_tree_name][socket_name]
            row = box.row()
            row.prop(group, socket_name, text=ename)

class BaseEdmMatrialShaderNode(ShaderNodeCustomGroup):
    def post_init(self, matrial_desc: MatDesc):
        self.node_tree = matrial_desc.create_custom()

    def init(self, context):
        self.width = 400

    def draw_buttons(self, context, layout):
        pass


class EdmMatrialShaderNode(BaseEdmMatrialShaderNode):
    bl_name = 'EDM Matrial Shader Node'
    bl_idname = 'EdmMatrialShaderNodeType'
    bl_label = 'Eagle Dynamics Matrial'
    bl_icon = 'NONE'

    def draw_buttons(self, context, layout):
        if not hasattr(self, 'node_tree'):
            return
        mat_name: str = self.node_tree.name

        box = layout.box()
        row = box.row()
        row.prop(self, "material_name", text="Material Name")
        socket_map: Dict[str, Dict[str, str]] = make_socket_map(self)
        if not socket_map.get(mat_name):
            return
        for socket_name, socket_type in socket_map[mat_name].items():
            row=box.row()
            row.prop(self, socket_type, text=socket_name)

class EdmDefaultShaderNode(BaseEdmMatrialShaderNode):
    bl_name = 'EDM_Default_Material'
    bl_idname = 'EdmDefaultShaderNodeType'
    bl_label = 'EDM_Default_Material'
    bl_icon = 'NONE'

    shadow_caster: bpy.props.EnumProperty (
        name        = 'Shadow Caster',
        description = "Does mesh cast shadow",
        items       = ShadowCasterEnumItems
    )

    transparency: bpy.props.EnumProperty(
        name        = 'Transparency',
        description = "Transparency/blending mode",
        items       = TransparencyEnumItems
    )

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, "shadow_caster")

        row = layout.row()
        row.prop(self, "transparency")

class EdmDeckShaderNode(BaseEdmMatrialShaderNode):
    bl_name = 'EDM_Deck_Material'
    bl_idname = 'EdmDeckShaderNodeType'
    bl_label = 'EDM_Deck_Material'
    bl_icon = 'NONE'

    deck_transparency: bpy.props.EnumProperty(
        name        = 'Transparency',
        description = "Deck Transparency",
        items       = DeckTransparencyEnumItems
    )

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, "deck_transparency")

class EdmFakeOmniShaderNode(BaseEdmMatrialShaderNode):
    bl_name = 'EDM_Fake_Omni_Material'
    bl_idname = 'EdmFakeOmniShaderNodeType'
    bl_label = 'EDM_Fake_Omni_Material'
    bl_icon = 'NONE'

class EdmFakeSpotShaderNode(BaseEdmMatrialShaderNode):
    bl_name = 'EDM_Fake_Spot_Material'
    bl_idname = 'EdmFakeSpotShaderNodeType'
    bl_label = 'EDM_Fake_Spot_Material'
    bl_icon = 'NONE'

class EdmMirrorShaderNode(BaseEdmMatrialShaderNode):
    bl_name = 'EDM_Mirror_Material'
    bl_idname = 'EdmMirrorShaderNodeType'
    bl_label = 'EDM_Mirror_Material'
    bl_icon = 'NONE'

class EdmGlassShaderNode(BaseEdmMatrialShaderNode):
    bl_name = 'EDM_Glass_Material'
    bl_idname = 'EdmGlassShaderNodeType'
    bl_label = 'EDM_Glass_Material'
    bl_icon = 'NONE'

    glass_shadow_caster: bpy.props.EnumProperty (
        name        = 'Shadow Caster',
        description = "Does mesh cast shadow",
        items       = ShadowCasterEnumItems
    )

    glass_transparency: bpy.props.EnumProperty(
        name        = 'Transparency',
        description = "Transparency/blending mode",
        items       = TransparencyGlassEnumItems
    )

    glass_type: bpy.props.EnumProperty (
        name        = 'Glass Type',
        description = "Glass type",
        items       = GlassEnumItems
    )

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, "glass_shadow_caster")

        row = layout.row()
        row.prop(self, "glass_transparency")

        row = layout.row()
        row.prop(self, "glass_type")

def get_custom_shader_group_classes():
    return [
        PANEL_OT_EDM_add_material_enum,
        PANEL_OT_EDM_delete_enum_value,
        PANEL_OT_EDM_add_enum_value,
        PANEL_OT_EDM_delete_socket,
        PANEL_OT_EDM_add_socket,
        EPSHADER_PT_EnumPanel,
        GPSHADER_PT_GroupPanel,
    ]
