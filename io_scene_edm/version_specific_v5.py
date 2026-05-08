import bpy
from bpy_extras import anim_utils
from enums import BpyShaderNode

def get_fcurves(action):
    if not action:
        return []
    
    all_fcurves = []

    if action.slots is None:
        return all_fcurves
    
    for slot in action.slots:
        channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
        if channelbag:
            all_fcurves.extend(channelbag.fcurves)
    
    return all_fcurves

def get_action_groups(action):
    if not action:
        return []
    
    groups_dict = {}
    
    all_fcurves = get_fcurves(action)
    for fcu in all_fcurves:
        if fcu.group:
            groups_dict[fcu.group.name] = fcu.group
    
    return list(groups_dict.values())

def create_node_in_node_tree(bl_idname, node_tree):
    CONVERSION_MAP = {
        BpyShaderNode.SEPARATE_RGB: BpyShaderNode.SEPARATE_COLOR,
        BpyShaderNode.COMBINE_RGB: BpyShaderNode.COMBINE_COLOR,
    }
    
    target_name = bl_idname
    if target_name in CONVERSION_MAP:
        target_name = CONVERSION_MAP[target_name]
    
    node = node_tree.nodes.new(target_name)
    
    if bl_idname in CONVERSION_MAP:
        node.mode = 'RGB'

    return node