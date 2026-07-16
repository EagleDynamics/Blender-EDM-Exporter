
import bpy

from enums import ObjectTypeEnum, EDMPropsSpecialTypeStr
from pyedm_platform_selector import pyedm
from objects_custom_props import get_edm_props

def is_transparent_pivot(obj: bpy.types.Object) -> bool:
    edm_props = get_edm_props(obj)
    if obj.type == ObjectTypeEnum.EMPTY and edm_props.SPECIAL_TYPE == EDMPropsSpecialTypeStr.TRANSPARENT_PIVOT:
        return True
    return False

def export_transparent_pivot(obj: bpy.types.Object, edm_render_node):
    if edm_render_node and isinstance(edm_render_node, pyedm.PBRNode):
        edm_render_node.addTransparentPivot(obj.matrix_local.decompose()[0])