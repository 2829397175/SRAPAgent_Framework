from . import group_registry
from pydantic import BaseModel
from abc import abstractmethod

@group_registry.register("base")
class BaseGroupPolicy(BaseModel):
    
    priority:bool = False
    log_fixed = {} # fixed_log for tenants : tenant_id[house_type_id,house_choose_reason]
    async def group(self,
                tenant,
                forum_manager, 
                system, 
                tool, 
                rule,
                log_round_tenant):
        # return group_id
        return "default" # 所有tenant分在同一组
    