from . import policy_registry
from .base import BasePolicy
import copy 
# 分组部分：选组（房型）
# 选择部分：按照项目，房子的顺序

@policy_registry.register("ver2")
class Ver2Policy(BasePolicy):
    log_fixed : dict = {} # tenant_id:{house_type_id, house_type_reason}
    
    def group(self,
              tenant,
            forum_manager, 
            system, 
            rule,
            tool, 
            log_round):
    
        choose_state, house_type_id, house_type_reason = tenant.choose_house_type(system,rule,log_round)

        self.log_fixed[tenant.id]={
            "choose_house_type":house_type_id,
            "choose_house_type_reason":house_type_reason
        }
        
        if not choose_state:
            tenant.update_times(choose_state)
            tenant.publish_forum(forum_manager,system,log_round)
            return "default" # belong to default queue
            
        return house_type_id # belong to group_id(house_type_id) queue
    
    def choose_pipeline(self,
                       tenant,
                       forum_manager, 
                        system, 
                        tool, 
                        rule,
                        log_round):
        
        log_round.init_log_round_from_dict(self.log_fixed[tenant.id])

        log_round.set_tenant_information(tenant.id,tenant.name,tenant.max_choose - tenant.choose_times)
            
        choose_state = False

        search_infos = tenant.search_forum(forum_manager=forum_manager,
                                         system=system,
                                         log_round=log_round)

        
        choose_state, community_id, community_choose_reason = tenant.choose_community(system,search_infos,rule,log_round)
        log_round.set_choose_community(community_id,community_choose_reason)

        
        if not choose_state:
            tenant.update_times(choose_state)
            tenant.publish_forum(forum_manager,system,log_round)
            return None 
        
        house_type_id,chose_house_type_reason = log_round.get_choose_house_type()
        house_filter_ids = {"house_type":house_type_id}
        
        
        for filter_label in self.filter_house_labels:
            if filter_label == "house_orientation":
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