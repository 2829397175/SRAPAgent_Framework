from LLM_PublicHouseAllocation.manager import HouseManager,CommunityManager
from pydantic import BaseModel
from typing import List
from LLM_PublicHouseAllocation.tenant.langchain_tenant import LangchainTenant
from LLM_PublicHouseAllocation.environments.rules import Rule
class System(BaseModel):
   
    house_manager:HouseManager
    community_manager:CommunityManager
    
    def reset(self):
        pass
    
    def set_chosed_house(self,house_id,community_id,house_filter_ids:List):
        self.community_manager.set_chosed_house(house_id,community_id,house_filter_ids)
        self.house_manager.set_chosed_house(house_id)
        self.community_manager.save_data()
        self.house_manager.save_data()
    
    def available_house_num(self):
        return self.house_manager.available_house_num()
    
    def get_community_abstract(self,rule=None,tenant=None):
        if isinstance(rule,Rule) and isinstance(tenant,LangchainTenant):
            community_list=self.community_manager.get_available_community_info()
            filter_community_list=rule.filter_community(tenant,community_list)
            community_str,_=self.community_manager.community_str(filter_community_list,[])
            community_ids = [d["community_id"] for d in filter_community_list if "community_id" in d]
            return community_str,community_ids
        else:
            community_list=self.community_manager.get_available_community_info()
            community_str,_=self.community_manager.community_str(community_list,[])
            return community_str
        
    
    def get_split_community_abstract(self):
        community_list=self.community_manager.get_available_community_info()
        curcommunity_list,furcommunity_list=self.community_manager.split(community_list)
        curstr,furstr=self.community_manager.community_str(curcommunity_list,furcommunity_list)
        return curstr,furstr
        
        
    def get_house_type(self,community_id,rule=None,tenant=None):
        if isinstance(rule,Rule) and isinstance(tenant,LangchainTenant):
            house_types = self.community_manager.get_available_house_type(community_id)
            filter_house_types=rule.filter_housetype(tenant,house_types)
            return self.community_manager.get_house_type(community_id,filter_house_types),filter_house_types
        else:
            house_types = self.community_manager.get_available_house_type(community_id)
            return self.community_manager.get_house_type(community_id,house_types)
    
    def get_filtered_houses_ids(self,community_id,house_filter_ids:list):
        house_ids = self.community_manager.get_filtered_house_ids(
            community_id=community_id,
            house_filter_ids=house_filter_ids
        )
        return house_ids
    
    
    def get_house_dark_info(self,house_id):
        dark_info=""
        if house_id in self.house_manager.data.keys():
            dark_info=self.house_manager.data[house_id].get("potential_information_house","")
        return dark_info
    
    def get_community_data(self):
        return self.community_manager.data
    
    def jug_community_valid(self,community_id,community_ids):
        return self.community_manager.jug_community_valid(community_id.lower(),community_ids)
    
    def get_available_house_type(self,community_id):
        return self.community_manager.get_available_house_type(community_id)
    
    def jug_community_housetype_valid(self,community_id,house_type,house_type_ids):
        return self.community_manager.jug_community_housetype_valid(community_id,house_type.lower(),house_type_ids)
    
    def jug_house_valid(self,choose_house_id):
        return self.house_manager.jug_house_valid(choose_house_id)
    
    def community_id_to_name(self,community_id):
        return self.community_manager[community_id].get("community_name","")
    def house_ids_to_infos(self,house_ids):
        house_infos={}
        for house_id in house_ids:
            house_infos.update({house_id:
                                self.house_manager.data[house_id]})
        return house_infos
    
    def get_available_community_ids(self):
        return self.community_manager.get_available_community_ids()
    