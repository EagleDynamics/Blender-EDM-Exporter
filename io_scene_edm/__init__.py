import sys
import bpy
import os
import re
import traceback

from typing import List, Dict, Tuple, Set

sys.path.append(bpy.utils.user_resource(resource_type='SCRIPTS', path="addons") + '\\' + __name__)

from pyedm_platform_selector import pyedm, native_bindings

from bpy.types import Operator, Panel, Context, AddonPreferences, Object, UILayout, Light
from bpy.props import StringProperty, BoolProperty, PointerProperty
from bpy_extras.io_utils import ExportHelper

from pathlib import Path
import shlex
import subprocess

from . import collection_walker
from objects_custom_props import get_edm_props, EDM_PropsEnumValues, EDMPropsGroup
from custom_sockets import get_custom_sockets_classes
from . import custom_shader_group as custom_sg

from objects_custom_props import get_objects_custom_props_classes

from edm_exception import EdmFatalException
from logger import log
from enums import ObjectTypeEnum, EDMPropsSpecialTypeStr, LampTypeEnum
from edm_materials import get_material_classes, NODE_MT_EDM_Menu_add, NODE_MT_EDM_Dev_Menu_add
from arg_panel import get_arg_panel_classes, EDM_PT_set_argument, EDM_PT_mute_animations, EDM_PT_unmute_animations, EDM_PT_reset, EDMArgPropsGroup, get_arg_panel_props
from materials.material_tools import get_material_tool_classes, EDM_PT_import_materials, EDM_PT_export_materials, check_materials_validity
from materials.materials import check_if_referenced_file, build_material_descriptions
from serializer_tools import MatDesc
from dev_mode import get_dev_mode_classes, EDMDevModePropsGroup, get_dev_mode_props
from export_connectors import ConnectorChildPanel
from materials.material_fake_common import FakeLightChildPanel
from export_lights import LightChildPanel
from . import utils

# Unfortunately, parser of bl_info doesn't support variables as values.
bl_info = {
    'name': 'EDM 10.0 format', # 'EDM 10.0 format'
    'author': 'Eagle Dynamics (c) 2024 - present',
    "version": (1, 0, "262186"),
    'blender': (3, 5, 0),
    'location': 'File > Export / Shader Editor > Add > EDM',
    'description': 'Export as EDM and compatible shading materials',
    'warning': '',
    'doc_url': "",
    'support': 'OFFICIAL',
    'category': 'Export',
}

def has_scene(context):
    if not context.scene:
        return False

    return True

def is_exists_on_disk():
    if len(bpy.data.filepath) > 0:
        return True
    return False

def get_default_save_path():    
    file_dir: str = os.path.dirname(bpy.data.filepath)
    file_name = Path(bpy.data.filepath).stem
    return os.path.join(file_dir, file_name + '.edm')

def get_current_export_path(context):
    if hasattr(context.scene, "edm_export_path") and context.scene.edm_export_path:
        return context.scene.edm_export_path
    elif bpy.data.filepath and len(bpy.data.filepath) > 0:
        return get_default_save_path()
    return ""

class EDM_OT_reset_export_path(Operator):
    bl_idname = "edm.reset_export_path"
    bl_label = "Reset Export Path"
    bl_description = "Reset export path to default"
    
    def execute(self, context):
        if not is_exists_on_disk():
            self.report({'ERROR'}, "Please save the .blend file before resetting export path")
            return {'CANCELLED'}
            
        context.scene.edm_export_path = get_default_save_path()
        return {'FINISHED'}
        
class EDM_OT_set_export_path(Operator):
    bl_idname = "edm.set_export_path"
    bl_label = "Set Export Path"
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        filepath = self.filepath
        
        if not os.path.basename(filepath):
            self.report({'ERROR'}, "Please enter a file name")
            return {'CANCELLED'}
        
        filename, ext = os.path.splitext(filepath)
        if not ext:
            filepath = filename + '.edm'
        elif ext.lower() != '.edm':
            filepath = filepath + '.edm'
        
        context.scene.edm_export_path = filepath
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class WM_OT_version_error_dialog(Operator):
    bl_idname = "wm.version_error_dialog"
    bl_label = "Blender version error"
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def draw(self, context):
        layout = self.layout
        layout.alert = True
        layout.label(text="Blender versions prior to 4.0 are not supported.", icon='CANCEL')
        layout.separator()
        layout.label(text=f"Your version: {bpy.app.version_string}")
        layout.separator()
        layout.label(text="EDM plugin is disabled")
    
    def cancel(self, context):
        pass

