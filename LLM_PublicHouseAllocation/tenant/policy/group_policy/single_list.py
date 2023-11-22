from . import group_registry
from .base import BaseGroupPolicy

@group_registry.register("single_list")
class SingleListPolicy(BaseGroupPolicy):
    
    
    def __init__(self,**kargs) -> None:
        return super().__init__(type = "single_list",
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
        
        return "default"
        
    