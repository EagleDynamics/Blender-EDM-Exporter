from typing import Dict, Union

from bpy.types import Collection, Context, LayerCollection

from tree_node import TreeNode
from utils import Lod, extract_lod


class CollectionNode(TreeNode):
    def __init__(self, col: Collection) -> None:
        super().__init__()
        self.col = col
        self.name: str = col.name
        self.visible = True


class LodLeafCollectionNode(CollectionNode):
    def __init__(self, col: Collection, lod: Lod) -> None:
        super().__init__(col)
        self.lod: Lod = lod


class CollectionRootNode(CollectionNode):
    def __init__(self, col: Collection) -> None:
        super().__init__(col)

CollectionNodeCustomType = Union[TreeNode, CollectionNode, LodLeafCollectionNode, CollectionRootNode]

class CollectionTree:
    def __init__(self, context: Context) -> None:
        self.collections: Dict[str, CollectionNodeCustomType] = {}
        self.col_tree: CollectionRootNode = None
        self.context: Context = context

    def build(self):
        self.col_tree = CollectionRootNode(self.context.scene.collection)
        self.collections[self.col_tree.col.name] = self.col_tree

        # collect all collections
        def walk(collection: Collection, parent_col_wrap: CollectionNodeCustomType):
            lod: Lod | None = extract_lod(collection.name)
            if lod is None:
                collection_node = CollectionNode(collection)
            else:
                collection_node = LodLeafCollectionNode(collection, lod)

            self.collections[collection_node.name] = collection_node
            parent_col_wrap.add_child(collection_node)

            for child in collection.children:
                walk(child, collection_node)

        #walk(self.context.scene.collection, self.col_tree)
        for child in self.col_tree.col.children:
            walk(child, self.col_tree)

        # set visibility
        def walk_view_layer(col: LayerCollection):
            if not col.visible_get():
                self.collections[col.collection.name].visible = False
            for child in col.children:
                walk_view_layer(child)

        walk_view_layer(self.context.view_layer.layer_collection)

    def dump(self):
        o = 'graph {\n'
        
        def walk(obj):
            nonlocal o
            if obj.parent == None:
                o += f'\tROOT -- "{obj.name}"\n'
            else:
                o += f'\t"{obj.parent.name}" -- "{obj.name}"\n'
        
            for i in obj.children:
                walk(i)

        walk(self.obj_tree)

        o += '}'
        return o