def show_version_error():
    bpy.ops.wm.version_error_dialog('INVOKE_DEFAULT')
    print(f"ERROR: EDM plugin requires Blender 4.0+. Current: {bpy.app.version_string}")
    return None 
    
class EDMDataPanel(Panel):
    bl_label = "Object Properties"
    bl_idname = "OBJECT_PT_edm_data"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "EDM Export"

    @classmethod
    def poll(cls, context):
        if context.scene:
            return True
        
        if not context.object:
            return False
        
        return True
    
    def draw_scene_related(self, layout: UILayout, context: Context):       

        row = layout.row(align=True)
        row.operator(EDM_PT_fast_export.bl_idname)
        
        rollout_icon = 'DOWNARROW_HLT' if context.scene.edm_export_rollout else 'RIGHTARROW'
        row.prop(context.scene, "edm_export_rollout", text="", icon=rollout_icon, emboss=False)

        if context.scene.edm_export_rollout:
            row = layout.row(align=True)
            row.prop(context.scene, "edm_export_path", text="Path")
            row.operator("edm.set_export_path", text="", icon='FILE_FOLDER')
            row.operator("edm.reset_export_path", text="", icon='LOOP_BACK')

        layout.split()

        props = get_arg_panel_props(context.scene)

        row = layout.row()
        row.prop(props, "CURRENT_ARG")
        row.operator(EDM_PT_set_argument.bl_idname)
        row = layout.row()
        row.operator(EDM_PT_mute_animations.bl_idname)
        row.operator(EDM_PT_unmute_animations.bl_idname)
        row = layout.row()
        row.operator(EDM_PT_reset.bl_idname)

        layout.split()

        if not check_if_referenced_file(bpy.context.blend_data.filepath):
            row = layout.row()
            row.operator(EDM_PT_import_materials.bl_idname)
        else:
            row = layout.row()
            row.operator(EDM_PT_export_materials.bl_idname)

        layout.split()

        if pyedm.dev_mode():
            dev_props = get_dev_mode_props(context.scene)
            row = layout.row()
            row.prop(dev_props, "EXPORT_CUR_ARG_ONLY")

            row = layout.row()
            row.prop(dev_props, "OPTIMIZE_TRANFORMATIONS")

            row = layout.row()
            row.prop(dev_props, "MERGE_PROPETIES_SET")

            row = layout.row()
            row.prop(dev_props, "OPTIMIZE_TEXTURE_CHANNELS")

            row = layout.row()
            row.prop(dev_props, "MERGE_NODES")

            row = layout.row()
            row.prop(dev_props, "EXTREMLY_OPTIMIZE_MESHES")

            row = layout.row()
            row.prop(dev_props, "OPTIMIZE_VERTEX_CACHE")

    def draw_object_related(self, layout: UILayout, context: Context):
        if not utils.has_object(context):
            return
        
        object: Object = context.object
        props = get_edm_props(object)

        row = layout.row()
        row.prop(object, "VISIBLE", event=True)

        if not(object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP):
            row = layout.row()
            row.prop(props, "SPECIAL_TYPE")

        return
        
    def draw(self, context):
        layout = self.layout

        self.draw_scene_related(layout, context)
        layout.split()
        self.draw_object_related(layout, context)

