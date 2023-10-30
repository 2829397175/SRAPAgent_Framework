from . import group_registry
from .base import BaseGroupPolicy

@group_registry.register("single_list")
class SingleListPolicy(BaseGroupPolicy):
    
    
    async def group(self,
                tenant,
                forum_manager, 
                system, 
                tool, 
                rule,
                log_round_tenant):
        
        return "default"
        
    