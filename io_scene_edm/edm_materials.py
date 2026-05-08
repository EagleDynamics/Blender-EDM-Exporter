import typing

import bpy
from typing import Dict
from bpy.types import Context, Menu, Operator, ShaderNodeGroup, NodeTree
from serializer_tools import MatDesc
from custom_shader_group import (
    EdmMatrialShaderNode, 
    EdmDefaultShaderNode, 
    EdmDeckShaderNode, 
    EdmFakeOmniShaderNode, 
    EdmFakeSpotShaderNode,
    EdmGlassShaderNode,
    EdmMirrorShaderNode
)

import enums
from materials.materials import build_material_descriptions
from materials.material_default import DefaultMaterial
from materials.material_deck import DeckMaterial
from materials.material_fake_omni import OmniFakeLightsMaterial
from materials.material_fake_spot import SpotFakeLightsMaterial
from materials.material_glass import GlassMaterial
from materials.material_mirror import MirrorMaterial


def unselect_shading_nodes(context):
    for node in context.space_data.node_tree.nodes:
        node.select = False

def pool_materials(cls, context):
    if context.object is None:
        return False
    
    if not context.object.material_slots:
        return False
    
    material_slot = context.object.material_slots[context.object.active_material_index]
    if not material_slot:
        return False
    
    material = material_slot.material
    if not material:
        return False
    
    return True

def strap_shader_group(pbr_group: EdmMatrialShaderNode, material_desc: MatDesc):
    pbr_group.post_init(material_desc)

class NODE_OT_EDM_Deck_add(Operator):
    bl_idname = "node.ed_add_deck"
    bl_label = "Add node group deck"
    bl_description = "Add node group deck"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return pool_materials(cls, context)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()
    
    def execute(self, context: Context) -> typing.Union[typing.Set[int], typing.Set[str]]:
        deck_group: ShaderNodeGroup = context.space_data.node_tree.nodes.new(type = enums.BpyShaderNode.NODE_GROUP)
        deck_tree: NodeTree = bpy.data.node_groups.get(DeckMaterial.name)
        if not deck_tree:
            deck_tree = self.material_desc[DeckMaterial.name].create()
        deck_group.location = (100, 100)
        deck_group.width = 350
        deck_group.node_tree = deck_tree

        unselect_shading_nodes(context)

        return {'FINISHED'}

class NODE_OT_EDM_DeckNew_add(Operator):
    bl_idname = "node.ed_add_decknew"
    bl_label = "Add node group test"
    bl_description = "Add node group new deck"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return pool_materials(cls, context)
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()

    def execute(self, context: Context) -> typing.Union[typing.Set[int], typing.Set[str]]:
        pbr_group: EdmDeckShaderNode = context.space_data.node_tree.nodes.new(type = DeckMaterial.node_group_name)
        strap_shader_group(pbr_group, self.material_desc[DeckMaterial.name])
        
        unselect_shading_nodes(context)

        return {'FINISHED'}

class NODE_OT_EDM_DefaultNew_add(Operator):
    bl_idname = "node.ed_add_defaultnew"
    bl_label = "Add node group default new"
    bl_description = "Add node group new default"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return pool_materials(cls, context)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()

    def execute(self, context: Context) -> typing.Union[typing.Set[int], typing.Set[str]]:
        pbr_group: EdmDefaultShaderNode = context.space_data.node_tree.nodes.new(type = DefaultMaterial.node_group_name)
        strap_shader_group(pbr_group, self.material_desc[DefaultMaterial.name])
        
        unselect_shading_nodes(context)

        return {'FINISHED'}


class NODE_OT_EDM_Default_add(Operator):
    bl_idname = "node.ed_add_default"
    bl_label = "Add node group default"
    bl_description = "Add node group default"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return pool_materials(cls, context)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()

    def execute(self, context: Context) -> typing.Union[typing.Set[int], typing.Set[str]]:
        pbr_group: ShaderNodeGroup = context.space_data.node_tree.nodes.new(type = enums.BpyShaderNode.NODE_GROUP)
        pbr_tree: NodeTree = bpy.data.node_groups.get(DefaultMaterial.name)
        if not pbr_tree:
            pbr_tree = self.material_desc[DefaultMaterial.name].create()
        pbr_group.location = (100, 100)
        pbr_group.width = 350
        pbr_group.node_tree = pbr_tree
        
        unselect_shading_nodes(context)

        return {'FINISHED'}

