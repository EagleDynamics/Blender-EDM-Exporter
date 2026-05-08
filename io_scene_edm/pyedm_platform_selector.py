import platform
import bpy

BLENDER_40 = 40
BLENDER_41 = 41
BLENDER_RELEASE = bpy.app.version[0] * 10 + bpy.app.version[1]

os_name = platform.system()
if os_name == 'Windows' and BLENDER_RELEASE >= BLENDER_40:
    import pyedm_311 as pyedm
    native_bindings = True
else:
    import pyedm_plug as pyedm
    native_bindings = False
