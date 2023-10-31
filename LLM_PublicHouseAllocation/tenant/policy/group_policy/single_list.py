from . import group_registry
from .base import BaseGroupPolicy

@group_registry.register("single_list")
class SingleListPolicy(BaseGroupPolicy):
    
    def __init__(self,**kargs) -> None:
        super().__init__(policy_type="single_list",
                         **kargs)
    
    async def group(self,
                tenant,
                forum_manager, 
                system, 
                tool, 
                rule,
                log_round_tenant):
        
        return "default"
        
    