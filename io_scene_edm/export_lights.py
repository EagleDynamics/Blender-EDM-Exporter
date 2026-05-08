from math import radians, pi, sqrt, pow
from typing import Union, List, Dict, Tuple, Set
import bpy
from bpy.types import Object, ShaderNodeEmission, ShaderNodeOutputLight, Light, SpotLight, Node, AnimData, Action
from mathutils import Matrix

import animation as anim
import scene_light_constants as light_const

from objects_custom_props import get_edm_props
from pyedm_platform_selector import pyedm
import utils


from enums import (
    ObjectTypeEnum, 
    LampTypeEnum, 
    BpyShaderNode, 
    NodeSocketInEmissiveEnum,
    ShaderNodeLightFalloffInParams
)
from objects_custom_props import EDMPropsGroup

from logger import log
from serializer import type_helper

def get_cycles_emission_node(bpy_node: Node) -> Union[ShaderNodeEmission, None]:
    if not bpy_node:
        return None
    for socket in bpy_node.inputs:
        for link in socket.links:
            linked_node: Node = link.from_node
            if linked_node.bl_idname == BpyShaderNode.EMISSION:
                return linked_node
            for linked_node_socket in linked_node.inputs:
                for linked_node_link in linked_node_socket.links:
                    return get_cycles_emission_node(linked_node_link.from_node)
    
    return None

def get_light_output_nodes(light: Light) -> List[ShaderNodeOutputLight]:
    use_nodes: bool = light.use_nodes and bool(light.node_tree)
    if not use_nodes:
        return []
    out_nodes_list: List[ShaderNodeOutputLight] = []
    for bpy_node in light.node_tree.nodes:
        if bpy_node.bl_idname == BpyShaderNode.OUTPUT_LIGHT:
            out_nodes_list.append(bpy_node)
    return out_nodes_list

def get_light_output(light: Light) -> Union[ShaderNodeOutputLight, None]:
    if not light:
        return None
    out_nodes_list: List[ShaderNodeOutputLight] = get_light_output_nodes(light)
    if len(out_nodes_list) == 0:
        return None
    for bpy_node in out_nodes_list:
        if bpy_node.is_active_output:
            return bpy_node
    return None

def gather_color(blender_lamp: Light) -> Tuple[float]:
    bpy_node: Node = get_light_output(blender_lamp)
    emission_node = get_cycles_emission_node(bpy_node)
    if emission_node is not None:
        return type_helper(emission_node.inputs[NodeSocketInEmissiveEnum.COLOR].default_value)

    return type_helper(blender_lamp.color)

def get_falloff_node(bpy_node: Node) -> Union[ShaderNodeEmission, None]:
    if not bpy_node:
        return None
    for socket in bpy_node.inputs:
        for link in socket.links:
            linked_node: Node = link.from_node
            if linked_node.bl_idname == BpyShaderNode.LIGHT_FALLOFF:
                return linked_node
            for linked_node_socket in linked_node.inputs:
                for linked_node_link in linked_node_socket.links:
                    return get_falloff_node(linked_node_link.from_node)
    
    return None

PBR_WATTS_TO_LUMENS = 683

def gather_intensity(blender_lamp: Light) -> float:
    bpy_node: Node = get_light_output(blender_lamp)
    emission_node = get_cycles_emission_node(bpy_node)
    emission_strength = 0.0
    if emission_node is not None:
        if blender_lamp.type != LampTypeEnum.SUN:
            falloff_node = get_falloff_node(emission_node)
            if falloff_node:
                emission_strength = falloff_node.inputs[ShaderNodeLightFalloffInParams.STRENGTH].default_value / (pi * 4.0)
            else:
                emission_strength = blender_lamp.energy
        else:
            emission_strength = emission_node.inputs[ShaderNodeLightFalloffInParams.STRENGTH].default_value
    else:
        emission_strength = blender_lamp.energy
    #return emission_strength
    
    if blender_lamp.type == LampTypeEnum.SUN: # W/m^2 to lm/m^2
        emission_luminous = emission_strength
    else:
        emission_luminous = emission_strength / (4 * pi)
    
    emission_luminous *= PBR_WATTS_TO_LUMENS
    
    return emission_luminous

