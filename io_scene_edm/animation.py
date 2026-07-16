from mathutils import Matrix
from pyedm_platform_selector import pyedm
from enum import Enum
from math_tools import euler_to_quat
from bpy.types import FCurve, Action, Object, AnimData
from typing import Union, Callable, Set, Tuple, List
import utils
from edm_exception import EdmFatalException 
from logger import log
from bpy import context

from animation_nla import is_nla, export_nla_animation_data
from version_specific import get_fcurves

class AllowedAnimationsEnum(int, Enum):
    LOCATION    = 1 << 0
    SCALE       = 1 << 1
    ROTATION    = 1 << 2
    ALL         = 0xffffffff

class Data_Path_Enum(str, Enum):
    LOCATION        = 'location'
    ROTATION_QUAT   = 'rotation_quaternion'
    ROTATION_EULER  = 'rotation_euler'
    SCALE           = 'scale'
    ENERGY          = 'energy'
    COLOR           = 'color'
    CUTOFF_DISTANCE = 'cutoff_distance'
    SPECULAR        = 'specular_factor'
    SPOT_SIZE       = 'spot_size'
    SPOT_BLEND      = 'spot_blend'

class Anim_Type(Enum):
    AT_NLA = 0
    AT_FCURVES = 1
    AT_NONE = 2

OBJ_PATHS = [
    Data_Path_Enum.ROTATION_QUAT,
    Data_Path_Enum.ROTATION_EULER,
    Data_Path_Enum.LOCATION,
    Data_Path_Enum.SCALE
]

DATA_PATHS = [
    Data_Path_Enum.ENERGY,
    Data_Path_Enum.COLOR,
    Data_Path_Enum.CUTOFF_DISTANCE,
    Data_Path_Enum.SPECULAR,
    Data_Path_Enum.SPOT_SIZE,
    Data_Path_Enum.SPOT_BLEND
]

def get_anim_ch_paths(action: Action) -> Set[str]:
    result: Set[str] = set()
    if not action:
        return result
    fcurves = get_fcurves(action)
    for fcurve in fcurves:
        result.add(fcurve.data_path)
    return result

class DummyFCurve:
    def __init__(self, array_index: int, val) -> None:
        self.keyframe_points = []
        self.array_index = array_index
        self.val = val
    
    def update(self):
        pass

    def evaluate(self, frame):
        return self.val

def get_animation_type(obj: Object, data_path_modifier=lambda x: x):
    obj_ad = obj.animation_data
    if not obj_ad: #or not obj_ad.action:
        return Anim_Type.AT_NONE

    obj_has_nla = is_nla(obj_ad)

    ## just to warn user:
    if obj_has_nla and obj.type != 'ARMATURE':
        msg = f'Notice, EDM plugin support NLA animation only for ARMATURE. In your scene object {obj.name} of type {obj.type} has nla.'
        def draw_menu(self, context):
            self.layout.label(text=msg)    
        context.window_manager.popup_menu(draw_menu, icon='INFO')
        log.warning(msg)
    
    ## only for bones we check NLA. For objects of other type we ignore nla.
    if obj.type == 'ARMATURE':
        if obj_has_nla:
            return Anim_Type.AT_NLA
    if not obj_ad.action:
        return Anim_Type.AT_NONE
    
    fcurves = get_fcurves(obj_ad.action)
    for fcu in fcurves:
        if data_path_modifier(fcu.data_path) in OBJ_PATHS:
            return Anim_Type.AT_FCURVES
    
    return Anim_Type.AT_NONE

# Bones add thier name to data_path, so we add argument process and return data_path whitout bone name.
# allowed_args == None means any args are allowed
# Returns tuple (action, arg) on success or (None, -1).
def has_transform_anim(obj: Object, data_path_modifier=lambda x: x, allowed_args=None):
    obj_ad = obj.animation_data
    if not obj_ad or not obj_ad.action:
        return (None, -1)

    arg = utils.extract_arg_number(obj_ad.action.name)
    if arg < 0 or (allowed_args and arg not in allowed_args):
        return (None, -1)

    if is_nla(obj_ad):
        return (None, -1)

    fcurves = get_fcurves(obj_ad.action)
    for fcu in fcurves:
         if data_path_modifier(fcu.data_path) in OBJ_PATHS:
            return (obj_ad.action, arg)
    
    return (None, -1)

