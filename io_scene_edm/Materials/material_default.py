import copy
from typing import List, Dict, Callable

from bpy.types import (
    Material,
    ShaderNodeGroup,
)

import utils
import animation as anim
from logger import log
from mesh_storage import MeshStorage
from pyedm_platform_selector import pyedm
from objects_custom_props import get_edm_props
from socket_types import SInput
from serializer import SLink, get_first_socket_by_name
from node_tree_tools import get_version
from custom_sockets import TransparencyEnumItems, ShadowCasterEnumItems
from materials.material_interface import IMaterial

from materials.material_wrap import (
    TextureDesk,
    ValueDesk,
    ValueDeskDropDown
)
from enums import (
    BpyShaderNode, 
    BpyNodeSocketType,
    NodeSocketCommonEnum,
    NodeSocketInDeckEnum, 
    NodeSocketInDefaultEnum
)
from materials.materials_common import (
    add_block,
    make_def_base_block,
    make_def_rmo_block,
    make_def_normal_block,
    make_def_decal_block,
    make_def_emissive_block,
    make_def_ao_block,
    make_def_flir_block,
    make_def_damage_block,
    make_def_bone_block,
    make_def_number_block,
    get_shadow_caster_value,
    get_transparency_value,
)


DEFAULT_MATERIAL_NAME = 'EDM_Default_Material'

