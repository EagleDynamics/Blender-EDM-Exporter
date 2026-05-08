## File contains methods that are used in many material files: 
## for getting values in drop-down lists, for creating blocks, etc. 

from typing import Tuple

from bpy.types import Material

import utils
from logger import log
import animation as anim
from mesh_storage import MeshStorage
from pyedm_platform_selector import pyedm
from objects_custom_props import EDMPropsGroup
from custom_sockets import (
    ShadowCasterEnumItems, 
    TransparencyEnumItems,
    TransparencyGlassEnumItems,
    GlassEnumItems
)
from materials.material_wrap import (
    AttachedTextureStruct,
)
from enums import (
    EDMCustomEmissiveTypeInt,
    ShaderNodeMappingInParams,  
    EdmTransparencySocketItemsEnum,
)

## methods below extract values from drop-down list: shadow_caster, transparency, glass type.
def get_shadow_caster_value(shadow_caster_value) -> int:
    if shadow_caster_value == ShadowCasterEnumItems[0][0]:
        return 0
    elif shadow_caster_value == ShadowCasterEnumItems[1][0]:
        return 1
    elif shadow_caster_value == ShadowCasterEnumItems[2][0]:
        return 2
    else:
        return 0

def get_transparency_value(transparency_value) -> int:
    if transparency_value == TransparencyEnumItems[0][0]:
        return 0
    elif transparency_value == TransparencyEnumItems[1][0]:
        return 1
    elif transparency_value == TransparencyEnumItems[2][0]:
        return 2
    elif transparency_value == TransparencyEnumItems[3][0]:
        return 3
    elif transparency_value == TransparencyEnumItems[4][0]:
        return 3 ## yes. it should be 3
    elif transparency_value == TransparencyEnumItems[5][0]:
        return 6
    else:
        return 0
    
def get_glass_transparency_value(transparency_value) -> int:
    if transparency_value == TransparencyGlassEnumItems[0][0]:
        return 1
    elif transparency_value == TransparencyGlassEnumItems[1][0]:
        return 3
    elif transparency_value == TransparencyGlassEnumItems[2][0]:
        return 6
    else:
        return 1
    
def get_glass_value(glass_value) -> int:
    if glass_value == GlassEnumItems[0][0]:
        return 0
    elif glass_value == GlassEnumItems[1][0]:
        return 1
    else:
        return 0

def make_base_texture(mesh_storage: MeshStorage, bpy_material: Material, is_valid: bool, texture: AttachedTextureStruct) -> pyedm.BaseBlock:
    edm_base_bock = pyedm.BaseBlock()
    
    albedo_uv_map_name: str = texture.get_uv_map(mesh_storage.uv_active)
    albedo_map_name: str = texture.texture_name
    uv_shift_animation_path: str = texture.uv_move_node.inputs[ShaderNodeMappingInParams.LOCATION].path_from_id('default_value') if is_valid and texture.uv_move_node else None
    arg_n: int = utils.extract_arg_number(texture.uv_move_node.label) if texture.uv_move_node else -1

    edm_base_bock.setAlbedoMapUV(mesh_storage.get_uv(albedo_uv_map_name, bpy_material.name))
    edm_base_bock.setAlbedoMap(albedo_map_name)

    ## animation of albedo diffuse uv map
    is_uv_shift_animated: bool = uv_shift_animation_path and anim.has_path_anim(bpy_material.node_tree.animation_data, uv_shift_animation_path)
    if is_uv_shift_animated and arg_n != -1:
        key_list: anim.KeyFramePoints = anim.extract_anim_vec3(bpy_material.node_tree.animation_data.action, uv_shift_animation_path, (0.0, 0.0, 0.0), lambda v: [v[0], 1.0 - v[1]])
        uv_shift_prop = pyedm.PropertyFloat2(arg_n, key_list)
        edm_base_bock.setAlbedoMapUVShift(uv_shift_prop)

    return edm_base_bock