class NODE_OT_EDM_Glass_add(Operator):
    bl_idname = "node.ed_add_glass"
    bl_label = "Add node group glass"
    bl_description = "Add node group glass"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return pool_materials(cls, context)
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()

    def execute(self, context: Context) -> typing.Union[typing.Set[int], typing.Set[str]]:
        pbr_group: ShaderNodeGroup = context.space_data.node_tree.nodes.new(type = enums.BpyShaderNode.NODE_GROUP)
        pbr_tree: NodeTree = bpy.data.node_groups.get(GlassMaterial.name)
        if not pbr_tree:
            pbr_tree = self.material_desc[GlassMaterial.name].create()
        pbr_group.location = (100, 100)
        pbr_group.width = 350
        pbr_group.node_tree = pbr_tree
        
        unselect_shading_nodes(context)

        return {'FINISHED'}
    

class NODE_OT_EDM_Mirror_add(Operator):
    bl_idname = "node.ed_add_mirror"
    bl_label = "Add node group mirror"
    bl_description = "Add node group mirror"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return pool_materials(cls, context)
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()

    def execute(self, context: Context) -> typing.Union[typing.Set[int], typing.Set[str]]:
        pbr_group: ShaderNodeGroup = context.space_data.node_tree.nodes.new(type = enums.BpyShaderNode.NODE_GROUP)
        pbr_tree: NodeTree = bpy.data.node_groups.get(MirrorMaterial.name)
        if not pbr_tree:
            pbr_tree = self.material_desc[MirrorMaterial.name].create()
        pbr_group.location = (100, 100)
        pbr_group.width = 350
        pbr_group.node_tree = pbr_tree
        
        unselect_shading_nodes(context)

        return {'FINISHED'}


class NODE_OT_EDM_GlassNew_add(Operator):
    bl_idname = "node.ed_add_glassnew"
    bl_label = "Add node group glass new"
    bl_description = "Add node group new glass"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return pool_materials(cls, context)
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()

    def execute(self, context: Context) -> typing.Union[typing.Set[int], typing.Set[str]]:
        pbr_group: EdmGlassShaderNode = context.space_data.node_tree.nodes.new(type = GlassMaterial.node_group_name)
        strap_shader_group(pbr_group, self.material_desc[GlassMaterial.name])
        
        unselect_shading_nodes(context)

        return {'FINISHED'}
    

class NODE_OT_EDM_MirrorNew_add(Operator):
    bl_idname = "node.ed_add_mirrornew"
    bl_label = "Add node group mirror new"
    bl_description = "Add node group new mirror"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return pool_materials(cls, context)
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()

    def execute(self, context: Context) -> typing.Union[typing.Set[int], typing.Set[str]]:
        pbr_group: EdmMirrorShaderNode = context.space_data.node_tree.nodes.new(type = MirrorMaterial.node_group_name)
        strap_shader_group(pbr_group, self.material_desc[MirrorMaterial.name])
        
        unselect_shading_nodes(context)

        return {'FINISHED'}

class NODE_OT_EDM_Omni_add(Operator):
    bl_idname = "node.ed_add_omni"
    bl_label = "Add node group omni"
    bl_description = "Add node group omni"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return pool_materials(cls, context)
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()

    def execute(self, context: Context) -> typing.Union[typing.Set[int], typing.Set[str]]:
        omni_group: ShaderNodeGroup = context.space_data.node_tree.nodes.new(type = enums.BpyShaderNode.NODE_GROUP)
        omni_tree: NodeTree = bpy.data.node_groups.get(OmniFakeLightsMaterial.name)
        if not omni_tree:
            omni_tree = self.material_desc[OmniFakeLightsMaterial.name].create()
        omni_group.location = (100, 100)
        omni_group.width = 350
        omni_group.node_tree = omni_tree
        
        unselect_shading_nodes(context)

        return {'FINISHED'}

class NODE_OT_EDM_OmniNew_add(Operator):
    bl_idname = "node.ed_add_omninew"
    bl_label = "Add node group omni new"
    bl_description = "Add node group new omni"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return pool_materials(cls, context)
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()

    def execute(self, context: Context) -> typing.Union[typing.Set[int], typing.Set[str]]:
        pbr_group: EdmFakeOmniShaderNode = context.space_data.node_tree.nodes.new(type = OmniFakeLightsMaterial.node_group_name)
        strap_shader_group(pbr_group, self.material_desc[OmniFakeLightsMaterial.name])
        
        unselect_shading_nodes(context)

        return {'FINISHED'}