## Default material
class DefaultMaterial(IMaterial):
    name = DEFAULT_MATERIAL_NAME
    description_file_name = f'data/{DEFAULT_MATERIAL_NAME}.pickle'
    node_group_name = 'EdmDefaultShaderNodeType'
   
    class Textures:
        def __init__(self, node_group: ShaderNodeGroup) -> None:
            self.albedo         = TextureDesk(node_group, NodeSocketInDefaultEnum.BASE_COLOR, BpyNodeSocketType.COLOR)
            self.decal          = TextureDesk(node_group, NodeSocketInDefaultEnum.DECAL_COLOR, BpyNodeSocketType.COLOR)
            self.rmo            = TextureDesk(node_group, NodeSocketInDefaultEnum.ROUGH_METAL, BpyNodeSocketType.COLOR)
            self.light_map      = TextureDesk(node_group, NodeSocketInDefaultEnum.LIGHTMAP, BpyNodeSocketType.COLOR)
            self.normal         = TextureDesk(node_group, NodeSocketInDefaultEnum.NORMAL, BpyNodeSocketType.COLOR)
            self.emissive       = TextureDesk(node_group, NodeSocketInDefaultEnum.EMISSIVE, BpyNodeSocketType.COLOR)
            self.emissive_mask  = TextureDesk(node_group, NodeSocketInDefaultEnum.EMISSIVE_MASK, BpyNodeSocketType.FLOAT)
            self.flir           = TextureDesk(node_group, NodeSocketInDefaultEnum.FLIR, BpyNodeSocketType.COLOR)
            self.damage_color   = TextureDesk(node_group, NodeSocketInDefaultEnum.DAMAGE_COLOR, BpyNodeSocketType.COLOR)
            self.damage_normal  = TextureDesk(node_group, NodeSocketInDefaultEnum.DAMAGE_NORMAL, BpyNodeSocketType.COLOR)
            self.damage_mask    = TextureDesk(node_group, NodeSocketInDefaultEnum.DAMAGE_MASK, BpyNodeSocketType.COLOR)
            self.damage_alpha   = TextureDesk(node_group, NodeSocketInDefaultEnum.DAMAGE_ALPHA, BpyNodeSocketType.COLOR)

    class Values:
        def __init__(self, node_group: ShaderNodeGroup) -> None:
            self.alpha              = ValueDesk(node_group, NodeSocketInDefaultEnum.BASE_ALPHA, BpyNodeSocketType.FLOAT, 1.0)
            self.decal_alpha        = ValueDesk(node_group, NodeSocketInDefaultEnum.DECAL_ALPHA, BpyNodeSocketType.FLOAT, 1.0)
            self.ao                 = ValueDesk(node_group, NodeSocketInDefaultEnum.AO_VALUE, BpyNodeSocketType.FLOAT, 0.0)
            self.light_map_value    = ValueDesk(node_group, NodeSocketInDefaultEnum.LIGHTMAP_VALUE, BpyNodeSocketType.FLOAT, 0.0)
            self.emissive_value     = ValueDesk(node_group, NodeSocketInDefaultEnum.EMISSIVE_VALUE, BpyNodeSocketType.FLOAT, 0.0)
            self.decal_id           = ValueDesk(node_group, NodeSocketInDefaultEnum.DECALID, BpyNodeSocketType.INTEGER, 0)
            self.blend_mode         = ValueDeskDropDown(node_group, NodeSocketInDefaultEnum.TRANSPARENCY, BpyNodeSocketType.TRANSPARENCY, 'OPAQUE')
            self.shadow_caster      = ValueDeskDropDown(node_group, NodeSocketInDefaultEnum.SHADOW_CASTER, BpyNodeSocketType.SHADOWCASTER, 'SHADOW_CASTER_YES')
            self.version            = ValueDesk(node_group, NodeSocketCommonEnum.VERSION, BpyNodeSocketType.INTEGER, -1)
            self.opacity_value      = ValueDesk(node_group, NodeSocketInDefaultEnum.OPACITY_VALUE, BpyNodeSocketType.FLOAT, 1.0)

    #TODO-270: copypasta in every material
    def __init__(self, bpy_material: Material, node_group: ShaderNodeGroup):
        self.bpy_material = bpy_material
        self.node_group = node_group
        self.is_valid = not self.node_group == None
        
        self.textures = DefaultMaterial.Textures(self.node_group)
        self.values = DefaultMaterial.Values(self.node_group)

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
        edm_render_node = pyedm.PBRNode(object.name, self.bpy_material.name)
        edm_render_node.setIndices(mesh_storage.indices)

        # create blocks and add them to 'edm_render_node'.
        # some methods 'make_def_..._block' might return None, so it would not be added to render node.
        add_block(edm_render_node, make_def_rmo_block(mesh_storage, self.textures, self.bpy_material))
        add_block(edm_render_node, make_def_normal_block(mesh_storage, self.textures, self.bpy_material))
        add_block(edm_render_node, make_def_decal_block(mesh_storage, self.textures, self.is_valid, self.bpy_material))
        add_block(edm_render_node, make_def_flir_block(self.textures))
        add_block(edm_render_node, make_def_damage_block(mesh_storage, self.textures, edm_props, self.bpy_material))
        add_block(edm_render_node, make_def_bone_block(mesh_storage))
        add_block(edm_render_node, make_def_number_block(mesh_storage, edm_props))
        add_block(edm_render_node, make_def_ao_block(mesh_storage, self.bpy_material, self.textures, self.values, 
                                                     self.is_valid, edm_props))
        add_block(edm_render_node, make_def_base_block(mesh_storage, self.bpy_material, self.textures, self.values,
                                                       self.is_valid, edm_props))
        add_block(edm_render_node, make_def_emissive_block(mesh_storage, self.bpy_material, self.textures, self.values,
                                                            self.is_valid, self.bpy_material.name, edm_props))
                                                                  
        
        decal_id: int = self.values.decal_id.value
        if(decal_id < 0 or decal_id > 8):
            log.fatal(f"{self.bpy_material.name} material has wrong value {str(decal_id)}. Decal id must be in 0 to 8 range.")
        edm_render_node.setDecalId(decal_id)
        
        transparency_mode: int = get_transparency_value(self.values.blend_mode.value)
        edm_render_node.setTransparentMode(transparency_mode)

        shadow_caster_type: int = get_shadow_caster_value(self.values.shadow_caster.value)
        edm_render_node.setShadowCaster(shadow_caster_type)

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
        new_links: List[SLink] = []
        
        if old_version == 0 or old_version == 1:
            for link in old_links:
                if link.to_type == 'ShaderNodeGroup':
                    if link.to_socket == 'Normal' or link.to_socket == 'Normal  (Non-Color)' or link.to_socket == 'Normal (Non color)':
                        link = copy.copy(link)
                        link.to_socket = NodeSocketInDefaultEnum.NORMAL
                new_links.append(link)
        elif old_version <= 11:
            for link in old_links:
                if link.to_type == 'ShaderNodeGroup':
                    if link.to_socket == 'Damage Color':
                        link = copy.copy(link)
                        link.to_socket = NodeSocketInDefaultEnum.DAMAGE_COLOR
                    elif link.to_socket == 'Damage Map':
                        link = copy.copy(link)
                        link.to_socket = NodeSocketInDeckEnum.DAMAGE_MASK
                    elif link.to_socket == 'Damage Map (Non-Color)':
                        link = copy.copy(link)
                        link.to_socket = NodeSocketInDeckEnum.DAMAGE_MASK
                    elif link.to_socket == 'Damage Normal':
                        link = copy.copy(link)
                        link.to_socket = NodeSocketInDefaultEnum.DAMAGE_NORMAL
                new_links.append(link)
        else:
            for link in old_links:
                new_links.append(link)

        return new_links
    
    @classmethod 
    def restore_defaults(cls, old_sockest, new_node_group, drop_down_values, old_version, material_name):
        version_new: int = get_version(new_node_group.node_tree)
        if old_version == 0:
            return
        if old_version < 8:
            for new_socket in new_node_group.inputs:
                old_socket_wrp: SInput = get_first_socket_by_name(old_sockest, new_socket.name)
                if not old_socket_wrp:
                    continue
                if new_socket.name == NodeSocketInDefaultEnum.SHADOW_CASTER and (old_socket_wrp.bl_socket_idname == 'NodeSocketUndefined' or not old_socket_wrp.instance_value):
                    new_socket.default_value = ShadowCasterEnumItems[0][0]
                    continue
                if new_socket.name == NodeSocketInDefaultEnum.SHADOW_CASTER:
                    new_socket.default_value = ShadowCasterEnumItems[old_socket_wrp.instance_value][0]
                    continue
                if new_socket.name == NodeSocketInDefaultEnum.TRANSPARENCY and (old_socket_wrp.bl_socket_idname == 'NodeSocketUndefined' or not old_socket_wrp.instance_value):
                    new_socket.default_value = TransparencyEnumItems[0][0]
                    continue
                if new_socket.name == NodeSocketInDefaultEnum.TRANSPARENCY:
                    new_socket.default_value = TransparencyEnumItems[old_socket_wrp.instance_value][0]
                    continue
                if new_socket.name == NodeSocketCommonEnum.VERSION:
                    new_socket.default_value = version_new
                    continue
                if hasattr(old_socket_wrp, 'instance_value'):
                    new_socket.default_value = old_socket_wrp.instance_value
        elif old_version >= 8:
            socket_map: Dict[str, Dict[str, str]] = utils.make_socket_map(new_node_group)
            socket_acro_map: Dict[str, str] = utils.make_acro_map(new_node_group)
            if socket_map.get(material_name):

                ## copy old drop-down values to new created node_group
                for key, val in drop_down_values.items():
                    setattr(new_node_group, key, val)

                ## TODO: DCSTOOLS-775. (Not sure 'for' is still needed.)
                for socket_name in socket_map[material_name].keys():
                    if new_node_group.bl_idname in ('EdmDefaultShaderNodeType', 'EdmDeckShaderNodeType', 
                                                    'EdmFakeOmniShaderNodeType', 'EdmFakeSpotShaderNodeType',
                                                    'EdmGlassShaderNodeType'):
                        prop_name: str = socket_acro_map.get(socket_name)
                        old_socket_wrp: SInput = get_first_socket_by_name(old_sockest, socket_name)
                        if hasattr(old_socket_wrp, 'instance_value'):
                            setattr(new_node_group, prop_name, old_socket_wrp.instance_value)
                    else:
                        enum_name: str = socket_map[material_name][socket_name]
                        old_socket_wrp: SInput = get_first_socket_by_name(old_sockest, socket_name)
                        if old_socket_wrp and hasattr(old_socket_wrp, 'instance_value'):
                            setattr(new_node_group, enum_name, old_socket_wrp.instance_value)
            for new_socket in new_node_group.inputs:
                old_socket_wrp: SInput = get_first_socket_by_name(old_sockest, new_socket.name)
                if not old_socket_wrp:
                    continue
                if new_socket.name == NodeSocketCommonEnum.VERSION:
                    new_socket.default_value = version_new
                    continue
                if old_socket_wrp.instance_value:
                    if new_socket.name not in (NodeSocketInDefaultEnum.TRANSPARENCY, NodeSocketInDefaultEnum.SHADOW_CASTER):
                        new_socket.default_value = old_socket_wrp.instance_value

