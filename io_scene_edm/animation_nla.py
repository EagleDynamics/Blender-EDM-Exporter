import bpy

from edm_exception import EdmFatalException
from utils import get_animation_argument
from pyedm_platform_selector import pyedm

def is_nla(ad):
    has_nla_tracks = len(ad.nla_tracks) > 0
    is_nla_active = ad.use_nla

    isNla = is_nla_active and has_nla_tracks
    if not isNla:
        return False
    return True

def export_nla_animation_data(armature_obj, bloc, brot, bsca, data_path_enum, allowed_args=None, target_bone=None):
    from animation import (
        extract_anim_vec3,
        extract_anim_vec4,
    )

    if not armature_obj or not armature_obj.animation_data or not armature_obj.animation_data.nla_tracks:
        return None, None, None

    if not target_bone:
        return None, None, None
    
    nla_tracks = armature_obj.animation_data.nla_tracks
    
    location_data = []
    rotation_data = [] 
    scale_data = []
    
    for track in nla_tracks:
        if not track.strips:
            continue     
            
        for strip in track.strips:
            action = strip.action
            if strip.type != 'CLIP' or not action:
                continue
                
            arg = get_animation_argument(strip.name, allowed_args)
            if arg == -1:
                raise EdmFatalException(f'Could not extract arg from action. Object.name="{armature_obj.name}". Action.name="{action.name}"')

            loc_points = extract_anim_vec3(action, data_path_enum.LOCATION, bloc)
            scale_points = extract_anim_vec3(action, data_path_enum.SCALE, bsca)
            rot_points = extract_anim_vec4(action, data_path_enum.ROTATION_QUAT, brot)
            
            if loc_points:
                location_data.append((arg, loc_points))
            if rot_points:
                rotation_data.append((arg, rot_points))
            if scale_points:
                scale_data.append((arg, scale_points))
    
    al_data = location_data if location_data else None
    ar_data = rotation_data if rotation_data else None  
    asc_data = scale_data if scale_data else None
    
    return al_data, ar_data, asc_data