class UnknownChildPanel(bpy.types.Panel):
    bl_label = "Unknown type Properties"
    bl_idname = "OBJECT_PT_unknown_child_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_edm_data"

    @classmethod
    def poll(cls, context):
        if not utils.has_object(context):
            return

        object: Object = context.object
        props = get_edm_props(object)

        result = props.SPECIAL_TYPE in (EDMPropsSpecialTypeStr.UNKNOWN_TYPE) and not(object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP)
        return result

    def draw(self, context):
        if not utils.has_object(context):
            return

        layout = self.layout
        object: Object = context.object
        props = get_edm_props(object)

        if object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP:
            box = layout.box()
            row = box.row()
            row.label(text='Light Arguments')
           
            row = box.row()
            row.prop(props, "LIGHT_COLOR_ARG")
            row = box.row()
            row.prop(props, "LIGHT_POWER_ARG")
            row = box.row()
            row.prop(props, "LIGHT_DISTANCE_ARG")

            row = box.row()
            row.label(text='Light Params')            
            row = box.row()
            row.prop(props, "LIGHT_SOFTNESS")
            blender_lamp: Light = object.data
            if blender_lamp.type == LampTypeEnum.SPOT:
                row = box.row()
                row.prop(props, "LIGHT_SPOT_SHAPE_ARG")

            row = box.row()
            row.label(text='Light Volume Params')            
            row = box.row()
            row.prop(props, "LIGHT_VOLUME_RADIUS_FACTOR")
            row = box.row()
            row.prop(props, "LIGHT_VOLUME_DENSITY_FACTOR")
            row = box.row()
            row.prop(props, "LIGHT_VOLUME_NEAR_DISTANCE")
            row = box.row()
            row.prop(props, "LIGHT_VOLUME_TYPE")

        else:
            row = layout.row()
            row.prop(props, "TWO_SIDED")

            row = layout.row()
            row.prop(props, "DAMAGE_ARG")

            row = layout.row()
            row.prop(props, "COLOR_ARG")

            row = layout.row()
            row.prop(props, "EMISSIVE_ARG")

            row = layout.row()
            row.prop(props, "EMISSIVE_COLOR_ARG")

            row = layout.row()
            row.prop(props, "OPACITY_VALUE_ARG")

            row = layout.row()
            row.prop(props, "AO_ARG")

class UserBoxChildPanel(bpy.types.Panel):
    bl_label = "UserBox type Properties"
    bl_idname = "OBJECT_PT_user_box_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_edm_data"

    @classmethod
    def poll(cls, context):
        # don't show the panel, until there is data to display. We leave the class so we don’t have to write it again later
        return False
        if not utils.has_object(context):
            return

        object: Object = context.object
        props = get_edm_props(object)

        result = props.SPECIAL_TYPE in (EDMPropsSpecialTypeStr.USER_BOX) and not(object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP)
        return result

    def draw(self, context):
        if not utils.has_object(context):
            return

class BoundingBoxChildPanel(bpy.types.Panel):
    bl_label = "BoundingBox type Properties"
    bl_idname = "OBJECT_PT_bounding_box_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_edm_data"

    @classmethod
    def poll(cls, context):
        # don't show the panel, until there is data to display. We leave the class so we don’t have to write it again later
        return False
        if not utils.has_object(context):
            return

        object: Object = context.object
        props = get_edm_props(object)

        result = props.SPECIAL_TYPE in (EDMPropsSpecialTypeStr.BOUNDING_BOX) and not(object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP)
        return result

    def draw(self, context):
        if not utils.has_object(context):
            return

        layout = self.layout
        object: Object = context.object
        props = get_edm_props(object)

class CollisionLineChildPanel(bpy.types.Panel):
    bl_label = "Collision line type Properties"
    bl_idname = "OBJECT_PT_collision_line_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_edm_data"

    @classmethod
    def poll(cls, context):
        # don't show the panel, until there is data to display. We leave the class so we don’t have to write it again later
        return False
        if not utils.has_object(context):
            return

        object: Object = context.object
        props = get_edm_props(object)

        result = props.SPECIAL_TYPE in (EDMPropsSpecialTypeStr.COLLISION_LINE) and not(object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP)
        return result

    def draw(self, context):
        if not utils.has_object(context):
            return

        layout = self.layout
        object: Object = context.object
        props = get_edm_props(object)

class CollisionShellChildPanel(bpy.types.Panel):
    bl_label = "Collision shell type Properties"
    bl_idname = "OBJECT_PT_collision_shell_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_edm_data"

    @classmethod
    def poll(cls, context):
        # don't show the panel, until there is data to display. We leave the class so we don’t have to write it again later
        return False
        if not utils.has_object(context):
            return

        object: Object = context.object
        props = get_edm_props(object)

        result = props.SPECIAL_TYPE in (EDMPropsSpecialTypeStr.COLLISION_SHELL) and not(object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP)
        return result

    def draw(self, context):
        if not utils.has_object(context):
            return

