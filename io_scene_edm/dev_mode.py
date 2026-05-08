from bpy.types import PropertyGroup, Scene
from bpy.props import BoolProperty

from pyedm_platform_selector import pyedm

class EDMDevModePropsGroupDummy:
    def __init__(self) -> None:
        self.EXPORT_CUR_ARG_ONLY = False

        self.OPTIMIZE_TRANFORMATIONS = True
        self.MERGE_PROPETIES_SET = True
        self.OPTIMIZE_TEXTURE_CHANNELS = True
        self.MERGE_NODES = True
        self.EXTREMLY_OPTIMIZE_MESHES = True
        self.OPTIMIZE_VERTEX_CACHE = True

class EDMDevModePropsGroup(PropertyGroup):
    bl_idname = "edm.EDMDevModePropsGroup"

    EXPORT_CUR_ARG_ONLY : BoolProperty(
        name = "Export only one arg",
        default = False,
		options = {'SKIP_SAVE'},
    )

    OPTIMIZE_TRANFORMATIONS : BoolProperty(
        name = "optimizeTransformations",
        default = True,
		options = {'SKIP_SAVE'},
    )

    MERGE_PROPETIES_SET : BoolProperty(
        name = "mergePopertiesSets",
        default = True,
		options = {'SKIP_SAVE'},
    )

    OPTIMIZE_TEXTURE_CHANNELS : BoolProperty(
        name = "optimizeTextureChannels",
        default = True,
		options = {'SKIP_SAVE'},
    )

    MERGE_NODES : BoolProperty(
        name = "mergeNodes",
        default = True,
		options = {'SKIP_SAVE'},
    )

    EXTREMLY_OPTIMIZE_MESHES : BoolProperty(
        name = "extremlyOptimizeMeshes",
        default = True,
		options = {'SKIP_SAVE'},
    )

    OPTIMIZE_VERTEX_CACHE : BoolProperty(
        name = "optimizeVertexCache",
        default = True,
		options = {'SKIP_SAVE'},
    )

def get_dev_mode_classes():
    if pyedm.dev_mode():
        return [EDMDevModePropsGroup]
    return []
    
def get_dev_mode_props(o: Scene)->EDMDevModePropsGroup:
    if pyedm.dev_mode():
        return o.EDMDevModeProps    
    return EDMDevModePropsGroupDummy()