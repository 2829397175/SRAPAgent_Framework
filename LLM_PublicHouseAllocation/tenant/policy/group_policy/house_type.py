from . import group_registry
from .base import BaseGroupPolicy

@group_registry.register("house_type")
class HouseTypePolicy(BaseGroupPolicy):
    
    
    
    async def group(self,
                tenant,
                forum_manager, 
                system, 
                tool, 
                rule,
                log_round_tenant):
        
        choose_state = False
        upper_bound = 3
        times = 0
        while not choose_state and \
            times < upper_bound:
            choose_state, house_type_id, house_type_reason = await tenant.choose_house_type(system,rule)
            log_round_tenant.set_choose_house_type(house_type_id,house_type_reason)
            self.log_fixed[tenant.id] = {
                "choose_house_type":house_type_id,
                "choose_house_type_reason": house_type_reason
            }
            times += 1
            
        if not choose_state:
            return "default"
        return house_type_id # belong to group_id(house_type_id) queue
            
    