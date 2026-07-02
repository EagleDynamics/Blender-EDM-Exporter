import platform
import bpy
from version_specific import BLENDER_40, BLENDER_51

BLENDER_RELEASE = bpy.app.version[0] * 10 + bpy.app.version[1]

os_name = platform.system()
if os_name == 'Windows':
    if BLENDER_RELEASE >= BLENDER_51:
        import pyedm_313 as pyedm
        native_bindings = True
    elif BLENDER_RELEASE >= BLENDER_40:
        import pyedm_311 as pyedm
        native_bindings = True
    else:
        import pyedm_plug as pyedm
        native_bindings = False
else:
    import pyedm_plug as pyedm
    native_bindings = False