def light_power_to_luminous_sp(power: float) -> float:
    left_edm_cx = light_const.blender_lamp_energy_coefficient
    emission_luminous = power * PBR_WATTS_TO_LUMENS
    emission_luminous *= left_edm_cx
    return emission_luminous

def light_power_to_energy(power: float) -> float:
    emission_luminous: float = light_power_to_luminous_sp(power)
    emission_luminous = pow(emission_luminous, light_const.blender_lamp_weak_coefficient)
    return emission_luminous

def gather_intensity_pow(blender_lamp: Light) -> float:
    bpy_node: Node = get_light_output(blender_lamp)
    emission_node = get_cycles_emission_node(bpy_node)
    emission_strength = 0.0
    if emission_node is not None:
        if blender_lamp.type != LampTypeEnum.SUN:
            falloff_node = get_falloff_node(emission_node)
            if falloff_node:
                emission_strength = falloff_node.inputs[ShaderNodeLightFalloffInParams.STRENGTH].default_value / (pi * 4.0)
            else:
                emission_strength = blender_lamp.energy
        else:
            emission_strength = emission_node.inputs[ShaderNodeLightFalloffInParams.STRENGTH].default_value
    else:
        emission_strength = blender_lamp.energy
    
    if blender_lamp.type == LampTypeEnum.SUN: # W/m^2 to lm/m^2
        emission_strength = emission_strength
    else:
        emission_strength = emission_strength / (4 * pi)
    
    return light_power_to_luminous_sp(emission_strength)

def gather_range(blender_lamp: Light) -> float:
    if blender_lamp.use_custom_distance:
        return blender_lamp.cutoff_distance
    else:
        return 20.0
    
def phy_angle_clamp(angle: float) -> float:
    return angle if angle < radians(170) else radians(170)
    
def gather_outer_cone_angle(blender_lamp: SpotLight) -> float:
    return phy_angle_clamp(blender_lamp.spot_size)

def spot_blend_to_angle(spot_size_angle: float, spot_blend: float) -> float:
    return spot_size_angle - spot_size_angle * (1.0 - spot_blend)

def gather_inner_cone_angle(blender_lamp: SpotLight) -> float:
    return spot_blend_to_angle(blender_lamp.spot_size, blender_lamp.spot_blend)

def light_animation_terms(object: Object) -> Set[str]:
    is_data_anim: bool = anim.has_data_anim(object)
    anim_ch_paths: Set[str] = set()
    if is_data_anim:
        blender_lamp: Light = object.data
        animation: AnimData = blender_lamp.animation_data
        action = animation.action
        anim_ch_paths = anim.get_anim_ch_paths(action)
    return anim_ch_paths