class LightBoxChildPanel(bpy.types.Panel):
    bl_label = "LightBox type Properties"
    bl_idname = "OBJECT_PT_lightbox_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_edm_data"

    @classmethod
    def poll(cls, context):
        # don't show the panel, until there is data to display. We leave the class so we don’t have to write it again later
        return False
        if not utils.has_object(context):
            return

        object: Object = context.object
        props = get_edm_props(object)

        result = props.SPECIAL_TYPE in (EDMPropsSpecialTypeStr.LIGHT_BOX) and not(object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP)
        return result

    def draw(self, context):
        if not utils.has_object(context):
            return

        layout = self.layout
        object: Object = context.object
        props = get_edm_props(object)

class NumberTypeChildPanel(bpy.types.Panel):
    bl_label = "Number type Properties"
    bl_idname = "OBJECT_PT_number_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_edm_data"

    @classmethod
    def poll(cls, context):
        if not utils.has_object(context):
            return

        object: Object = context.object
        props = get_edm_props(object)

        result = props.SPECIAL_TYPE in (EDMPropsSpecialTypeStr.NUMBER_TYPE) and not(object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP)
        return result

    def draw(self, context):
        if not utils.has_object(context):
            return

        layout = self.layout
        object: Object = context.object
        props = get_edm_props(object)

        box = layout.box()
        
        row = box.row()
        row.prop(props, "DAMAGE_ARG")

        row = box.row()
        row.prop(props, "NUMBER_UV_X_ARG")
        row.prop(props, "NUMBER_UV_X_SCALE")

        row = box.row()
        row.prop(props, "NUMBER_UV_Y_ARG")
        row.prop(props, "NUMBER_UV_Y_SCALE")


def add_node_button(self, context):
    self.layout.menu(NODE_MT_EDM_Menu_add.__name__, text = "EDM Materials")
    is_dev_env: bool = utils.get_is_dev_env()
    is_reference_file: bool = check_if_referenced_file(bpy.context.blend_data.filepath)
    if is_dev_env or is_reference_file:
        self.layout.menu(NODE_MT_EDM_Dev_Menu_add.__name__, text = "Dev EDM Materials")

class EDMAddonParams(AddonPreferences):
    bl_idname = __name__

    run_viewer_flag: BoolProperty(
        name = "Run viewer after model export",
        default = False,
    )

    executable_path: StringProperty(
        name="Executable path",
        subtype='FILE_PATH',
        default='H:\\lockon\\LockOnExe\\bin\\x86_64\\vc143.debug-ad-mt\\ModelViewer2.exe'
    )

    arguments: StringProperty(
        name="Arguments",
        default="--reload --single s $FILE$"
    )
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="This is a preferences view for our add-on")
        layout.prop(self, "run_viewer_flag")
        layout.prop(self, "arguments")
        layout.prop(self, "executable_path")

        addon_path = os.path.dirname(__file__)
        learning_demo_path = os.path.join(addon_path, "Learning_Demo")
        if os.path.exists(learning_demo_path):
            row = layout.row()
            op = row.operator("wm.path_open", text="Open Learning_Demo")
            op.filepath = learning_demo_path
        else:
            layout.label(text="Could not find 'Learning_Demo' path")

