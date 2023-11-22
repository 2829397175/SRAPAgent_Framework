from . import group_registry
from .base import BaseGroupPolicy

@group_registry.register("multi_list")
class MultiListPolicy(BaseGroupPolicy):
    
    def __init__(self,**kargs) -> None:
        return super().__init__(type = "multi_list",
                                **kargs)
    
    async def group(self,
                tenant,
                tenant_manager,
                forum_manager, 
                system, 
                tool, 
                rule,
                log_round_tenant,
                tenant_ids):
        
        if tenant.family_num>2:
            return  "large_house"
        elif tenant.family_num==2: 
            return "middle_house"
        else:
            return "small_house"
        
    