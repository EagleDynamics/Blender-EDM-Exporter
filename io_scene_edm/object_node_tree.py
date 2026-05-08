from dataclasses import dataclass

from bpy.types import Context
from typing import Dict, List
from object_node import ObjectNode, LodRoot, LodLeaf, SceneRootNode
from collection_tree import CollectionTree, LodLeafCollectionNode, CollectionNodeCustomType
from logger import log
from utils import is_parent, is_list_unique_sub, get_not_unique_attr
import animation as anim

class ObjectNodeTree:
    def __init__(self, context: Context) -> None:
        self.objects: Dict[str, ObjectNode] = {}
        self.obj_tree: SceneRootNode = None
        self.context: Context = context
        self.collection_tree = CollectionTree(context)
        self.has_transform_anim = False

    def destroy(self):
        for key in self.objects:
            self.objects[key].destroy()
        self.obj_tree.destroy()        
        self.obj_tree = None

    def build_lods(self):
        @dataclass
        class LodLink:
            obj_wrp: ObjectNode
            collection_node: CollectionNodeCustomType

        def find_root(lod_name: str, lods_by_col: List[LodLink]):
            to_add = [x.obj_wrp for x in lods_by_col if type(x.obj_wrp.parent) is SceneRootNode]          
            
            for lod_link in lods_by_col:
                result = False
                for obj_node in to_add:
                    if lod_link.obj_wrp.name == obj_node.name:
                        result = True
                        break

                    if is_parent(lod_link.obj_wrp, obj_node):
                        result = True
                        break

                if not result:
                    log.fatal(f"Object {lod_link.obj_wrp.name} doesn't belong to lod {lod_name}.")
            return to_add

        lod_links: List[LodLink] = []

        # collect
        for obj_wrp in self.objects.values():
            if not obj_wrp.visible:
                continue
            
            ## sometimes it is possible to create object that visible, and parent of this object is not visible.
            ## that is why we need to check it before exporting
            if obj_wrp.parent is not None:
                if issubclass(type(obj_wrp.parent), ObjectNode):
                    if not obj_wrp.parent.visible:
                        log.error(
                        f"Error: object {obj_wrp.name} has parent {obj_wrp.parent.name} "  
                        f"that is part of invisible collection {obj_wrp.parent.obj.users_collection[0].name}.\n" 
                        f"Unparent {obj_wrp.name} from {obj_wrp.parent.name}.")
            
            if anim.get_animation_type(obj_wrp.obj) is not anim.Anim_Type.AT_NONE:
                self.has_transform_anim = True

            for bpy_collection in obj_wrp.obj.users_collection:
                parent_lod_col = self.collection_tree.collections.get(bpy_collection.name, None)
                
                while(type(parent_lod_col) != LodLeafCollectionNode and parent_lod_col.parent is not None):
                    parent_lod_col = parent_lod_col.parent
                
                if type(parent_lod_col) == LodLeafCollectionNode:
                    lod_links.append(LodLink(collection_node=parent_lod_col, obj_wrp=obj_wrp))

        # validate
        if not is_list_unique_sub(lod_links, 'obj_wrp', 'name'):
            log.fatal(f'Object {get_not_unique_attr(lod_links, "obj_wrp", "name")} is in multiple lods.')

        # split
        ParentName = str
        lods_by_groups: Dict[ParentName, Dict[str, List[LodLink]]] = {}
        for lod_link in lod_links:
            if not lod_link.collection_node.parent.name in lods_by_groups:
                lods_by_groups[lod_link.collection_node.parent.name] = {}

            lod_childs_dict = lods_by_groups[lod_link.collection_node.parent.name]
            if lod_link.collection_node.name in lod_childs_dict:
                lod_childs_dict[lod_link.collection_node.name].append(lod_link)
            else:
                lod_childs_dict[lod_link.collection_node.name] = [lod_link]
        
        # Check parent.
        for root_col_name, lods_by_col in lods_by_groups.items():
            parent_parent = None
            parents = []
            for lod_col_name, lod_col in lods_by_col.items():
                to_add = find_root(lod_col_name, lod_col)
                if not to_add:
                    log.fatal(f"Lod item {lod_col_name} is empty.")
                    return
                
                parent = None
                for i in to_add:
                    if not parent:
                        parent = i.parent
                    elif parent != i.parent:
                        log.fatal(f"Multiple parents of lod items. Expected {parent.name} got {i.parent.name}.")
                        return

                parent.remove_children(to_add)

                if not parent_parent:
                    parent_parent = parent.parent
                elif parent_parent != parent.parent:
                    log.fatal(f"Multiple parents of lod root. Expected {parent_parent.name} got {parent.parent.name}.")
                    return

                dist: float = self.collection_tree.collections[lod_col_name].lod.dist
                dummy = LodLeaf(dist)
                parent.add_child(dummy)
                dummy.add_children(to_add)

                parents.append(dummy)

            lod_root = LodRoot()
            if parent_parent:
                parent_parent.remove_children(parents)
                parent_parent.add_child(lod_root)
                lod_root.add_children(parents)
            else:
                self.obj_tree.remove_children(parents)
                lod_root.add_children(parents)
                self.obj_tree.add_child(lod_root)
                
    def build(self):
        self.obj_tree = SceneRootNode()
        # collect all objects
        for obj in self.context.scene.objects:
            self.objects[obj.name] = ObjectNode(obj)

        # build tree
        for obj in self.objects.values():
            if obj.obj.parent == None:
                self.obj_tree.add_child(obj)
            else:
                if obj.obj.parent.name not in self.objects:
                    log.error(f'Object "{obj.name}" has parent "{obj.obj.parent.name}" which is not in the current scene. To continue export please remove this parent.')
                else:
                    self.objects[obj.obj.parent.name].add_child(obj)

        # build collections
        self.collection_tree.build()
        
        # build visibility
        for obj_wrp in self.objects.values():
            for collection in obj_wrp.obj.users_collection:
                collection_wrp = self.collection_tree.collections.get(collection.name, None)
                if collection_wrp == None:
                    continue
                vis = collection_wrp.visible
                if vis:
                    obj_wrp.visible = True    

        self.build_lods()

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