def run_edm_export(file_path: str, context: Context, operator: Operator, run_model_viewer: bool = True):
    abs_file_path: str = os.path.abspath(file_path)    
    try:
        if not native_bindings:
            raise EdmFatalException(f"\nError: couldn't proceed edm export because it's python dummy plugin, not native.")
                
        if not check_if_referenced_file(bpy.context.blend_data.filepath):
            check_materials_validity()
        collection_walker._write(context, abs_file_path)

        for i in log.warnings:
            operator.report({"WARNING"}, i)

        if log.errors:
            for i in log.errors:
                operator.report({"ERROR"}, i)
            log.errors = []
            return {'CANCELLED'}
            
        operator.report({"INFO"}, f'Model successfully exported to {abs_file_path}.')
    except EdmFatalException as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        res = ''.join(traceback.format_tb(exc_traceback, limit=1))
        res += ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback, limit=2))
        log.error(str(e))
        log.errors = []
        operator.report({"ERROR"}, str(e))
        return {'CANCELLED'}

    my_addon_params: EDMAddonParams = context.preferences.addons[__name__].preferences
    run_viewer_flag: bool = my_addon_params and my_addon_params.run_viewer_flag and run_model_viewer
    if run_viewer_flag:
        args = shlex.split(my_addon_params.arguments)
        args.insert(0, my_addon_params.executable_path)
        if '$FILE$' in args:
            i = args.index('$FILE$')
            args[i] = file_path
        DETACHED_PROCESS = 0x00000008
        try:
            subprocess.Popen(args, close_fds = True, creationflags = DETACHED_PROCESS)
        except:
            pass
    return {'FINISHED'}

class EDM_PT_export(Operator, ExportHelper):
    bl_idname = "edm.export"
    bl_label = "export to EDM"
    bl_description = "Export edm"
    filename_ext = ".edm"
    filter_glob: StringProperty (
        default = "*.edm",
        options = {'HIDDEN'},
        maxlen = 255
    )

    def execute(self, context):
        return run_edm_export(self.filepath, context, self)

class EDM_PT_fast_export(Operator):
    bl_idname = "edm.fast_export" 
    bl_label = "Fast EDM export"
    
    @classmethod
    def description(cls, context, properties):
        file_path = get_current_export_path(context)
        if len(file_path) <= 0:
            file_path = "No export path set"
        
        return f"Export path: {file_path}"
    
    def execute(self, context):
        current_export_path = get_current_export_path(context)
        if len(current_export_path) <= 0:
            self.report({'ERROR'}, "Please save the .blend file before exporting or set path in settings")
            return {'CANCELLED'}

        return run_edm_export(current_export_path, context, self)
    
class EDM_PT_fast_export_dummy(Operator):
    bl_idname = "edm.fast_export_dummy" 
    bl_label = "Fast EDM export dummy"
    bl_description = "Fast export to edm without calling ModelView.exe after"

    def execute(self, context):
        is_file_name_available: bool = len(bpy.data.filepath) > 0
        file_dir: str = os.path.dirname(bpy.data.filepath) if is_file_name_available else os.path.dirname(os.path.realpath(__file__))
        file_name = Path(bpy.data.filepath).stem if is_file_name_available else 'test'
        file_path: str = os.path.join(file_dir, file_name + '.edm')
        return run_edm_export(file_path, context, self, False)

def menu_func_export(self, context):
    self.layout.operator(EDM_PT_export.bl_idname, text="Eagle Dynamics Model (.edm)")


def collect_classes():
    classes = get_material_classes()
    classes += get_material_tool_classes()
    classes += get_arg_panel_classes()
    classes += get_custom_sockets_classes()
    classes += get_objects_custom_props_classes()
    classes += custom_sg.get_custom_shader_group_classes()
    classes += get_dev_mode_classes()
    classes += (
        EDMDataPanel,
        EDM_PT_fast_export,
        EDM_PT_fast_export_dummy,
        EDMAddonParams,
        LightChildPanel,
        UnknownChildPanel,
        UserBoxChildPanel,
        BoundingBoxChildPanel,
        CollisionLineChildPanel,
        CollisionShellChildPanel,
        ConnectorChildPanel,
        FakeLightChildPanel,
        LightBoxChildPanel,
        NumberTypeChildPanel,
        EDM_PT_export,
    )
    return classes


def visibility_get_func(self):
    if self.display_type == 'WIRE':
        return False
    return True

def visibility_set_func(self, val):
    if val == True:
        self.display_type = 'TEXTURED'
    else:
        self.display_type = 'WIRE'

def create_return_items(enum_name: str, mat_name: str, it: Dict[custom_sg.MaterialNameType, Dict[custom_sg.SocketNameType, List[Tuple[str, str, str, int]]]]):
    def retrive_items(self, context):
        return it[mat_name][enum_name]
    return retrive_items

