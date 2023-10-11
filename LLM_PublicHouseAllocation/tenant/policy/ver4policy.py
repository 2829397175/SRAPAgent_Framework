from . import policy_registry
from .base import BasePolicy

# not used ,remain to be modified
@policy_registry.register("ver1")
class Ver1Policy(BasePolicy):

    
    def group(self, tenant, forum_manager, system, tool, rule, log_round):
        return "default"
    
    def choose_pipeline(self,
                       tenant,
                       forum_manager, 
                        system, 
                        tool, 
                        rule,
                        log_round):
        
        log_round.set_tenant_information(tenant.id,tenant.name,tenant.max_choose - tenant.choose_times)
        search_infos = tenant.search_forum(forum_manager=forum_manager,
                                         system=system,
                                         log_round=log_round)


        choose_state, community_id, community_choose_reason = tenant.choose_community(system,search_infos,rule,log_round)
        log_round.set_choose_community(community_id,community_choose_reason)
        
        if not choose_state:
            tenant.update_times(choose_state)
            tenant.publish_forum(forum_manager,system,log_round)
            return False,"None"
        
        house_filter_ids = {}
        for filter_label in self.filter_house_labels:
            if filter_label == "house_type":
                choose_state, house_type_id, house_type_reason = tenant.choose_house_type(system,rule,log_round,community_id)
                log_round.set_choose_house_type(house_type_id,house_type_reason)
                house_filter_ids["house_type"] = house_type_id
                
            elif filter_label == "house_orientation":
                choose_state, filter_id, reason = tenant.choose_orientation(system,rule,log_round,community_id)
                log_round.set_choose_house_orientation(filter_id, reason)
                house_filter_ids["house_orientation"] = filter_id
                
            elif filter_label == "floor_type":
                choose_state, filter_id, reason = tenant.choose_floor(system,rule,log_round,community_id)
                log_round.set_choose_floor_type(filter_id, reason)
                house_filter_ids["floor_type"] = filter_id
            else:
                assert NotImplementedError
                
            if not choose_state:
                tenant.update_times(choose_state)
                tenant.publish_forum(forum_manager,system,log_round)
                return False,"None"
        
            
        choose_state, house_id, house_choose_reason = tenant.choose_house(
                                                   system,
                                                   community_id,
                                                   house_filter_ids,
                                                   log_round)

        log_round.set_choose_house(house_id,house_choose_reason)
        
        tenant.publish_forum(system=system,
                           forum_manager=forum_manager,
                           log_round=log_round)
        # 更改tenant 的选择状态
        tenant.update_times(choose_state)
             
        if not choose_state:
            return False,"None"
        
        # 更改communitymanager中的remain_num
        system.set_chosed_house(house_id,community_id,house_filter_ids)

        return True,house_id.lower()