def make_glass_block(mesh_storage: MeshStorage, bpy_material: Material, textures, values, is_valid: bool, edm_props: EDMPropsGroup) -> pyedm.BaseBlock:
    edm_glass_block = pyedm.GlassFilterBlock()
    if textures.glass_filter.texture:
        glass_color_map: str = textures.glass_filter.texture.texture_name
        edm_glass_block.setColorMap(glass_color_map)
    else:
        base_color_prop = pyedm.PropertyFloat3((textures.glass_filter.default_color[0], textures.glass_filter.default_color[1], textures.glass_filter.default_color[2]))
        edm_glass_block.setColor(base_color_prop)    
    return edm_glass_block

def make_def_base_block(mesh_storage: MeshStorage, bpy_material: Material, textures, values, is_valid: bool, edm_props: EDMPropsGroup) -> pyedm.BaseBlock:
    if not (values.blend_mode.value == EdmTransparencySocketItemsEnum.SUM_BLENDING_SI and textures.emissive.texture):
        if not textures.albedo.texture:
            if utils.cmp_vec4(textures.albedo.default_color, (0.0, 0.0, 0.0, 1.0)):
                return None
    
    if values.blend_mode.value == EdmTransparencySocketItemsEnum.SUM_BLENDING_SI and textures.emissive.texture:
        edm_base_bock = make_base_texture(mesh_storage, bpy_material, is_valid, textures.emissive.texture)
    elif textures.albedo.texture:
        edm_base_bock = make_base_texture(mesh_storage, bpy_material, is_valid, textures.albedo.texture)
    else:
        edm_base_bock = pyedm.ColorBaseBlock()
        base_color_path: str = textures.albedo.color_anim_path
        is_color_value_animated: bool = base_color_path and anim.has_path_anim(bpy_material.node_tree.animation_data, base_color_path)
        if is_color_value_animated and edm_props.COLOR_ARG != -1:
            arg_color_n: int = edm_props.COLOR_ARG
            key_color_list: anim.KeyFramePoints = anim.extract_anim_vec4(bpy_material.node_tree.animation_data.action, base_color_path, (0.0, 0.0, 0.0, 1.0), lambda v: [v[0], v[1], v[2]])
            base_color_prop = pyedm.PropertyFloat3(arg_color_n, key_color_list)
            edm_base_bock.setColor(base_color_prop)
        else:
            base_color_prop = pyedm.PropertyFloat3((textures.albedo.default_color[0], textures.albedo.default_color[1], textures.albedo.default_color[2]))
            edm_base_bock.setColor(base_color_prop)

    edm_base_bock.setPositions(mesh_storage.positions)
    edm_base_bock.setNormals(mesh_storage.normals)

    return edm_base_bock

def make_def_rmo_block(mesh_storage: MeshStorage, textures, bpy_material) -> pyedm.AormsBlock:
    if not textures.rmo.texture:
        return None
    
    edm_aorms_block = pyedm.AormsBlock()

    aorms_uv_map_name: str = textures.rmo.texture.get_uv_map(mesh_storage.uv_active)
    edm_aorms_block.setAormsMapUV(mesh_storage.get_uv(aorms_uv_map_name, bpy_material.name))

    aorms_map_name: str = textures.rmo.texture.texture_name
    edm_aorms_block.setAormsMap(aorms_map_name)

    return edm_aorms_block

def make_def_normal_block(mesh_storage: MeshStorage, textures, bpy_material) -> pyedm.NormalBlock:
    if not textures.normal.texture:
        return None
    
    edm_normals_block = pyedm.NormalBlock()

    normals_uv_map_name: str = textures.normal.texture.get_uv_map(mesh_storage.uv_active)
    edm_normals_block.setNormalMapUV(mesh_storage.get_uv(normals_uv_map_name, bpy_material.name))

    normal_map_name: str = textures.normal.texture.texture_name
    edm_normals_block.setNormalMap(normal_map_name)

    return edm_normals_block

