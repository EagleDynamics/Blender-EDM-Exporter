"""
This file contains methods for creating render node that is used only in cases when we want to cover some object.
Created render node is RenderNode which:
        1) has only one block - BT_Base (with black color);
        2) with '_purposeType' set to 'EMeshPurpose::MP_WaterMask'.
"""

from typing import List

import bpy

from mesh_builder import buld_mesh
from pyedm_platform_selector import pyedm
from objects_custom_props import get_edm_props
from enums import ObjectTypeEnum, EDMPropsSpecialTypeStr

def is_water_mask(obj: bpy.types.Object) -> bool:
    edm_props = get_edm_props(obj)
    if obj.type == ObjectTypeEnum.MESH and edm_props.SPECIAL_TYPE == EDMPropsSpecialTypeStr.WATER_MASK:
        return True
    return False

def export_water_mask(obj: bpy.types.Object, control_node: pyedm.Node):
    _color_in_viewer = (0., 1., 0.)
    _material_name = 'water_mask_material'

    nTriangles = 0
    mesh_storages = buld_mesh(obj, None)

    edm_render_nodes: List[pyedm.PBRNode] = []
    for mesh_storage in mesh_storages:
        nTriangles += mesh_storage.nTriangles

        ## create BT_Base block
        edm_base_bock = pyedm.ColorBaseBlock()
        edm_base_bock.setColor(pyedm.PropertyFloat3(_color_in_viewer))
        edm_base_bock.setPositions(mesh_storage.positions)
        edm_base_bock.setNormals(mesh_storage.normals)
        
        ## create render node
        edm_render_node = pyedm.PBRNode(obj.name, _material_name)
        edm_render_node.setIndices(mesh_storage.indices)
        edm_render_node.addBlock(edm_base_bock)
        edm_render_node.setControlNode(control_node)
        edm_render_node.setPurposeWaterMask()

        ## add render node to output list
        edm_render_nodes.append(edm_render_node)
    
    return (nTriangles, edm_render_nodes)