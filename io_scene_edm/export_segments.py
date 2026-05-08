import bpy
import numpy as np

from logger import log
from enums import ObjectTypeEnum
from mesh_builder import get_mesh
from pyedm_platform_selector import pyedm
from objects_custom_props import get_edm_props

## check if object is segment
def is_segment(object: bpy.types.Object) -> bool:
    edm_props = get_edm_props(object)
    if object.type in (ObjectTypeEnum.MESH, ObjectTypeEnum.CURVE, ObjectTypeEnum.CURVES) and edm_props.SPECIAL_TYPE in ('COLLISION_LINE'):
        return True
    return False

## from Blender-type object create and return segments that can be exported to EDM.
def create_segments_node(o: bpy.types.Object, name: str, control_node: pyedm.Node) -> pyedm.SegmentsNode:
    bpy_mesh = get_mesh(o)
    segment_node = pyedm.SegmentsNode(name)
    
    # constants
    dim = 3 # 3D dimention
    points_count = 2 # one segment is described by 2 points
    vert_count = len(bpy_mesh.vertices)
    edge_count = len(bpy_mesh.edges)

    #parse coordinates
    vertices = np.empty(vert_count * dim, dtype=np.float32)
    bpy_mesh.vertices.foreach_get('co', vertices)    
    # foreach_get() method returns flatted array.
    # we need to reshape it to array which contains list of vertex coordinates (x, y, z)
    vertices = np.reshape(vertices, (vert_count, dim), order='C').tolist()

    # parse edges
    edges = np.empty(edge_count * points_count, dtype=np.int32)
    bpy_mesh.edges.foreach_get('vertices', edges)
    edges = np.reshape(edges, (edge_count, points_count), order='C').tolist()

    #make list of segments
    segments = [(vertices[p1], vertices[p2]) for p1, p2 in edges]

    segment_node.set(segments)
    segment_node.setControlNode(control_node)
    
    return segment_node


