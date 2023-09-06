from pydantic import BaseModel
from . import readcommunity_registry as ReadCommunityRgistry
from .base import Base_ReadCommunity
from typing import List

# 每次返回available的小区信息，不泄露未来community

@ReadCommunityRgistry.register("available")
class Available_ReadCommunity(Base_ReadCommunity):
    
    def read_community_list(self,
                            community_data:dict,
                            community_ids:List[str] = None):
        community_ids = community_data.keys() if community_ids is None else community_ids
        community_ids = self.filter_community_ids(community_data=community_data,
                                                  community_ids=community_ids)
        community_data_filtered = self.get_available_community_abstract(community_data=community_data,
                                                                        community_ids=community_ids) 
        
        return self.get_community_abstract(community_infos=community_data_filtered)
        
    def get_community_abstract(self,
                               community_infos):
        len_community = len(community_infos)

        template = """{index}: 
        {community_name}, located at {en_location}. \
        The rent for this community is {value_inch} dollars per square meter. \
        {get_shortest_commute_time_str}. \
        In this community, {description}. \
        {nearby_info}. \
        There are {remain_house_num} houses."""
        communitys_str = [
            template.format(index = community_idx,
                            community_name = community_info.get("community_name",""),
                            en_location=community_info.get("en_location", ""),
                            value_inch= community_info.get("value_inch",""),
                            get_shortest_commute_time_str = community_info.get("get_shortest_commute_time_str", ""),
                            description=community_info.get("description",""),
                            nearby_info = community_info.get("nearby_info",""),
                            remain_house_num=community_info.get("sum_remain_num", 0))
            for community_idx, community_info in community_infos.items()
        ]
        communitys_str = "\n\n".join(communitys_str)
        communitys_describe_prompt = "There are {num_communitys} communitys available. The infomation of these communitys are listed as follows:\n{communitys} "
        str_community_description = communitys_describe_prompt.format(num_communitys=len_community,
                                                                      communitys=communitys_str)

        return str_community_description
    
        
    def get_available_community_abstract(self,
                                     community_data:dict,
                                     community_ids:List[str]):
        community_filtered = {}
        community_data_temp = community_data.copy()
        
        for community_id, community_info in list(community_data_temp.items()):
            if community_id not in community_ids:
                continue
            if  community_info["sum_remain_num"] >  0 :
                for housetype,housetype_att in list(community_info.items()):
                    if isinstance(housetype_att, dict) \
                        and 'remain_number' in housetype_att \
                        and housetype_att['remain_number'] <= 0:
                        del community_info[housetype]
                        
                community_filtered[community_id] = community_info
                
        return community_filtered
    
    def filter_community_ids(self,community_data:dict,community_ids:List[str]):
        return list(filter(lambda community_id:community_id in community_data.keys() \
            and community_data[community_id].get("available",False), community_ids))
        
        
    