from pydantic import BaseModel
from . import readcommunity_registry as ReadCommunityRgistry
from .base import Base_ReadCommunity
from typing import List

# 每次返回future+cur 小区信息

# 没写完

@ReadCommunityRgistry.register("available")
class Publish_Order_ReadCommunity(Base_ReadCommunity):
    def read_community_list(self,
                            community_manager,
                            community_ids:List[str] = None):
        cur_info, fur_info = community_manager.split(community_ids)
        house_info, house_future_info=self.community_str(house_info, house_future_info)
        
        
    
    def community_str(self,curcommunity_list,furcommunity_list):
        len_curcommunity= len(curcommunity_list)
        len_furcommunity = len(furcommunity_list)
        template = """\
                                {community_id}. {community_name} is located at {en_location}.\
                                The rent for this community is {value_inch} dollars per square meter. 
                                {get_shortest_commute_time_str}.\
                                In this community, {description}. 
                                {nearby_info}.My comment after watching the community forum is that {comment_summary}.\
                            """

        curcommunity_description = ""
        furcommunity_description = ""
        for community_info in curcommunity_list:
            curcommunity_description += template.format(community_id=community_info["community_id"],
                                                     community_name=community_info["community_name"],
                                                     en_location=community_info["en_location"],
                                                     value_inch=community_info["value_inch"],
                                                     description=community_info["description"],
                                                     get_shortest_commute_time_str=community_info[
                                                         "get_shortest_commute_time"],
                                                     nearby_info=community_info["nearby_info"],
                                                     comment_summary=community_info["comment_summary"]
                                                     )
            

        curcommunitys_describe_prompt = "There are {num_communitys} communities available. The infomation of these communitys are listed as follows:\n{communitys}"
        curstr = curcommunitys_describe_prompt.format(num_communitys=len_curcommunity,
                                                                      communitys=curcommunity_description)

        for furcommunity_info in furcommunity_list:
            furcommunity_description += template.format(community_id=furcommunity_info["community_id"],
                                                     community_name=furcommunity_info["community_name"],
                                                     en_location=furcommunity_info["en_location"],
                                                     value_inch=furcommunity_info["value_inch"],
                                                     description=furcommunity_info["description"],
                                                     get_shortest_commute_time_str=furcommunity_info[
                                                         "get_shortest_commute_time"],
                                                     nearby_info=furcommunity_info["nearby_info"],
                                                     comment_summary=furcommunity_info["comment_summary"]
                                                     )

        furcommunitys_describe_prompt = "There are {num_communitys} communities that will be released in the future . \
            The infomation of these communitys are listed as follows:\n{communitys}"
        furstr = furcommunitys_describe_prompt.format(num_communitys=len_furcommunity,
                                                                      communitys=furcommunity_description)
        return curstr,furstr
    
    