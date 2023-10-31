from . import group_registry
from .base import BaseGroupPolicy

@group_registry.register("community")
class CommunityPolicy(BaseGroupPolicy):
    
    def __init__(self,**kargs) -> None:
        super().__init__(policy_type="community",
                         **kargs)

    
    async def group(self,
                tenant,
                forum_manager, 
                system, 
                tool, 
                rule,
                log_round_tenant):
        
        search_infos = tenant.search_forum(forum_manager=forum_manager,
                                         system=system)

        
        choose_state, community_id, community_choose_reason = await tenant.choose_community(system,search_infos,rule)

        self.log_fixed[tenant.id]={
            "choose_community_id":community_id,
            "choose_community_reason":community_choose_reason
        }
        
        if not choose_state:
            tenant.update_times(choose_state)
            await tenant.publish_forum(forum_manager,system)
            return "default"
        
        return community_id
        
    