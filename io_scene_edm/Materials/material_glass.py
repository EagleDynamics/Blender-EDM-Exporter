from bpy.types import (
    Material,
    ShaderNodeGroup,
)

import animation as anim
from pyedm_platform_selector import pyedm
from objects_custom_props import get_edm_props
from materials.material_interface import IMaterial
from materials.material_wrap import (
    TextureDesk,
    ValueDesk,
    ValueDeskDropDown
)
from enums import (
    BpyNodeSocketType,
    NodeSocketCommonEnum,
    NodeSocketInGlassEnum,
)
from materials.materials_common import (
    add_block,
    make_def_base_block,
    make_def_rmo_block,
    make_def_normal_block,
    make_def_flir_block,
    make_def_damage_block,
    make_def_bone_block,
    make_glass_block,
    get_shadow_caster_value,
    get_glass_transparency_value,
    get_glass_value
)
from node_tree_tools import get_version

GLASS_MATERIAL_NAME = 'EDM_Glass_Material'

## Glass material
class GlassMaterial(IMaterial):
    name = GLASS_MATERIAL_NAME
    description_file_name = f'data/{GLASS_MATERIAL_NAME}.pickle'
    node_group_name = 'EdmGlassShaderNodeType'

    class Textures:
        def __init__(self, node_group: ShaderNodeGroup) -> None:
            self.glass_filter   = TextureDesk(node_group, NodeSocketInGlassEnum.GLASS_COLOR, BpyNodeSocketType.COLOR)
            self.albedo         = TextureDesk(node_group, NodeSocketInGlassEnum.DIRT_COLOR, BpyNodeSocketType.COLOR)
            self.rmo            = TextureDesk(node_group, NodeSocketInGlassEnum.ROUGH_METAL, BpyNodeSocketType.COLOR)
            self.normal         = TextureDesk(node_group, NodeSocketInGlassEnum.NORMAL, BpyNodeSocketType.COLOR)
            self.flir           = TextureDesk(node_group, NodeSocketInGlassEnum.FLIR, BpyNodeSocketType.COLOR)
            self.damage_color   = TextureDesk(node_group, NodeSocketInGlassEnum.DAMAGE_COLOR, BpyNodeSocketType.COLOR)
            self.damage_normal  = TextureDesk(node_group, NodeSocketInGlassEnum.DAMAGE_NORMAL, BpyNodeSocketType.COLOR)
            self.damage_mask    = TextureDesk(node_group, NodeSocketInGlassEnum.DAMAGE_MASK, BpyNodeSocketType.COLOR)
            self.damage_alpha   = TextureDesk(node_group, NodeSocketInGlassEnum.DAMAGE_ALPHA, BpyNodeSocketType.COLOR)

    class Values:
        def __init__(self, node_group: ShaderNodeGroup) -> None:
            self.alpha              = ValueDesk(node_group, NodeSocketInGlassEnum.DIRT_ALPHA, BpyNodeSocketType.FLOAT, 1.0)
            self.blend_mode         = ValueDeskDropDown(node_group, NodeSocketInGlassEnum.TRANSPARENCY, BpyNodeSocketType.GLASS_TRANSPARENCY, 'ALPHA_BLENDING')
            self.shadow_caster      = ValueDeskDropDown(node_group, NodeSocketInGlassEnum.SHADOW_CASTER, BpyNodeSocketType.GLASS_SHADOWCASTER, 'SHADOW_CASTER_YES')
            self.glass_type         = ValueDeskDropDown(node_group, NodeSocketInGlassEnum.GLASS_TYPE, BpyNodeSocketType.GLASSTYPE, 'GLASS_INSTRUMENTAL')
            self.version            = ValueDesk(node_group, NodeSocketCommonEnum.VERSION, BpyNodeSocketType.INTEGER, -1)
            self.opacity_value      = ValueDesk(node_group, NodeSocketInGlassEnum.OPACITY_VALUE, BpyNodeSocketType.FLOAT, 1.0)

    def __init__(self, bpy_material: Material, node_group: ShaderNodeGroup):
        self.bpy_material = bpy_material
        self.node_group = node_group
        self.is_valid = not self.node_group == None
        
        self.textures = GlassMaterial.Textures(self.node_group)
        self.values = GlassMaterial.Values(self.node_group)

        if self.is_valid:
            # apply
            for attr in self.textures.__dict__.keys():
                getattr(self.textures, attr).apply(self.node_group)
            for attr in self.values.__dict__.keys():
                getattr(self.values, attr).apply(self.node_group)

            # update
            for i in self.textures.__dict__.keys():
                getattr(self.textures, i).update()
            for i in self.values.__dict__.keys():
                getattr(self.values, i).update() 

    def build_blocks(self, object, mesh_storage):
        edm_props = get_edm_props(object)
        edm_render_node = pyedm.GlassNode(object.name, self.bpy_material.name)        
        edm_render_node.setIndices(mesh_storage.indices)

        add_block(edm_render_node, make_def_rmo_block(mesh_storage, self.textures, self.bpy_material))
        add_block(edm_render_node, make_def_normal_block(mesh_storage, self.textures, self.bpy_material))
        add_block(edm_render_node, make_def_flir_block(self.textures))
        add_block(edm_render_node, make_def_damage_block(mesh_storage, self.textures, edm_props, self.bpy_material))
        add_block(edm_render_node, make_def_bone_block(mesh_storage))
        add_block(edm_render_node, make_glass_block(mesh_storage, self.bpy_material, self.textures, self.values,
                                                self.is_valid, edm_props))
        add_block(edm_render_node, make_def_base_block(mesh_storage, self.bpy_material, self.textures, self.values,
                                                       self.is_valid, edm_props))
        
        transparency_mode: int = get_glass_transparency_value(self.values.blend_mode.value)
        edm_render_node.setTransparentMode(transparency_mode)

        shadow_caster_type: int = get_shadow_caster_value(self.values.shadow_caster.value)
        edm_render_node.setShadowCaster(shadow_caster_type)

        glass_type: int = get_glass_value(self.values.glass_type.value)
        edm_render_node.setGlassType(glass_type)

        opacity_value_path: str = self.values.opacity_value.anim_path
        is_color_value_animated: bool = opacity_value_path and anim.has_path_anim(self.bpy_material.node_tree.animation_data, opacity_value_path)
        if is_color_value_animated and edm_props.OPACITY_VALUE_ARG != -1:
            arg_opacity_value_n: int = edm_props.OPACITY_VALUE_ARG
            key_opacity_value_list: anim.KeyFramePoints = anim.extract_anim_float(self.bpy_material.node_tree.animation_data.action, opacity_value_path)
            opacity_value_prop = pyedm.PropertyFloat(arg_opacity_value_n, key_opacity_value_list)
            edm_render_node.setOpacityValue(opacity_value_prop)
        else:
            opacity_value_prop = pyedm.PropertyFloat(self.values.opacity_value.value)
            edm_render_node.setOpacityValue(opacity_value_prop)

        two_sided: bool = edm_props.TWO_SIDED
        edm_render_node.setTwoSided(two_sided)

        return edm_render_node
    
    @classmethod
    def process_links(cls, old_links, old_version, group_node_type_name):
        return old_links
    
    @classmethod 
    def restore_defaults(cls, old_sockest, new_node_group, drop_down_values, old_version, material_name):
        version_new: int = get_version(new_node_group.node_tree)

        if old_version == 0:
            return
        
        ## copy old drop-down values to new created node_group
        for key, val in drop_down_values.items():
            setattr(new_node_group, key, val)
            
        for new_socket in new_node_group.inputs:
            if new_socket.name == NodeSocketCommonEnum.VERSION:
                new_socket.default_value = version_new
                break

        