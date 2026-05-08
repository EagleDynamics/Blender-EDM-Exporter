import bpy
from typing import List
from bpy.types import Mesh, Object, ObjectModifiers
import numpy as np
from logger import log

from mesh_storage import MeshStorage
from version_specific import BLENDER_RELEASE, BLENDER_41

def get_mesh(obj: Object) -> Mesh:
    if obj.data.is_editmode:
        #obj.update_from_editmode()
        log.fatal('Can not export from edit mode.')

    modifiers: ObjectModifiers = obj.modifiers
    if not modifiers: # If no modifier, use original mesh, it will instance all shared mesh in a single mesh
        if isinstance(obj.data, Mesh):
            bpy_mesh: Mesh = obj.data
        else:
            bpy_mesh: Mesh = obj.to_mesh()
    else:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        blender_mesh_owner = obj.evaluated_get(depsgraph)
        bpy_mesh: Mesh = blender_mesh_owner.to_mesh(preserve_all_data_layers = True, depsgraph = depsgraph)
        for prop in obj.data.keys():

            ## It is highly likely that obj has 'hops' property, because HardOps addon added this property.
            ## While exporting model to .edm we do not care about this property, so we can easily skip it.
            ## see https://jira.dcs.dev/browse/DCSTOOLS-894
            if prop == 'hops':
                continue
            bpy_mesh[prop] = obj.data[prop]
    
    return bpy_mesh

def buld_mesh(obj: Object, armature) -> List[MeshStorage]:
    bpy_mesh = get_mesh(obj)

    bpy_mesh.calc_loop_triangles()
    if BLENDER_RELEASE < BLENDER_41:
        bpy_mesh.calc_normals_split()

    nTriangles = len(bpy_mesh.loop_triangles)
    nLoops = len(bpy_mesh.loops)

    mat_inds = np.empty(nTriangles, dtype=np.uint32)
    bpy_mesh.loop_triangles.foreach_get('material_index', mat_inds)
    uniq_mat_inds = np.unique(mat_inds)
    mat_ind_to_ind = {x: i for i, x in enumerate(uniq_mat_inds)}

    vertices = np.empty(len(bpy_mesh.vertices) * 3, dtype=np.float32)
    bpy_mesh.vertices.foreach_get('co', vertices)
    
    vertices_indices = np.empty(nLoops, dtype=np.uint32)
    bpy_mesh.loops.foreach_get('vertex_index', vertices_indices)
    vertices_indices *= 3

    normals = np.empty(nLoops * 3, dtype=np.float32)
    bpy_mesh.loops.foreach_get('normal', normals)

    uvs = {}
    for uv_name, uv_loop in bpy_mesh.uv_layers.items():
        if len(uv_loop.uv) == 0:
            uvs[uv_name] = np.array([], dtype=np.float32)
            continue
        buf = np.empty(nLoops * 2, dtype=np.float32)
        uv_loop.uv.foreach_get('vector', buf)
        buf[1::2] *= -1.0
        uvs[uv_name] = buf

    if bpy_mesh.uv_layers:
        uv_active = bpy_mesh.uv_layers[0].name
    else:
        uv_active = None

    bverts = bpy_mesh.vertices
    meshes = [MeshStorage(nTriangles, bpy_mesh.uv_layers.keys(), uv_active, x, armature) for x in uniq_mat_inds]
    for mesh in meshes:
        mesh.prepare(vertices, bverts, obj, normals, uvs, vertices_indices)

    for ti, triangle in enumerate(bpy_mesh.loop_triangles):
        mat_ind = mat_inds[ti]
        meshes[mat_ind_to_ind[mat_ind]].set(triangle.loops)

    for m in meshes:
        m.shrink()

    return meshes