def make_def_ao_block(mesh_storage: MeshStorage, bpy_material: Material, textures, values, is_valid: bool, 
                      edm_props: EDMPropsGroup) -> pyedm.AoBlock:
    if not textures.light_map.texture:
        return None
    
    ao_block = pyedm.AoBlock()

    ao_uv_name: str = textures.light_map.texture.get_uv_map(mesh_storage.uv_active)
    ao_block.setAoMapUV(mesh_storage.get_uv(ao_uv_name, bpy_material.name))

    ao_map_name: str = textures.light_map.texture.texture_name
    ao_block.setAoMap(ao_map_name)

    uv_shift_animation_path: str = textures.light_map.texture.uv_move_loc_anim_path if is_valid and textures.light_map.texture.uv_move_node else None
    is_uv_shift_animated: bool = uv_shift_animation_path and anim.has_path_anim(bpy_material.node_tree.animation_data, uv_shift_animation_path)
    arg_n: int = utils.extract_arg_number(textures.light_map.texture.uv_move_node.label) if is_uv_shift_animated else -1
    if is_uv_shift_animated and arg_n != -1:
        key_list: anim.KeyFramePoints = anim.extract_anim_vec3(bpy_material.node_tree.animation_data.action, uv_shift_animation_path, (0.0, 0.0, 0.0), lambda v: [v[0], 1.0 - v[1]])
        uv_shift_prop = pyedm.PropertyFloat2(arg_n, key_list)
        ao_block.setAoShift(uv_shift_prop)

    if edm_props.AO_ARG >= 0:
        ao_block.setAoAnimationArgument(edm_props.AO_ARG)

    return ao_block
    
def check_emissive_texture_eq_rule(textures, mat_name: str) -> None:
    if not textures.emissive.texture or not textures.emissive_mask.texture:
        return
    if not textures.emissive.texture.texture_name == textures.emissive_mask.texture.texture_name:
        log.fatal(f"Emissive texture has different alpha source on material {mat_name}. Emissive texure is {textures.emissive.texture.texture_name} and alpha mask is {textures.emissive_mask.texture.texture_name}")