class NODE_OT_EDM_Spot_add(Operator):
    bl_idname = "node.ed_add_spot"
    bl_label = "Add node group spot"
    bl_description = "Add node group spot"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return pool_materials(cls, context)
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()

    def execute(self, context: Context) -> typing.Union[typing.Set[int], typing.Set[str]]:
        spot_group: ShaderNodeGroup = context.space_data.node_tree.nodes.new(type = enums.BpyShaderNode.NODE_GROUP)
        spot_tree: NodeTree = bpy.data.node_groups.get(SpotFakeLightsMaterial.name)
        if not spot_tree:
            spot_tree = self.material_desc[SpotFakeLightsMaterial.name].create()
        spot_group.location = (100, 100)
        spot_group.width = 350
        spot_group.node_tree = spot_tree

        return {'FINISHED'}

class NODE_OT_EDM_SpotNew_add(Operator):
    bl_idname = "node.ed_add_spotnew"
    bl_label = "Add node group spot new"
    bl_description = "Add node group new spot"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return pool_materials(cls, context)
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.material_desc: Dict[str, MatDesc] = build_material_descriptions()

    def execute(self, context: Context) -> typing.Union[typing.Set[int], typing.Set[str]]:
        pbr_group: EdmFakeSpotShaderNode = context.space_data.node_tree.nodes.new(type = SpotFakeLightsMaterial.node_group_name)
        strap_shader_group(pbr_group, self.material_desc[SpotFakeLightsMaterial.name])
        
        unselect_shading_nodes(context)

        return {'FINISHED'}


class NODE_MT_EDM_Menu_add(Menu):
    bl_idname = 'NODE_MT_EDM_Menu_add'
    bl_label = "Node Template"

    @classmethod
    def poll(cls, context):
        return context.space_data.node_tree != None

    def draw(self, context):
        layout = self.layout

        group_name = "Material - Default"
        props = layout.operator(NODE_OT_EDM_DefaultNew_add.bl_idname, text = group_name)

        group_name = "Material - Deck"
        props = layout.operator(NODE_OT_EDM_DeckNew_add.bl_idname, text = group_name)

        group_name = "Material - Fake Omni"
        props = layout.operator(NODE_OT_EDM_OmniNew_add.bl_idname, text = group_name)
        
        group_name = "Material - Fake Spot"
        props = layout.operator(NODE_OT_EDM_SpotNew_add.bl_idname, text = group_name)

        group_name = "Material - Glass"
        props = layout.operator(NODE_OT_EDM_GlassNew_add.bl_idname, text = group_name)

        group_name = "Material - Mirror"
        props = layout.operator(NODE_OT_EDM_MirrorNew_add.bl_idname, text = group_name)


class NODE_MT_EDM_Dev_Menu_add(Menu):
    bl_idname = "NODE_MT_EDM_Dev_Menu_add"
    bl_label = "Dev Node Template"

    @classmethod
    def poll(cls, context):
        return context.space_data.node_tree != None

    def draw(self, context):
        layout = self.layout

        group_name = "Material - Default"
        props = layout.operator(NODE_OT_EDM_Default_add.bl_idname, text = group_name)

        group_name = "Material - Deck"
        props = layout.operator(NODE_OT_EDM_Deck_add.bl_idname, text = group_name)

        group_name = "Material - Fake Omni"
        props = layout.operator(NODE_OT_EDM_Omni_add.bl_idname, text = group_name)

        group_name = "Material - Fake Spot"
        props = layout.operator(NODE_OT_EDM_Spot_add.bl_idname, text = group_name)

        group_name = "Material - Glass"
        props = layout.operator(NODE_OT_EDM_Glass_add.bl_idname, text = group_name)

        group_name = "Material - Mirror"
        props = layout.operator(NODE_OT_EDM_Mirror_add.bl_idname, text = group_name)


def get_material_classes():
    return [
        EdmMatrialShaderNode,
        EdmDefaultShaderNode,
        EdmDeckShaderNode,
        EdmFakeOmniShaderNode,
        EdmFakeSpotShaderNode,
        EdmGlassShaderNode,
        EdmMirrorShaderNode,
        NODE_OT_EDM_DefaultNew_add,
        NODE_OT_EDM_Default_add,
        NODE_OT_EDM_Deck_add,
        NODE_OT_EDM_DeckNew_add,
        NODE_OT_EDM_Omni_add,
        NODE_OT_EDM_OmniNew_add,
        NODE_OT_EDM_Spot_add,
        NODE_OT_EDM_SpotNew_add,
        NODE_OT_EDM_Glass_add,
        NODE_OT_EDM_GlassNew_add,
        NODE_OT_EDM_Mirror_add,
        NODE_OT_EDM_MirrorNew_add,        
        NODE_MT_EDM_Menu_add,
        NODE_MT_EDM_Dev_Menu_add,
    ]
