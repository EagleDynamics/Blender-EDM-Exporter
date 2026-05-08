import copy
from typing import List

from bpy.types import Material, ShaderNodeGroup
from logger import log
from node_tree_tools import get_version
from pyedm_platform_selector import pyedm
from objects_custom_props import get_edm_props
from socket_types import SInput
from serializer import SLink, get_first_socket_by_name
from materials.material_interface import IMaterial
from materials.material_wrap import (
    TextureDesk,
    ValueDesk,
    ValueDeskDropDown
)
from enums import (
    BpyNodeSocketType,
    NodeSocketCommonEnum,
    NodeSocketInDeckEnum,
    NodeSocketInDefaultEnum,
)
from materials.materials_common import (
    get_transparency_value
)

DECK_MATERIAL_NAME = 'EDM_Deck_Material'

# --- Deck
class DeckMaterial(IMaterial):
    name = DECK_MATERIAL_NAME
    description_file_name = f'data/{DECK_MATERIAL_NAME}.pickle'
    node_group_name = 'EdmDeckShaderNodeType'

    class Textures:
        def __init__(self, node_group: ShaderNodeGroup) -> None:
            self.base_tile_map      = TextureDesk(node_group, NodeSocketInDeckEnum.BASE_TILE_MAP, BpyNodeSocketType.COLOR)
            self.base_alpha         = TextureDesk(node_group, NodeSocketInDeckEnum.BASE_ALPHA, BpyNodeSocketType.COLOR)
            self.rmo_tile_map       = TextureDesk(node_group, NodeSocketInDeckEnum.RMO_TILE_MAP, BpyNodeSocketType.COLOR)
            self.normal_tile_map    = TextureDesk(node_group, NodeSocketInDeckEnum.NORMAL_TILE_MAP, BpyNodeSocketType.COLOR)
            self.decal_map          = TextureDesk(node_group, NodeSocketInDeckEnum.DECAL_BASE_COLOR, BpyNodeSocketType.COLOR)
            self.decal_alpha        = TextureDesk(node_group, NodeSocketInDeckEnum.DECAL_ALPHA, BpyNodeSocketType.COLOR)
            self.decal_rmo          = TextureDesk(node_group, NodeSocketInDeckEnum.DECAL_RMO, BpyNodeSocketType.COLOR)
            self.damage_color       = TextureDesk(node_group, NodeSocketInDeckEnum.DAMAGE_COLOR, BpyNodeSocketType.COLOR)
            self.damage_mask        = TextureDesk(node_group, NodeSocketInDeckEnum.DAMAGE_MASK, BpyNodeSocketType.COLOR)
            self.damage_normal      = TextureDesk(node_group, NodeSocketInDeckEnum.DAMAGE_NORMAL, BpyNodeSocketType.COLOR)
            self.damage_alpha       = TextureDesk(node_group, NodeSocketInDeckEnum.DAMAGE_ALPHA, BpyNodeSocketType.COLOR)
            self.rain_mask          = TextureDesk(node_group, NodeSocketInDeckEnum.RAIN_MASK, BpyNodeSocketType.COLOR)

    class Values:
        def __init__(self, node_group: ShaderNodeGroup) -> None:
            self.ao                 = ValueDesk(node_group, NodeSocketInDeckEnum.AO_VALUE, BpyNodeSocketType.FLOAT, 0.0)
            self.wetness            = ValueDesk(node_group, NodeSocketInDeckEnum.WETNESS, BpyNodeSocketType.FLOAT, 1.0)
            self.decal_id           = ValueDesk(node_group, NodeSocketInDeckEnum.DECALID, BpyNodeSocketType.INTEGER, 0)
            self.blend_mode         = ValueDeskDropDown(node_group, NodeSocketInDeckEnum.TRANSPARENCY, BpyNodeSocketType.TRANSPARENCY, 'OPAQUE')
            self.version            = ValueDesk(node_group, NodeSocketCommonEnum.VERSION, BpyNodeSocketType.INTEGER, -1)

    def __init__(self, bpy_material: Material, node_group: ShaderNodeGroup):
        self.bpy_material = bpy_material
        self.node_group = node_group
        self.is_valid = not self.node_group == None
        
        self.textures = DeckMaterial.Textures(self.node_group)
        self.values = DeckMaterial.Values(self.node_group)

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
        edm_render_node = pyedm.DeckNode(object.name, self.bpy_material.name)
        edm_render_node.setPositions(mesh_storage.positions)
        edm_render_node.setNormals(mesh_storage.normals)
        edm_render_node.setIndices(mesh_storage.indices)

        transparency_mode: int = get_transparency_value(self.values.blend_mode.value)
        edm_render_node.setTransparentMode(transparency_mode)

        decal_id: int = self.values.decal_id.value
        if(decal_id < 0 or decal_id > 8):
            log.fatal(f"{DeckMaterial.name} material has wrong value {str(decal_id)}. Decal id must be in 0 to 8 range.")
        edm_render_node.setDecalId(decal_id)

        if self.textures.base_tile_map.texture:
            base_tile_uv_map_name: str = self.textures.base_tile_map.texture.get_uv_map(mesh_storage.uv_active)
            edm_render_node.setTiledUV(mesh_storage.get_uv(base_tile_uv_map_name, self.bpy_material.name))

            base_tile_map_name: str = self.textures.base_tile_map.texture.texture_name
            edm_render_node.setBaseTiledMap(base_tile_map_name)

        if self.textures.normal_tile_map.texture:
            normal_tile_map_name: str = self.textures.normal_tile_map.texture.texture_name
            edm_render_node.setNormalTiledMap(normal_tile_map_name)

        if self.textures.rmo_tile_map.texture:
            rmo_tile_map_name: str = self.textures.rmo_tile_map.texture.texture_name
            edm_render_node.setAormsTiledMap(rmo_tile_map_name)

        if self.textures.decal_map.texture:
            base_uv_map_name: str = self.textures.decal_map.texture.get_uv_map(mesh_storage.uv_active)
            edm_render_node.setRegularUV(mesh_storage.get_uv(base_uv_map_name, self.bpy_material.name))

            base_map_name: str = self.textures.decal_map.texture.texture_name
            edm_render_node.setBaseMap(base_map_name)

        if self.textures.decal_rmo.texture:
            rmo_map_name: str = self.textures.decal_rmo.texture.texture_name
            edm_render_node.setAormsMap(rmo_map_name)

        if self.textures.damage_color.texture:
            damage_map_name: str = self.textures.damage_color.texture.texture_name
            edm_render_node.setDamageMap(damage_map_name)

        if self.textures.damage_mask.texture:
            damage_mask_name: str = self.textures.damage_mask.texture.texture_name
            edm_render_node.setDamageMaskRGBA(damage_mask_name)

        if self.textures.rain_mask.texture:
            rain_mask_name: str = self.textures.rain_mask.texture.texture_name
            edm_render_node.setRainMask(rain_mask_name)

        edm_props = get_edm_props(object)
        edm_render_node.setArgument(edm_props.DAMAGE_ARG)
        if mesh_storage.has_dmg_group:
            edm_render_node.setPerVertexArguments(mesh_storage.damage_arguments)

        return edm_render_node

    @classmethod
    def process_links(cls, old_links, old_version, group_node_type_name):
        new_links: List[SLink] = []
        
        if old_version < 7:
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
                        link.to_socket = NodeSocketInDeckEnum.DAMAGE_NORMAL
                new_links.append(link)
        else:
            for link in old_links:
                new_links.append(link)

        return new_links

    @classmethod    
    def restore_defaults(cls, old_sockest, new_node_group, drop_down_values, old_version, material_name):
        version_new: int = get_version(new_node_group.node_tree)
        if old_version >= 1:
            
            ## copy old drop-down values to new created node_group
            for key, val in drop_down_values.items():
                setattr(new_node_group, key, val)
                
            for new_socket in new_node_group.inputs:
                old_socket_wrp: SInput = get_first_socket_by_name(old_sockest, new_socket.name)
                if not old_socket_wrp:
                    continue
                if new_socket.name == NodeSocketCommonEnum.VERSION:
                    new_socket.default_value = version_new
                    continue
                if old_socket_wrp.instance_value and new_socket.name not in (NodeSocketInDeckEnum.TRANSPARENCY): 
                    new_socket.default_value = old_socket_wrp.instance_value