def has_data_anim(obj: Object) -> bool:
    if not hasattr(obj, 'data'):
        return False
    data_ad: AnimData = obj.data.animation_data
    if not data_ad or not data_ad.action:
        return False

    fcurves = get_fcurves(data_ad.action)
    for fcu in fcurves:
         if fcu.data_path in DATA_PATHS:
            return True
    return False

def has_path_anim(anim_data: AnimData, data_path: str) -> bool:
    if not anim_data: 
        return False
    if not data_path:
        return False
    if not anim_data.action:
        return False
    action: Action = anim_data.action

    fcurves = get_fcurves(action)
    for fcu in fcurves:
        if data_path == fcu.data_path:
            return True
    return False

KeyFrameTime = float
KeyFrameValue = Union[float, List[float]]
KeyFrameValueTransform = Callable[[KeyFrameValue], KeyFrameValue]
KeyFramePoint = Tuple[KeyFrameTime, KeyFrameValue]
KeyFramePoints = List[KeyFramePoint]

# Returns [(key, value), ...] for 1 animation element and [(key, [value1, value2, ...], ...] for multiple, or None
def fcurves_animation(fcurves: List[FCurve], expected_num: int, def_value: KeyFrameValue, fn: KeyFrameValueTransform = lambda v: v) -> KeyFramePoints:
    if not def_value:
        def_value = [0] * expected_num
    
    # collect keys
    keys = set()
    for fcu in fcurves:
        fcu.update()
        for kf in fcu.keyframe_points:
            keys.add(kf.co[0])

    # collect values
    keys = sorted([x for x in keys])
    kvs = []
    if expected_num > 1:
        for k in keys:
            v = []
            for fcu in fcurves:
                if not type(fcu) is DummyFCurve:
                    val = fcu.evaluate(k)
                    v.append(val)
                else:
                    v.append(fcu.val)
            kvs.append((((k / 100.0) - 1.0), fn(v)))
    else:
        for k in keys:
            for fcu in fcurves:
                v = fcu.evaluate(k)
                kvs.append((((k / 100.0) - 1.0), fn(v)))
        
    return kvs

# Returns [(key, value), ...] for 1 animation element and [(key, [value1, value2, ...], ...] for multiple, or None
def action_animation(action: Action, data_path: str, expected_num: int, def_value: KeyFrameValue, fn: KeyFrameValueTransform = lambda v: v) -> KeyFramePoints:
    if not action:
        return None
    
    if not def_value:
        def_value = [0] * expected_num
    
    fcurves = [DummyFCurve(i, def_value[i]) for i in range(expected_num)]

    not_dummy = False

    action_fcurves = get_fcurves(action)
    for fcu in action_fcurves:
        if fcu.data_path == data_path:
            not_dummy = True
            fcurves[fcu.array_index] = fcu

    if not not_dummy:
        return None
    
    return fcurves_animation(fcurves, expected_num, def_value, fn)

def extract_anim_float(action: Action, data_path: str, fn: KeyFrameValueTransform = lambda v: v) -> KeyFramePoints:
    return action_animation(action, data_path, 1, None, fn)

def extract_anim_vec2(action: Action, data_path: str, def_value, fn: KeyFrameValueTransform = lambda v: v) -> KeyFramePoints:
    return action_animation(action, data_path, 2, def_value, fn)

def extract_anim_vec3(action: Action, data_path: str, def_value, fn: KeyFrameValueTransform = lambda v: v) -> KeyFramePoints:
    return action_animation(action, data_path, 3, def_value, fn)

def extract_anim_vec4(action: Action, data_path: str, def_value, fn: KeyFrameValueTransform = lambda v: v) -> KeyFramePoints:
    return action_animation(action, data_path, 4, def_value, fn)

def euler_to_quat_anim(rot_anim):
    a = []
    for i in rot_anim[1]:
        a.append((i[0], euler_to_quat(i[1])))

    return [rot_anim[0], a]