class LightData:
    def __init__(self, object: Object, transform_node: pyedm.Node) -> None:
        self.light_transform = pyedm.Transform('Fake Light Transform', Matrix.Rotation(radians(90.0), 4, 'Y'))
        transform_node.addChild(self.light_transform)

        self.blender_lamp: Light = object.data
        edm_props = get_edm_props(object)
        anim_ch_paths: Set[str] = light_animation_terms(object)
        terms_map = {
            anim.Data_Path_Enum.COLOR:              anim.Data_Path_Enum.COLOR in anim_ch_paths and edm_props.LIGHT_COLOR_ARG >= 0,
            anim.Data_Path_Enum.ENERGY:             anim.Data_Path_Enum.ENERGY in anim_ch_paths and edm_props.LIGHT_POWER_ARG >= 0,
            anim.Data_Path_Enum.CUTOFF_DISTANCE:    anim.Data_Path_Enum.CUTOFF_DISTANCE in anim_ch_paths and edm_props.LIGHT_DISTANCE_ARG >= 0,
            anim.Data_Path_Enum.SPECULAR:           anim.Data_Path_Enum.SPECULAR in anim_ch_paths and edm_props.LIGHT_SPECULAR_ARG >= 0,
            anim.Data_Path_Enum.SPOT_SIZE:          anim.Data_Path_Enum.SPOT_SIZE in anim_ch_paths and edm_props.LIGHT_SPOT_SHAPE_ARG >= 0,
            anim.Data_Path_Enum.SPOT_BLEND:         anim.Data_Path_Enum.SPOT_BLEND in anim_ch_paths and edm_props.LIGHT_SPOT_SHAPE_ARG >= 0
        }
        
        action: Action = self.blender_lamp.animation_data.action if len(anim_ch_paths) > 0 else None

        self.light_color = gather_color(self.blender_lamp)
        if terms_map[anim.Data_Path_Enum.COLOR]:
            color_keys = anim.extract_anim_vec3(action, anim.Data_Path_Enum.COLOR, self.light_color)
            self.edm_color_prop = pyedm.PropertyFloat3(edm_props.LIGHT_COLOR_ARG, color_keys)
        else:
            self.edm_color_prop = pyedm.PropertyFloat3(self.light_color)

        self.light_intensity = gather_intensity_pow(self.blender_lamp)
        self.light_intensity = pow(self.light_intensity, light_const.blender_lamp_weak_coefficient)
        if terms_map[anim.Data_Path_Enum.ENERGY]:
            power_keys = anim.extract_anim_float(action, anim.Data_Path_Enum.ENERGY, light_power_to_energy)
            self.edm_intensity_prop = pyedm.PropertyFloat(edm_props.LIGHT_POWER_ARG, power_keys)
        else:
            self.edm_intensity_prop = pyedm.PropertyFloat(self.light_intensity)

        if not self.blender_lamp.use_custom_distance:
            log.warning(f"{object.name} light has no custom distance set.")
        self.light_distance = gather_range(self.blender_lamp)
        if terms_map[anim.Data_Path_Enum.CUTOFF_DISTANCE]:
            distance_keys = anim.extract_anim_float(action, anim.Data_Path_Enum.CUTOFF_DISTANCE)
            self.edm_distance_prop = pyedm.PropertyFloat(edm_props.LIGHT_DISTANCE_ARG, distance_keys)
        else:
            self.edm_distance_prop = pyedm.PropertyFloat(self.light_distance)

        self.specular: float = self.blender_lamp.specular_factor
        if terms_map[anim.Data_Path_Enum.SPECULAR]:
            specular_keys = anim.extract_anim_float(action, anim.Data_Path_Enum.SPECULAR)
            self.edm_specular_prop = pyedm.PropertyFloat(edm_props.LIGHT_SPECULAR_ARG, specular_keys)
        else:
            self.edm_specular_prop = pyedm.PropertyFloat(self.specular)
        
        if self.blender_lamp.type == LampTypeEnum.SPOT:
            blender_spot_light: SpotLight = self.blender_lamp
            
            self.phy = gather_outer_cone_angle(blender_spot_light)
            if terms_map[anim.Data_Path_Enum.SPOT_SIZE]:
                spot_size_keys = anim.extract_anim_float(action, anim.Data_Path_Enum.SPOT_SIZE, phy_angle_clamp)
                self.edm_phy_prop = pyedm.PropertyFloat(edm_props.LIGHT_SPOT_SHAPE_ARG, spot_size_keys) 
            else:
                self.edm_phy_prop = pyedm.PropertyFloat(self.phy)
            
            self.theta = blender_spot_light.spot_blend
            if terms_map[anim.Data_Path_Enum.SPOT_BLEND]:
                #spot_blend_keys = anim.extract_anim_float(action, anim.Data_Path_Enum.SPOT_BLEND, lambda spot_blend: spot_blend_to_angle(blender_spot_light.spot_size, spot_blend))
                spot_blend_keys = anim.extract_anim_float(action, anim.Data_Path_Enum.SPOT_BLEND)
                self.edm_blend_prop = pyedm.PropertyFloat(edm_props.LIGHT_SPOT_SHAPE_ARG, spot_blend_keys)
            else:
                self.edm_blend_prop = pyedm.PropertyFloat(self.theta)

def make_spot_light(object: Object, transform_node: pyedm.Node) -> pyedm.SpotLight:
    light_data: LightData = LightData(object, transform_node)
    edm_props = get_edm_props(object)

    softness: float = edm_props.LIGHT_SOFTNESS
    softness_prop = pyedm.PropertyFloat(softness)

    blender_spot_light: SpotLight = light_data.blender_lamp
    edm_light = pyedm.SpotLight(object.name)
    edm_light.setColor(light_data.edm_color_prop)
    edm_light.setBrightness(light_data.edm_intensity_prop)
    edm_light.setDistance(light_data.edm_distance_prop)
    edm_light.setAngles(light_data.edm_phy_prop, light_data.edm_blend_prop)
    edm_light.setSpecularAmount(light_data.edm_specular_prop)
    edm_light.setSoftness(softness_prop)
    edm_light.setControlNode(light_data.light_transform)

    return edm_light

