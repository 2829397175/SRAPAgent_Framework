        log_round.set_tenant_information(tenant.id,tenant.name,tenant.max_choose - tenant.choose_times)
        # log_round["tenant_id"] = tenant.id
        # log_round["tenant_name"] = tenant.name
        # log_round["available_times"] = tenant.max_choose - tenant.choose_times
            
        choose_state = False
        # search_forum test
        # search_infos = tenant.search_forum(tool,log_round)
        search_infos = tenant.search_forum(forum_manager=forum_manager,
                                         system=system,
                                         log_round=log_round)

        
        choose_state, community_id, community_choose_reason = tenant.choose_community(system,search_infos,rule,log_round)
        log_round.set_choose_community(community_id,community_choose_reason)
        # log_round["choose_community_id"] = community_id
        # log_round["choose_community_reason"] = community_choose_reason
        
        if not choose_state:
            tenant.update_times(choose_state)
            tenant.publish_forum(forum_manager,system,log_round)
            return False,"None"
        
        # test
        # tenant.access_forum(tenant_id=tenant_id)
        
        choose_state, house_type_id, house_type_reason = tenant.choose_house_type(system,community_id,rule,log_round)
        # log_round["choose_house_type"] = house_type_id
        # log_round["choose_house_type_reason"] = house_type_reason
        log_round.set_choose_house_type(house_type_id,house_type_reason)
        if not choose_state:
            tenant.update_times(choose_state)
            tenant.publish_forum(forum_manager,system,log_round)
            return False,"None"
        
        if not isinstance(house_type_id,list):
            house_filter_ids = [house_type_id] #这里存储 某个community中的，某些类型的房子
        else:
            house_filter_ids = house_type_id
            
            
       
            
        choose_state, house_id, house_choose_reason = tenant.choose_house(
                                                   system,
                                                   community_id,
                                                   house_filter_ids,
                                                   log_round)
        
        # log_round["choose_house_id"] = house_id
        # log_round["choose_house_reason"] = house_choose_reason
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