def make_def_emissive_block(mesh_storage: MeshStorage, bpy_material: Material,
                             textures, values, is_valid: bool, mat_name: str, edm_props: EDMPropsGroup) -> pyedm.EmissiveBlock:
    if not textures.emissive.texture and utils.cmp_vec4(textures.emissive.default_color, (0.0, 0.0, 0.0, 1.0)):
        return None

    check_emissive_texture_eq_rule(textures, mat_name)
    
    edm_emissive_block = pyedm.EmissiveBlock()
    
    if textures.emissive.texture:
        edm_emissive_block.setEmissiveType(int(EDMCustomEmissiveTypeInt.DEFAULT))

        emissive_uv_map_name: str = textures.emissive.texture.get_uv_map(mesh_storage.uv_active)
        edm_emissive_block.setEmissiveMapUV(mesh_storage.get_uv(emissive_uv_map_name, bpy_material.name))
    
        emissive_map_name: str = textures.emissive.texture.texture_name
        edm_emissive_block.setEmissiveMap(emissive_map_name)

        ## animation of emissive texture
        texture = textures.emissive.texture
        uv_shift_animation_path: str = texture.uv_move_node.inputs[ShaderNodeMappingInParams.LOCATION].path_from_id('default_value') if is_valid and texture.uv_move_node else None
        arg_n: int = utils.extract_arg_number(texture.uv_move_node.label) if texture.uv_move_node else -1
        is_uv_shift_animated: bool = uv_shift_animation_path and anim.has_path_anim(bpy_material.node_tree.animation_data, uv_shift_animation_path)
        if is_uv_shift_animated and arg_n != -1:
            key_list: anim.KeyFramePoints = anim.extract_anim_vec3(bpy_material.node_tree.animation_data.action, uv_shift_animation_path, (0.0, 0.0, 0.0), lambda v: [v[0], 1.0 - v[1]])
            uv_shift_prop = pyedm.PropertyFloat2(arg_n, key_list)
            edm_emissive_block.setUVShift(uv_shift_prop)
    else:
        edm_emissive_block.setEmissiveType(int(EDMCustomEmissiveTypeInt.SELF_ILLUMINATION))

        emissive_color_path: str = textures.emissive.color_anim_path
        is_emissive_color_animated: bool = emissive_color_path and anim.has_path_anim(bpy_material.node_tree.animation_data, emissive_color_path)
        if is_emissive_color_animated and edm_props.EMISSIVE_COLOR_ARG != -1:
            arg_color_n: int = edm_props.EMISSIVE_COLOR_ARG
            key_color_list: anim.KeyFramePoints = anim.extract_anim_vec4(bpy_material.node_tree.animation_data.action, emissive_color_path, (0.0, 0.0, 0.0, 1.0), lambda v: [v[0], v[1], v[2]])
            emissive_color_prop = pyedm.PropertyFloat3(arg_color_n, key_color_list)
        else:
            emissive_color: Tuple[float, float, float] = (textures.emissive.default_color[0], textures.emissive.default_color[1], textures.emissive.default_color[2])
            emissive_color_prop = pyedm.PropertyFloat3(emissive_color)
            
        edm_emissive_block.setColor(emissive_color_prop)

        if textures.emissive_mask.texture:
            emissive_mask_uv_map_name: str = textures.emissive_mask.texture.get_uv_map(mesh_storage.uv_active)
            edm_emissive_block.setEmissiveMapUV(mesh_storage.get_uv(emissive_mask_uv_map_name, bpy_material.name))

            emissive_mask_map_name: str = textures.emissive_mask.texture.texture_name
            edm_emissive_block.setEmissiveMap(emissive_mask_map_name)
        
    emissive_value: float = values.emissive_value.value
    emissive_value_prop = pyedm.PropertyFloat(emissive_value)
    emissive_value_anim_path: str = values.emissive_value.anim_path if is_valid else None
    is_emissive_value_animated: bool = emissive_value_anim_path and anim.has_path_anim(bpy_material.node_tree.animation_data, emissive_value_anim_path)
    if is_emissive_value_animated and edm_props.EMISSIVE_ARG != -1:
        key_list: anim.KeyFramePoints = anim.extract_anim_float(bpy_material.node_tree.animation_data.action, emissive_value_anim_path)
        arg_n: int = edm_props.EMISSIVE_ARG
        emissive_value_prop = pyedm.PropertyFloat(arg_n, key_list)
    edm_emissive_block.setAmount(emissive_value_prop)

    if values.blend_mode.value == EdmTransparencySocketItemsEnum.SUM_BLENDING_SI:
        if not textures.albedo.texture and not utils.cmp_vec4(textures.emissive.default_color, (0.0, 0.0, 0.0, 1.0)):
            edm_emissive_block.setEmissiveType(int(EDMCustomEmissiveTypeInt.ADDITIVE_SELF_COLOR_ILLUMINATION))
        elif textures.albedo.texture and textures.emissive.texture:
            edm_emissive_block.setEmissiveType(int(EDMCustomEmissiveTypeInt.ADDITIVE_SELF_TEX_ILLUMINATION))
        else:
            edm_emissive_block.setEmissiveType(int(EDMCustomEmissiveTypeInt.ADDITIVE_SELF_ILLUMINATION))

    return edm_emissive_block

def make_def_flir_block(textures) -> pyedm.FlirBlock:
    if not textures.flir.texture:
        return None
    
    edm_flir_block = pyedm.FlirBlock()

    flir_name: str = textures.flir.texture.texture_name
    edm_flir_block.setFlirMap(flir_name)

    return edm_flir_block

