
from pydantic import BaseModel
from abc import abstractmethod
from . import readcommunity_registry as ReadCommunityRgistry
from typing import List

@ReadCommunityRgistry.register("base")
class Base_ReadCommunity(BaseModel):
    @abstractmethod
    
    def read_community_list(self,
                            community_data,
                            community_ids:List[str] = None):
        pass