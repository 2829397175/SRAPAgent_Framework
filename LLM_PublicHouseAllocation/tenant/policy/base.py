from . import policy_registry
from abc import abstractmethod
from .group_policy import BaseGroupPolicy
from pydantic import BaseModel

@policy_registry.register("base")
class BasePolicy(BaseModel):
    filter_house_labels :list = ["house_type",
                           "house_orientation",
                           "floor_type"]
    
    group_policy:BaseGroupPolicy
    
    type = "base"
    # def __init__(self, **kwargs):
    #     self.filter_house_labels = ["house_type",
    #                        "house_orientation",
    #                        "floor_type"]
        
    #     for k,v in kwargs.items():
    #         self.__setattr__(k,v)
    
    @abstractmethod
    async def choose_pipeline(self,
                       tenant,
                       forum_manager, 
                        system, 
                        tool, 
                        rule,
                        log_round_tenant):
        pass # return chooose_state, house_id.lower()
    
    async def group(self, 
                    tenant,
                    tenant_manager,
                    forum_manager, 
                    system, 
                    tool, 
                    rule,
                    log_round_tenant,
                    tenant_ids):
        return await self.group_policy.group(
                    tenant,
                    tenant_manager,
                    forum_manager, 
                    system, 
                    tool, 
                    rule,
                    log_round_tenant,
                    tenant_ids)
                    