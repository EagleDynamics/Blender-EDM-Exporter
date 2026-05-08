from typing import Dict, Union

from bpy.types import Material

from materials.materials import MATERIALS, get_edm_node_group
from materials.material_interface import IMaterial

class MaterialCache:
    def __init__(self) -> None:
        self.materials: Dict[Material, IMaterial] = {}

    def get(self, material: Material) -> IMaterial:
        if material in self.materials.keys():
            return self.materials[material]
        
        material_instance: IMaterial = get_material_wrap(material)
        self.materials[material] = material_instance

        return material_instance
    
def get_material_wrap(bpy_material: Union[Material | None]) -> Union[IMaterial, None]:
    if not bpy_material:
        return None
    
    use_nodes: bool = bpy_material.use_nodes and bool(bpy_material.node_tree)
    if not use_nodes:
        return None
    
    for bpy_node in bpy_material.node_tree.nodes:
        if not hasattr(bpy_node, 'node_tree'):
            continue

        mat: IMaterial = MATERIALS.get(bpy_node.node_tree.name, None)
        if mat:
            node_group = get_edm_node_group(bpy_material, mat.name)
            mat_instance = mat(bpy_material, node_group)
            return mat_instance