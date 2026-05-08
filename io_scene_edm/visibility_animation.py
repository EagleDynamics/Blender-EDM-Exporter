from bpy.types import Object
from typing import Union

from pyedm_platform_selector import pyedm
import animation as anim
import utils

# Returns visibility node or parent.
# allowed_args == None means any args are allowed
def extract_visibility_animation(parent: pyedm.Node, obj: Object, allowed_args) -> Union[None, pyedm.VisibilityNode]:
    if obj.animation_data and obj.animation_data.action:
        action = obj.animation_data.action
        
        arg = utils.extract_arg_number(action.name)
        if arg >= 0:
            if allowed_args and arg not in allowed_args:
                return parent
            avis = anim.extract_anim_float(action, 'VISIBLE')
            if avis:
                vis = pyedm.VisibilityNode("v_" + obj.name)
                vis.setArguments([[arg, avis]])
                parent = parent.addChild(vis)
                return parent
            
            
    return parent