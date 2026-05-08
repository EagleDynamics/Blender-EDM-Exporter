import bpy
from bpy.types import Object
from pyedm_platform_selector import pyedm
from logger import log
from math import radians
from mathutils import Matrix
from objects_custom_props import get_edm_props
from enums import ObjectTypeEnum
from utils import has_object
from enums import EDMPropsSpecialTypeStr

def is_connector(object: Object) -> bool:
    edm_props = get_edm_props(object)
    if object.type == ObjectTypeEnum.EMPTY and edm_props.SPECIAL_TYPE in ('CONNECTOR'):
        return True

    return False


def export_connector(object: Object, transform_node: pyedm.Node):
    edm_connector = pyedm.Connector(object.name)

    connector_transform = pyedm.Transform(
        "Connector Transform", Matrix.Rotation(radians(90.0), 4, "X")
    )
    transform_node.addChild(connector_transform)

    edm_connector.setControlNode(connector_transform)

    edm_props = get_edm_props(object)
    sp_scope = {}
    connector_ext: str = edm_props.CONNECTOR_EXT
    try:
        exec(connector_ext, {}, sp_scope)
    except Exception as e:
        log.error(f"Connector has {object.name} invalid format: {edm_props}. {e}")
        return

    for ext_name, ext_value in sp_scope.items():
        if type(ext_value) == float or type(ext_value) == int:
            edm_connector.setPropertyFloat(ext_name, float(ext_value))
        if type(ext_value) == str:
            edm_connector.setPropertyString(ext_name, ext_value)

    return edm_connector

class ConnectorChildPanel(bpy.types.Panel):
    bl_label = "Connector type Properties"
    bl_idname = "OBJECT_PT_connector_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_edm_data"

    @classmethod
    def poll(cls, context):
        if not has_object(context):
            return

        object: Object = context.object
        props = get_edm_props(object)

        result = props.SPECIAL_TYPE in (EDMPropsSpecialTypeStr.CONNECTOR) and not(object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP)
        return result

    def draw(self, context):
        if not has_object(context):
            return

        layout = self.layout
        object: Object = context.object
        props = get_edm_props(object)

        box = layout.box()
        row = box.row()
        row.prop(props, "CONNECTOR_EXT")

        return
