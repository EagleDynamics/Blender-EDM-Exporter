import sys
from typing import List, Tuple
from math import sqrt
from mathutils import Euler, Matrix, Vector
import bpy

ZERO_VEC3 = Vector([0, 0, 0])
ZERO_VEC4 = Vector([0, 0, 0, 0])

RIGHT_TRANSFORM_MATRIX = Matrix((
    (-1.0,  0.0,  0.0,  0.0),
    ( 0.0,  0.0, -1.0,  0.0),
    ( 0.0,  1.0,  0.0,  0.0),
    ( 0.0,  0.0,  0.0,  1.0)
))

if 1:
    ROOT_TRANSFORM_MATRIX = Matrix((
        ( 1.0,  0.0,  0.0,  0.0),
        ( 0.0,  0.0,  1.0,  0.0),
        ( 0.0, -1.0,  0.0,  0.0),
        ( 0.0,  0.0,  0.0,  1.0)
    ))
else:
    ROOT_TRANSFORM_MATRIX = Matrix((
        ( 1.0,  0.0,  0.0,  0.0),
        ( 0.0,  1.0,  0.0,  0.0),
        ( 0.0,  0.0,  1.0,  0.0),
        ( 0.0,  0.0,  0.0,  1.0)
    ))

IDENTITY_MATRIX = Matrix((
    ( 1.0,  0.0,  0.0,  0.0),
    ( 0.0,  1.0,  0.0,  0.0),
    ( 0.0,  0.0,  1.0,  0.0),
    ( 0.0,  0.0,  0.0,  1.0)
))

def length2(v4):
    l = v4[0] * v4[0] + v4[1] * v4[1] + v4[2] * v4[2] + v4[3] * v4[3]
    return l

# Probabilistic normalization (sum normalization)
def normalize_L1(v4):
    total = v4[0] + v4[1] + v4[2] + v4[3] 
    eps = 0.0001
    
    # already normalized
    if abs(total - 1.) < eps:
        return
    
    v4[0] /= total
    v4[1] /= total
    v4[2] /= total
    v4[3] /= total

def euler_to_quat(euler):
    eul = Euler(euler, 'XYZ')
    q = eul.to_quaternion()
    return q

def get_max(vecs : List[Vector]):
    max_x = max_y = max_z = sys.float_info.min
    for v in vecs:
        if v.x > max_x:
           max_x = v.x
        if v.y > max_y:
           max_y = v.y
        if v.z > max_z:
           max_z = v.z
    return (max_x, max_y, max_z)

def get_min(vecs : List[Vector]):
    min_x = min_y = min_z = sys.float_info.max
    for v in vecs:
        if v.x < min_x:
           min_x = v.x
        if v.y < min_y:
           min_y = v.y
        if v.z < min_z:
           min_z = v.z
    return (min_x, min_y, min_z)

## this method returns bbox coordinates as two points (x1, y1, z1, x2, y2, z2)
def get_aa_bb(object: bpy.types.Object) -> Tuple[float, float, float, float, float, float]:    
    mat = ROOT_TRANSFORM_MATRIX @ object.matrix_world
    vecs: List[Vector] = []
    for i in (-1.0, 1.0):
        for j in (-1.0, 1.0):
            for k in (-1.0, 1.0):
                vec = mat @ Vector((i, j, k))
                vecs.append(vec)
        
    vec1 = Vector(get_min(vecs))
    vec2 = Vector(get_max(vecs))

    return (vec1.x, vec1.y, vec1.z, vec2.x, vec2.y, vec2.z)
