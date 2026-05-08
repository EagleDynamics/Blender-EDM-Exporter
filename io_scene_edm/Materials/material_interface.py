from typing import List, Dict
from abc import ABC, abstractmethod

from bpy.types import (
    Object, 
    ShaderNodeGroup, 
)

from mesh_storage import MeshStorage
from serializer import SLink
from socket_types import SInput
from pyedm_platform_selector import pyedm

## base material class 
class IMaterial(ABC):
    """
    Common abstract class for all types of materials.
    """

    ## Material name. Now supported 4 materials: Deck, Default, Fake_Spot, Fake_Omni
    name: str = NotImplemented
    ## Relative path to .pickle file of serialised material.
    description_file_name: str = NotImplemented
    ## name of node group
    node_group_name: str = NotImplemented
 
    @abstractmethod
    def build_blocks(self, obj: Object, storage: MeshStorage) -> pyedm.IRenderNode:
        """
        Create render node that can be imported to edm. 
        Once 'pyedm.IRenderNode' was created, you need to set control node to it and add render node to model. 
        """
        pass

    #TODO-270 - add description for methods  
    @classmethod
    @abstractmethod
    def process_links(cls, links: List[SLink], version: int, group_node_type_name: str)-> List[SLink]:
        pass

    @classmethod
    @abstractmethod
	## drop_down_values - dict where 'key' - name of attribute, 'value' - current value of drop-down list.
    def restore_defaults(cls, old_sockest: List[SInput], 
                         new_node_group: ShaderNodeGroup, drop_down_values: Dict[str, str], old_version: int, material_name: str) -> None:
        pass
