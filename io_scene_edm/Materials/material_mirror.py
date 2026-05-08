from bpy.types import (
    Material,
    ShaderNodeGroup,
)

from mesh_storage import MeshStorage
from pyedm_platform_selector import pyedm
from objects_custom_props import get_edm_props
from node_tree_tools import get_version
from materials.material_interface import IMaterial
from materials.material_wrap import (
    TextureDesk,
    ValueDesk,
    g_missing_texture_name
)
from enums import (
    BpyNodeSocketType,
    NodeSocketCommonEnum,
    NodeSocketInMirrorEnum,
)

MIRROR_MATERIAL_NAME = 'EDM_Mirror_Material'

## Mirror material
class MirrorMaterial(IMaterial):
    name = MIRROR_MATERIAL_NAME
    description_file_name = f'data/{MIRROR_MATERIAL_NAME}.pickle'
    node_group_name = 'EdmMirrorShaderNodeType'

    class Textures:
        def __init__(self, node_group: ShaderNodeGroup) -> None:
            self.albedo         = TextureDesk(node_group, NodeSocketInMirrorEnum.BASE_COLOR, BpyNodeSocketType.COLOR)
            self.normal         = TextureDesk(node_group, NodeSocketInMirrorEnum.NORMAL, BpyNodeSocketType.COLOR)

    class Values:
        def __init__(self, node_group: ShaderNodeGroup) -> None:
            self.version        = ValueDesk(node_group, NodeSocketCommonEnum.VERSION, BpyNodeSocketType.INTEGER, -1)

    def __init__(self, bpy_material: Material, node_group: ShaderNodeGroup):
        self.bpy_material = bpy_material
        self.node_group = node_group
        self.is_valid = not self.node_group == None
        
        self.textures = MirrorMaterial.Textures(self.node_group)
        self.values = MirrorMaterial.Values(self.node_group)

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

    def build_blocks(self, object, mesh_storage: MeshStorage):       
        edm_render_node = pyedm.MirrorNode(object.name, self.bpy_material.name)        
        edm_render_node.setIndices(mesh_storage.indices)
        edm_render_node.setPositions(mesh_storage.positions)
        edm_render_node.setNormals(mesh_storage.normals)     

        uv = mesh_storage.get_uv(mesh_storage.uv_active, self.bpy_material.name)
        edm_render_node.setTextureCoordinates(uv)
        edm_render_node.setTexture("mirror_texture")
        
        return edm_render_node
    
    @classmethod
    def process_links(cls, old_links, old_version, group_node_type_name):
        return old_links
    
    @classmethod 
    def restore_defaults(cls, old_sockest, new_node_group, drop_down_values, old_version, material_name):
        version_new: int = get_version(new_node_group.node_tree)

        if old_version == 0:
            return
        
        for new_socket in new_node_group.inputs:
            if new_socket.name == NodeSocketCommonEnum.VERSION:
                new_socket.default_value = version_new
                continue