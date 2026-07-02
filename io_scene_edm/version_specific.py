import bpy

BLENDER_VERSION_MAJOR = bpy.app.version[0]
BLENDER_VERSION_MINOR = bpy.app.version[1]
IS_BLENDER_3 = BLENDER_VERSION_MAJOR == 3
IS_BLENDER_4 = BLENDER_VERSION_MAJOR == 4
IS_BLENDER_5 = BLENDER_VERSION_MAJOR == 5
BLENDER_40 = 40
BLENDER_41 = 41
BLENDER_50 = 50
BLENDER_51 = 51
BLENDER_RELEASE = bpy.app.version[0] * 10 + bpy.app.version[1]

if BLENDER_RELEASE < BLENDER_40:
    from bpy.types import NodeSocketInterface
    InterfaceNodeSocket = NodeSocketInterface
    get_fcurves = None
    get_action_groups = None
    create_node_in_node_tree = None
else:
    from bpy.types import NodeTreeInterfaceSocket
    InterfaceNodeSocket = NodeTreeInterfaceSocket

    if BLENDER_RELEASE >= BLENDER_50:
        import version_specific_v5 as v5
        get_fcurves = v5.get_fcurves
        get_action_groups = v5.get_action_groups
        create_node_in_node_tree = v5.create_node_in_node_tree
    else:    
        import version_specific_v4 as v4
        get_fcurves = v4.get_fcurves
        get_action_groups = v4.get_action_groups
        create_node_in_node_tree = v4.create_node_in_node_tree