def make_point_light(object: Object, transform_node: pyedm.Node) -> pyedm.OmniLight:
    light_data: LightData = LightData(object, transform_node)
    edm_props = get_edm_props(object)

    softness: float = edm_props.LIGHT_SOFTNESS
    softness_prop = pyedm.PropertyFloat(softness)

    edm_light = pyedm.OmniLight(object.name)
    edm_light.setColor(light_data.edm_color_prop)
    edm_light.setBrightness(light_data.edm_intensity_prop)
    edm_light.setDistance(light_data.edm_distance_prop)
    edm_light.setSpecularAmount(light_data.edm_specular_prop)
    edm_light.setSoftness(softness_prop)
    edm_light.setControlNode(light_data.light_transform)

    return edm_light


## extract volume light params from side panel.
def set_volumetric_light_params(object: Object, edm_light: pyedm.ILight):
    edm_props = get_edm_props(object)

    radiusFac = pyedm.PropertyFloat(edm_props.LIGHT_VOLUME_RADIUS_FACTOR)
    edm_light.setVolumeRadiusFactor(radiusFac)

    densityFac = pyedm.PropertyFloat(edm_props.LIGHT_VOLUME_DENSITY_FACTOR)
    edm_light.setVolumeDensityFactor(densityFac)

    nearDistance = pyedm.PropertyFloat(edm_props.LIGHT_VOLUME_NEAR_DISTANCE)
    edm_light.setVolumeNearDistance(nearDistance)
    
    #TODO: make it better    
    if(edm_props.LIGHT_VOLUME_TYPE == 'LANDING'):
            edm_light.setVolumeType(0)
    if(edm_props.LIGHT_VOLUME_TYPE == 'NAV'):
            edm_light.setVolumeType(1)
    if(edm_props.LIGHT_VOLUME_TYPE == 'TAXI'):
            edm_light.setVolumeType(2)
    if(edm_props.LIGHT_VOLUME_TYPE == 'BANO'):
            edm_light.setVolumeType(3)


def export_light(object: Object, transform_node: pyedm.Node):
    edm_light: pyedm.ILight = None
    blender_lamp: Light = object.data
    if blender_lamp.type == LampTypeEnum.SPOT:
        edm_light = make_spot_light(object, transform_node)
    elif blender_lamp.type == LampTypeEnum.POINT:
        edm_light = make_point_light(object, transform_node)
    
    ## common features
    set_volumetric_light_params(object, edm_light)

    return edm_light

def is_light(object: Object) -> bool:
    if object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP:
        return True
    return False

class LightChildPanel(bpy.types.Panel):
    bl_label = "Light type Properties"
    bl_idname = "OBJECT_PT_light_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "OBJECT_PT_edm_data"

    @classmethod
    def poll(cls, context):
        if not utils.has_object(context):
            return

        object: Object = context.object

        result = object.type == ObjectTypeEnum.LIGHT or object.type == ObjectTypeEnum.LAMP
        return result

    def draw(self, context):
        if not utils.has_object(context):
            return

        layout = self.layout
        object: Object = context.object
        props = get_edm_props(object)

        box = layout.box()
        row = box.row()
        row.label(text='Light Arguments')

        row = box.row()
        row.prop(props, "LIGHT_COLOR_ARG")
        row = box.row()
        row.prop(props, "LIGHT_POWER_ARG")
        row = box.row()
        row.prop(props, "LIGHT_DISTANCE_ARG")

        row = box.row()
        row.label(text='Light Params')
        
        row = box.row()
        row.prop(props, "LIGHT_SOFTNESS")

        blender_lamp: Light = object.data
        if blender_lamp.type == LampTypeEnum.SPOT:
            row = box.row()
            row.prop(props, "LIGHT_SPOT_SHAPE_ARG")

        row = box.row()
        row.label(text='Light Volume Params')            
        row = box.row()
        row.prop(props, "LIGHT_VOLUME_RADIUS_FACTOR")
        row = box.row()
        row.prop(props, "LIGHT_VOLUME_DENSITY_FACTOR")
        row = box.row()
        row.prop(props, "LIGHT_VOLUME_NEAR_DISTANCE")
        row = box.row()
        row.prop(props, "LIGHT_VOLUME_TYPE")

        return