import bpy

from bpy.types import Operator, PropertyGroup
from bpy.props import IntProperty, PointerProperty

import utils
from version_specific import get_fcurves, get_action_groups

def mute_action(action, mute):
    for g in get_action_groups(action):
        g.mute = mute

    fcurves = get_fcurves(action)
    for fcu in fcurves:
        fcu.mute = mute

def mute_anim(objects, mute):
    for o in objects:
        if not o.visible_get():
            continue

        ad = o.animation_data
        if not ad or not ad.action:
            continue

        for g in get_action_groups(ad.action):
            g.mute = mute

        fcurves = get_fcurves(ad.action)
        for fcu in fcurves:
            fcu.mute = mute

def query_objects(objects, filter):
    for o in objects:
        if not o.visible_get():
            continue

        filter(o)


class EDMArgPropsGroup(PropertyGroup):
    bl_idname = "edm.EDMArgPropsGroup"
    CURRENT_ARG : IntProperty(
        name = "Argument",
        default = -1,
        min = -1,
        options = {'SKIP_SAVE'},
    )


class EDM_PT_set_argument(Operator):
    bl_idname = "edm.set_argument" 
    bl_label = "Set argument"
    bl_description = "Set argument"
    
    def execute(self, context):
        if not context.scene:
            return {'FINISHED'}
        
        props = get_arg_panel_props(context.scene)
        arg = props.CURRENT_ARG
        for o in context.scene.objects:
            ad = o.animation_data
            if not ad or not ad.action:
                continue

            a = utils.extract_arg_number(ad.action.name)
            if a == arg:
                mute_action(ad.action, False)
            else:
                mute_action(ad.action, True)
        
        return {'FINISHED'}


class EDM_PT_mute_animations(Operator):
    bl_idname = "edm.mute_animations" 
    bl_label = "Mute all"
    bl_description = "Mute all"
    
    def execute(self, context):
        if not context.scene:
            return {'FINISHED'}
        
        mute_anim(context.scene.objects, True)

        return {'FINISHED'}


class EDM_PT_unmute_animations(Operator):
    bl_idname = "edm.unmute_animations" 
    bl_label = "Unmute all"
    bl_description = "Unmute all"
    
    def execute(self, context):
        if not context.scene:
            return {'FINISHED'}
        
        mute_anim(context.scene.objects, False)

        return {'FINISHED'}

class EDM_PT_reset(Operator):
    bl_idname = "edm.reset" 
    bl_label = "Reset"
    bl_description = "Reset"
    
    def execute(self, context):
        if not context.scene:
            return {'FINISHED'}
        
        muted_groups = []
        muted_fcurves = []
        def collect_muted(o):
            nonlocal muted_groups, muted_fcurves

            ad = o.animation_data
            if not ad or not ad.action:
                return

            for g in get_action_groups(ad.action):
                if g.mute:
                    muted_groups.append(g)
                    g.mute = False

            fcurves = get_fcurves(ad.action)
            for fcu in fcurves:
                if fcu.mute:
                    muted_fcurves.append(fcu)
                    fcu.mute = False

        query_objects(context.scene.objects, collect_muted)

        context.scene.frame_set(100)
        context.scene.frame_start = 0
        context.scene.frame_end = 200

        for fcu in muted_fcurves:
            fcu.mute = True

        for g in muted_groups:
            g.mute = True
        
        return {'FINISHED'}

def get_arg_panel_props(o: bpy.types.Scene)->EDMArgPropsGroup:
    return o.EDMArgProps

def get_arg_panel_classes():
    return [
        EDMArgPropsGroup,
        EDM_PT_set_argument,
        EDM_PT_mute_animations,
        EDM_PT_unmute_animations,
        EDM_PT_reset,
    ]