def extract_transfrom_anim_fcurves(action, bloc, brot, bsca, name, allowed_anims=AllowedAnimationsEnum.ALL, 
                                   data_path_enum=Data_Path_Enum, allowed_args=None):
    
    euler_brot = brot.to_euler()

    al = ar = asc = None

    arg = utils.get_animation_argument(action.name, allowed_args)
    if arg == -1:
        raise EdmFatalException(f'Could not extract arg from action. Object.name="{name}". Action.name="{action.name}"')

    if allowed_anims & AllowedAnimationsEnum.LOCATION:
        loc_keys = extract_anim_vec3(action, data_path_enum.LOCATION, bloc)
        if loc_keys != None:
            al = pyedm.AnimationNode('al_' + name)
            al.setPositionAnimation([[arg, loc_keys]])
    
    if allowed_anims & AllowedAnimationsEnum.SCALE:
        scale_keys = extract_anim_vec3(action, data_path_enum.SCALE, bsca)
        if scale_keys:
            asc = pyedm.AnimationNode('as_' + name)
            asc.setScaleAnimation([[arg, scale_keys]])

    if allowed_anims & AllowedAnimationsEnum.ROTATION:
        rot_keys = extract_anim_vec3(action, data_path_enum.ROTATION_EULER, euler_brot)
        if rot_keys != None:
            anim = euler_to_quat_anim([arg, rot_keys])
            ar = pyedm.AnimationNode('ar_' + name)
            ar.setRotationAnimation([anim])
        else:
            rot_keys = extract_anim_vec4(action, data_path_enum.ROTATION_QUAT, brot)
            if rot_keys:
                ar = pyedm.AnimationNode('ar_' + name)
                ar.setRotationAnimation([[arg, rot_keys]])

    return al, ar, asc

def export_nla_animation(armature_obj, bone, allowed_anims, bloc, brot, bsca, data_path_enum=Data_Path_Enum, allowed_args=None):
    al_data, ar_data, asc_data = export_nla_animation_data(armature_obj, bloc, brot, bsca, data_path_enum, allowed_args, target_bone=bone)
    
    al = ar = asc = None

    if al_data and (allowed_anims & AllowedAnimationsEnum.LOCATION):
        al = pyedm.AnimationNode('al_' + bone.name)
        al.setPositionAnimation(al_data)
        
    if ar_data and (allowed_anims & AllowedAnimationsEnum.ROTATION):
        ar = pyedm.AnimationNode('ar_' + bone.name)
        ar.setRotationAnimation(ar_data)
        
    if asc_data and (allowed_anims & AllowedAnimationsEnum.SCALE):
        asc = pyedm.AnimationNode('as_' + bone.name)
        asc.setScaleAnimation(asc_data)

    return al, ar, asc


def extract_transform_anim(parent: pyedm.Node, obj: Object, action, mat, bmat, name, anim_type,
                           allowed_anims=AllowedAnimationsEnum.ALL, data_path_enum=Data_Path_Enum, 
                           allowed_args=None, bone=None):
    bmat_inv = bmat.inverted()
    bloc, brot, bsca = bmat.decompose()

    al = ar = asc = None

    if anim_type is Anim_Type.AT_FCURVES:
        al, ar, asc = extract_transfrom_anim_fcurves(action, bloc, brot, bsca, name, allowed_anims, data_path_enum, allowed_args)
    elif anim_type is Anim_Type.AT_NLA:
        ## works only for bones
        if obj.type == 'ARMATURE':
            al, ar, asc = export_nla_animation(obj, bone, allowed_anims, bloc, brot, bsca, data_path_enum, allowed_args)

    # Need for debugging to disable some animations.
    #al = ar = asc =  None
    a = parent
    
    a = a.addChild(pyedm.Transform(name + '_mat', mat))
    a = a.addChild(pyedm.Transform(name + '_bmat_inv', bmat_inv))

    if al:
        a = a.addChild(al)
    else:
        a = a.addChild(pyedm.Transform('tl_' + name, Matrix.LocRotScale(bloc, None, None)))

    if ar:
        a = a.addChild(ar)
    else:
        a = a.addChild(pyedm.Transform('tr_' + name, Matrix.LocRotScale(None, brot, None)))

    if asc:
        a = a.addChild(asc)
    else:
        a = a.addChild(pyedm.Transform('s_' + name, Matrix.LocRotScale(None, None, bsca)))

    return a

# allowed_args == None means any args are allowed
# Animation keys are in space before parenting applied (matrix_basis's space).
def extract_transform_animation(parent: pyedm.Node, obj: Object, allowed_args=None) -> Union[pyedm.AnimationNode, pyedm.Transform]:
    anim_type = get_animation_type(obj)
    
    if anim_type is Anim_Type.AT_NONE:
        parent = parent.addChild(pyedm.Transform(obj.name, obj.matrix_local))
        return parent
    
    a = extract_transform_anim(parent, obj, obj.animation_data.action, obj.matrix_local, obj.matrix_basis, 
                               obj.name, anim_type, allowed_args=allowed_args)

    return a