def get_edm_export_path(self):
    if self.get("edm_export_path", ""):
        return self["edm_export_path"]
    elif bpy.data.filepath and len(bpy.data.filepath) > 0:
        return get_default_save_path()
    return ""

def set_edm_export_path(self, value):
    self["edm_export_path"] = value

def register():
    pyedm.init()
    
    if bpy.app.version < (4, 0, 0):
        bpy.utils.register_class(WM_OT_version_error_dialog)
        bpy.app.timers.register(show_version_error, first_interval=0.1)   
        return

    material_desc: Dict[str, MatDesc] = build_material_descriptions()
    items: Dict[custom_sg.MaterialNameType, Dict[custom_sg.SocketNameType, List[Tuple[str, str, str, int]]]] = custom_sg.get_enum_items(material_desc)
    names: Dict[custom_sg.MaterialNameType, Dict[str, str]] = custom_sg.get_enum_names(material_desc)
    names_enum: List[Tuple[custom_sg.SocketType, custom_sg.MaterialNameType, custom_sg.SocketNameType, int]] = custom_sg.get_enum_names_map(names)

    deffered_names_enum = bpy.props.EnumProperty (
        name        = 'enum_names',
        items       = names_enum
    )
    setattr(bpy.types.ShaderNodeCustomGroup, 'enum_names', deffered_names_enum)
    setattr(bpy.types.ShaderNodeGroup, 'enum_names', deffered_names_enum)

    for mat_name, enum_dict in items.items():
        for enum_name, enum_values in enum_dict.items():
            deffered_enum = bpy.props.EnumProperty (
                name        = enum_name,
                items       = create_return_items(enum_name, mat_name, items)
            )
            setattr(bpy.types.ShaderNodeCustomGroup, enum_name, deffered_enum)
            setattr(bpy.types.ShaderNodeGroup, enum_name, deffered_enum)


    classes = collect_classes()
    for cls in classes:
        utils.register_bpy_class(cls)

    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.NODE_MT_add.append(add_node_button)
    
    bpy.types.Scene.EDMArgProps = PointerProperty(type = EDMArgPropsGroup)
    bpy.types.Object.EDMProps = PointerProperty(type = EDMPropsGroup)
    bpy.types.Scene.EDMEnumItems = PointerProperty(type = EDM_PropsEnumValues)
    
    if pyedm.dev_mode():
        bpy.types.Scene.EDMDevModeProps = PointerProperty(type = EDMDevModePropsGroup)
    
    # Have set this property directly into object as we need acces to parent object in callbacks.
    bpy.types.Object.VISIBLE = BoolProperty(
        name = "visibility",
        default = True,
        set = visibility_set_func,
        get = visibility_get_func,
    )

    bpy.types.Scene.edm_export_path = bpy.props.StringProperty(
        name="EDM Export Path",
        description="Path for EDM export",
        default="",
        get=get_edm_export_path,
        set=set_edm_export_path
    )
    bpy.types.Scene.edm_export_rollout = BoolProperty(
        name="Show Export Path",
        default=False
    )
    bpy.utils.register_class(EDM_OT_reset_export_path)
    bpy.utils.register_class(EDM_OT_set_export_path)

    print("EDM Addon was registered")

def unregister():        
    pyedm.deinit()

    if bpy.app.version < (4, 0, 0):
        bpy.utils.unregister_class(WM_OT_version_error_dialog)
        return
    
    del bpy.types.Scene.EDMArgProps
    del bpy.types.Object.EDMProps
    del bpy.types.Scene.EDMEnumItems
    del bpy.types.Scene.edm_export_path
    del bpy.types.Scene.edm_export_rollout

    if pyedm.dev_mode():
        del bpy.types.Scene.EDMDevModeProps

    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.NODE_MT_add.remove(add_node_button)

    classes = collect_classes()
    for cls in reversed(classes):
        utils.unregister_bpy_class(cls)

    bpy.utils.unregister_class(EDM_OT_reset_export_path)
    bpy.utils.unregister_class(EDM_OT_set_export_path)

    print("EDM Addon was unregistered")

if __name__ == "__main__":
       
    register()
