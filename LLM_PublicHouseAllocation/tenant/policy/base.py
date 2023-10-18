from . import policy_registry
from pydantic import BaseModel
from abc import abstractmethod

@policy_registry.register("base")
class BasePolicy(BaseModel):
    
    filter_house_labels = [
                            "house_type",
                           "house_orientation",
                           "floor_type"]
    
    @abstractmethod
    async def choose_pipeline(self,
                       tenant,
                       forum_manager, 
                        system, 
                        tool, 
                        rule,
                        log_round):
        pass # return chooose_state, house_id.lower()
    
    @abstractmethod
    async def group(self,
                tenant,
                forum_manager, 
                system, 
                tool, 
                rule,
                log_round):
        pass # return group_id (community_id/house_type) or None (无法解析的group_id)