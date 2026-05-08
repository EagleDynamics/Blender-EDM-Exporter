import numpy as np
from export_armature import build_bone_id
from logger import log
import utils
from math_tools import normalize_L1

def get_armature_from_modifiers(modifiers):
    if not modifiers:
        return False
    
    m = modifiers.get('Armature')
    if m and m.name == 'Armature':
        return m.object
    return False

def get_common_dmg_arg(dmg_list):
    for i in dmg_list[0]:
        if i in dmg_list[1] and i in dmg_list[2]:
            return i
    return -1

class MeshStorage:
    def __init__(self, nTriangles, uvNames, uv_active, material_index, armature) -> None:
        self.cur = 0
        self.nVerts = 0
        self.material_index = material_index
        self.armature = armature
        self.nTriangles = nTriangles
        self.positions = np.empty(nTriangles * 9, dtype=np.float32)
        self.normals = np.empty(nTriangles * 9, dtype=np.float32)
        self.indices = np.empty(nTriangles * 3, dtype=np.uint32)
        self.indices_map = {}
        self.uv_active = uv_active
        self.uv = {name: np.empty(nTriangles * 6, dtype=np.float32) for name in uvNames}

        self.bones = {}
        self.bone_indices = np.empty(nTriangles * 12, dtype=np.uint32)
        self.bone_weights = np.empty(nTriangles * 12, dtype=np.float32)
        self.damage_arguments = np.empty(nTriangles * 3, dtype=np.float32)
        self.cur_bone_index = 0
        self.armature = []
        self.bone_names = []
        self.has_dmg_group = False

    def get_uv(self, uv_name, material_name):
        if uv_name in self.uv:
            return self.uv[uv_name]
        else:
            log.fatal(f"Error. There is no such uv={uv_name} in material={material_name}")

    def prepare(self, vertices, bverts, obj, orig_normals, orig_uvs, vertices_indices):
        self.vertices = vertices
        self.bverts = bverts

        self.vertex_group_names = [[x.name, utils.get_dmg_vert_group_arg(x.name)] for x in obj.vertex_groups]
            
        self.orig_normals = orig_normals
        self.orig_uvs = orig_uvs
        self.vertices_indices = vertices_indices
        self.armature = get_armature_from_modifiers(obj.modifiers)
        if self.armature:
            self.bone_names = [x.name for x in self.armature.pose.bones]
        else:
            self.bone_names = []

    def set(self, loops):
        dmg = [[], [], []]
        for i, index in enumerate(loops):
            vertex_index = self.vertices_indices[index]
            vgroups = self.bverts[vertex_index // 3].groups
            for gr in vgroups:
                vg_name = self.vertex_group_names[gr.group]
                if vg_name[1] >= 0:
                    dmg[i].append(vg_name[1])
        
        dmg_arg = get_common_dmg_arg(dmg)
        if dmg_arg >= 0:
            self.has_dmg_group = True

        for index in loops:
            vertex_index = self.vertices_indices[index]

            # check if vertex was already processed.
            if (vertex_index, index, dmg_arg) in self.indices_map:
                i = self.indices_map[(vertex_index, index, dmg_arg)]
                self.indices[self.cur] = i
                self.cur += 1
                continue

            # sort bones, damage and other groups
            vgroups = self.bverts[vertex_index // 3].groups
            bones_groups = []
            for gr in vgroups:
                vg_name = self.vertex_group_names[gr.group][0]
                if vg_name in self.bone_names and gr.weight >= 1.0e-3:
                    bones_groups.append(gr)

            self.damage_arguments[self.nVerts] = dmg_arg
                
            if len(bones_groups) > 4:
                log.fatal("Skin vertex has more than 4 infuencing bones.")

            if bones_groups:
                weights_temp = [0.0, 0.0, 0.0, 0.0]
                temp_inds = [0, 0, 0, 0]
                for i, gr in enumerate(bones_groups):
                    bone_name = build_bone_id(self.armature.name, self.vertex_group_names[gr.group][0])
                    if bone_name not in self.bones:
                        ind = self.cur_bone_index
                        self.bones[bone_name] = ind
                        self.cur_bone_index += 1
                    else:
                        ind = self.bones[bone_name]
                    
                    weights_temp[i] = gr.weight
                    temp_inds[i] = ind
                
                normalize_L1(weights_temp)
                c = self.nVerts * 4
                self.bone_indices[c : c + 4] = temp_inds
                self.bone_weights[c : c + 4] = weights_temp
            elif self.armature:
                c = self.nVerts * 4
                self.bone_indices[c : c + 4] = [0.0, 0.0, 0.0, 0.0]
                self.bone_weights[c : c + 4] = [0, 0, 0, 0]
            
            i = len(self.indices_map)
            self.indices_map[(vertex_index, index, dmg_arg)] = i
            self.indices[self.cur] = i

            c = self.nVerts * 3
            self.positions[c : c + 3] = self.vertices[vertex_index : vertex_index + 3]
            self.normals[c : c + 3] = self.orig_normals[index * 3 : index * 3 + 3]

            c = self.nVerts * 2
            for k in self.orig_uvs.keys():
                #self.uv[k][c : c + 2] = self.orig_uvs[k][index * 2 : index * 2 + 2]
                if not len(self.orig_uvs[k]) == 0:
                    self.uv[k][c : c + 2] = self.orig_uvs[k][index * 2 : index * 2 + 2]
                else:
                    self.uv[k][c : c + 2] = 0.0
            self.cur += 1
            self.nVerts += 1

    def shrink(self):
        self.nTriangles = self.cur // 3
        self.positions = self.positions[:self.nVerts * 3]
        self.normals = self.normals[:self.nVerts * 3]
        self.indices = self.indices[:self.nTriangles * 3]
        self.bone_indices = self.bone_indices[:self.nVerts * 4]
        self.bone_weights = self.bone_weights[:self.nVerts * 4]
        self.damage_arguments = self.damage_arguments[:self.nVerts]
        for k in self.uv.keys():
            self.uv[k] = self.uv[k][:self.nVerts * 2]