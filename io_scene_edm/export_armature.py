import re
from enum import Enum
import bpy

from pyedm_platform_selector import pyedm
from logger import log
from tree_node import TreeNode
from animation import has_transform_anim, extract_transform_anim, get_animation_type, AllowedAnimationsEnum, Anim_Type
from math_tools import IDENTITY_MATRIX, ROOT_TRANSFORM_MATRIX, RIGHT_TRANSFORM_MATRIX

def build_bone_id(armature_name, bone_name):
    return f'{armature_name} : {bone_name}'

bone_path_re_c = re.compile(r'.*\["(.*)"\]\.(.*)')
def split_data_path(data_path):
    m = re.match(bone_path_re_c, data_path)
    if not m:
        return (None, data_path)
    return (m.group(1), m.group(2))

class BoneNode(TreeNode):
    def __init__(self, pbone: bpy.types.PoseBone, armature: bpy.types.Armature) -> None:
        super().__init__()
        self.name = build_bone_id(armature.name, pbone.name)
        self.armature = armature
        self.pbone = pbone
        self.bone = pbone.bone # rest bone
        self.edm_node = None
        self.update_matrices()

    def build_bones(self, parent: pyedm.Node):
        self.edm_node = extract_bone_animation(parent, self)
        for i in self.children:
            i.build_bones(self.edm_node)

    def update_matrices(self):
        if self.bone.parent:
            self.mat = self.bone.parent.matrix_local.inverted() @ self.bone.matrix_local
            self.mat_inv = self.mat.inverted()
            #self.mat_inv = (self.bone.matrix_local).inverted()
        else:
            self.mat = self.bone.matrix_local
            self.mat_inv = (self.bone.matrix_local).inverted()

        if self.pbone.parent:
            self.pmat = self.pbone.parent.matrix.inverted() @ self.pbone.matrix
        else:
            self.pmat = self.pbone.matrix
        self.mat_inv = (self.pbone.matrix).inverted()
        

# allowed_args == None means any args are allowed
def extract_bone_animation(parent: pyedm.Node, bone: BoneNode, allowed_args=None):
   
    anim_type = get_animation_type(bone.armature, lambda x: split_data_path(x)[1])
    if anim_type is Anim_Type.AT_NONE:
        parent = parent.addChild(pyedm.Bone(bone.name, bone.pmat, bone.mat_inv))
        return parent
    
    class DPE:
        LOCATION        = 'pose.bones["' + bone.bone.name + '"].location'
        ROTATION_QUAT   = 'pose.bones["' + bone.bone.name + '"].rotation_quaternion'
        ROTATION_EULER  = 'pose.bones["' + bone.bone.name + '"].rotation_euler'
        SCALE           = 'pose.bones["' + bone.bone.name + '"].scale'

    a = extract_transform_anim(parent, bone.armature, bone.armature.animation_data.action, bone.mat,
                               bone.armature.matrix_local, bone.name, anim_type,
                               AllowedAnimationsEnum.ALL, DPE, allowed_args, bone=bone)

    a = a.addChild(pyedm.Bone(bone.name, IDENTITY_MATRIX, bone.mat_inv))
    
    return a

# we need to build tree because blender holds bones in a flat list
def build_bones_tree(parent, bones_list, armature):
    bones = [BoneNode(b, armature) for b in bones_list]

    for b in bones:
        for c in b.pbone.children:
            for bb in bones:
                if c == bb.pbone:
                    b.add_child(bb)
                    break

    roots = [b for b in bones if b.parent == None]

    for r in roots:
        r.build_bones(parent)

    return bones

def export_armature(armature, parent, bones_dict):
    # Pose bones contain pose data for the current frame, while regular bone objects store the default state of the bone.
    pose_bones = armature.pose.bones
    if not pose_bones:
        log.warning(f'Armature {armature.name} is empty')
        return
    

    #root = pyedm.Node(f'Armature {armature.name} Root')
    #root = pyedm.Transform(f'Armature {armature.name} Root', armature.matrix_local)
    #parent = parent.addChild(root)
    
    bone_nodes = build_bones_tree(parent, pose_bones, armature)
    
    bones_dict.update({(x.name, x) for x in bone_nodes})
    
    return parent
