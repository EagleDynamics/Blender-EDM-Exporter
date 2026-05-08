def get_fcurves(action):
    if not action:
        return []
    
    return action.fcurves

def get_action_groups(action):
    if not action:
        return []
    
    return action.groups

def create_node_in_node_tree(bl_idname, node_tree):
    return node_tree.nodes.new(bl_idname)
