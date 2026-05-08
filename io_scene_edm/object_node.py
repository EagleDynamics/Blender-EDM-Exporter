from bpy.types import Object
from tree_node import TreeNode
from typing import Union

class ObjectNode(TreeNode):
    def __init__(self, obj: Object) -> None:
        super().__init__()
        self.obj: Object = obj
        self.name: str = obj.name
        self.visible: bool = False

class LodRoot(TreeNode):
    def __init__(self) -> None:
        super().__init__()
        self.name = '_LodRoot_'

class LodLeaf(TreeNode):
    def __init__(self, dist) -> None:
        super().__init__()
        self.name = '_LodLeaf_'
        self.dist = dist

class DummyNode(TreeNode):
    def __init__(self) -> None:
        super().__init__()
        self.name = '_Dummy_'

class SceneRootNode(TreeNode):
    def __init__(self) -> None:
        super().__init__()
        self.name = '_SceneRoot_'

ObjectNodeCustomType = Union[TreeNode, ObjectNode, LodRoot, LodLeaf, DummyNode, SceneRootNode]