from . import group_registry
from .base import BaseGroupPolicy

@group_registry.register("house_type")
class HouseTypePolicy(BaseGroupPolicy):
    
    def __init__(self,**kargs) -> None:
        return super().__init__(type = "house_type",
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
        
        choose_state = False
        upper_bound = 3
        times = 0
        
        thought_hint = """Remember to consider the following things before choosing house:
1. The per capita living area should be taken into consideration.
2. Remember to give the reason why the selected house type meets your needs in thought(exp. \
My family has a large population and needs a larger house to live in)"""
        while not choose_state and \
            times < upper_bound:
            choose_state, house_type_id, house_type_reason = await tenant.choose_house_type(system,rule,thought_hint = thought_hint)
            log_round_tenant.set_choose_house_type(house_type_id,house_type_reason)
            self.log_fixed[tenant.id] = {
                "choose_house_type":house_type_id,
                "choose_house_type_reason": house_type_reason
            }
            times += 1
            
        if not choose_state:
            return "default"
        return house_type_id # belong to group_id(house_type_id) queue
            
    