def make_def_decal_block(mesh_storage: MeshStorage, textures, is_valid: bool, bpy_material: Material) -> pyedm.DecalBlock:
    if not textures.decal.texture:
        return None
    
    edm_decal_block = pyedm.DecalBlock()

    decal_uv_map_name: str = textures.decal.texture.get_uv_map(mesh_storage.uv_active)
    edm_decal_block.setDecalMapUV(mesh_storage.get_uv(decal_uv_map_name, bpy_material.name))

    decal_map_name: str = textures.decal.texture.texture_name
    edm_decal_block.setDecalMap(decal_map_name)

    uv_shift_animation_path: str = textures.decal.texture.uv_move_loc_anim_path if is_valid and textures.decal.texture.uv_move_node else None
    is_uv_shift_animated: bool = ( uv_shift_animation_path and anim.has_path_anim(bpy_material.node_tree.animation_data, uv_shift_animation_path) )
    arg_n: int = utils.extract_arg_number(textures.decal.texture.uv_move_node.label) if is_uv_shift_animated else -1
    if is_uv_shift_animated and arg_n != -1:
        key_list: anim.KeyFramePoints = anim.extract_anim_vec3(bpy_material.node_tree.animation_data.action, uv_shift_animation_path, (0.0, 0.0, 0.0), lambda v: [v[0], 1.0 - v[1]])
        uv_shift_prop = pyedm.PropertyFloat2(arg_n, key_list)
        edm_decal_block.setDecalShift(uv_shift_prop)

    return edm_decal_block

def make_def_damage_block(mesh_storage: MeshStorage, textures, edm_props: EDMPropsGroup, bpy_material) -> pyedm.DamageBlock:
    if not textures.damage_color.texture:
        return None
    if not textures.damage_mask.texture:
        return None
    
    if edm_props.DAMAGE_ARG < 0 and not mesh_storage.has_dmg_group:
        return None

    edm_damage_block = pyedm.DamageBlock()
    if mesh_storage.has_dmg_group:
        edm_damage_block.setPerVertexArguments(mesh_storage.damage_arguments)

    damage_color_uv_map_name: str = textures.damage_color.texture.get_uv_map(mesh_storage.uv_active)
    edm_damage_block.setAlbedoMapUV(mesh_storage.get_uv(damage_color_uv_map_name, bpy_material.name))

    damage_color_map_name: str = textures.damage_color.texture.texture_name
    edm_damage_block.setAlbedoMap(damage_color_map_name)

    if textures.damage_normal.texture:
        damage_normal_uv_map_name: str = textures.damage_normal.texture.get_uv_map(mesh_storage.uv_active)
        edm_damage_block.setNormalMapUV(mesh_storage.get_uv(damage_normal_uv_map_name, bpy_material.name))

        damage_normal_map_name: str = textures.damage_normal.texture.texture_name
        edm_damage_block.setNormalMap(damage_normal_map_name)

    damage_mask_name: str = textures.damage_mask.texture.texture_name
    edm_damage_block.setMaskRGBA(damage_mask_name)

    edm_damage_block.setArgument(edm_props.DAMAGE_ARG)

    return edm_damage_block

def make_def_bone_block(mesh_storage: MeshStorage) -> pyedm.BoneBlock:
    if not mesh_storage.armature:
        return None
    
    edm_bone_block = pyedm.BoneBlock()
    edm_bone_block.setBoneIndices(mesh_storage.bone_indices)
    edm_bone_block.setBoneWeights(mesh_storage.bone_weights)

    bone_names = list(mesh_storage.bones.items())
    bone_names.sort(key=lambda x : x[1])
    bone_names = [x[0] for x in bone_names]

    edm_bone_block.setBoneNames(bone_names)

    return edm_bone_block

def make_def_number_block(mesh_storage: MeshStorage, edm_props: EDMPropsGroup) -> pyedm.NumberBlock:
    ## read number type settings 
    if edm_props.SPECIAL_TYPE != 'NUMBER_TYPE':
        return None
    uv_x_arg = edm_props.NUMBER_UV_X_ARG
    uv_x_scale = edm_props.NUMBER_UV_X_SCALE
    uv_y_arg = edm_props.NUMBER_UV_Y_ARG
    uv_y_scale = edm_props.NUMBER_UV_Y_SCALE

    edm_number_block = pyedm.NumberBlock()
    edm_number_block.setUVParams(uv_x_arg, uv_x_scale, uv_y_arg, uv_y_scale)

    return edm_number_block

def add_block(edm_render_node: pyedm.PBRNode, block: pyedm.IBlock):
    if block is not None:
        edm_render_node.addBlock(block)
