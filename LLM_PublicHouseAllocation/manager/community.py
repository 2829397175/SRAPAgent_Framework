import json
import os
from .base import BaseManager
from . import manager_registry as ManagerRgistry
import LLM_PublicHouseAllocation.map as map
from typing import List,Union
from copy import deepcopy
@ManagerRgistry.register("community")
class CommunityManager(BaseManager):
    """
        manage infos of different community.
    """
    
    @classmethod
    def load_data(cls,
                  data_dir,
                  **kwargs):

        assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
        with open(data_dir,'r',encoding = 'utf-8') as f:
            community_datas = json.load(f)
            
        publish_order = kwargs.pop("publish_order",False)
        id_ = 0
        for community_name, community_info in community_datas.items():
            if publish_order:
                community_info["available"] = False
                if (id_ == 0):
                    community_info["available"] = True
                    id_+=1
            else:
                community_info["available"] = True

        return cls(
            data = community_datas,
            data_type= "community_data",
            save_dir= kwargs["save_dir"]
            )

    def publish_community(self, k=1):
        for community_id, community in self.data.items():
            if community["available"] == False and community["sum_remain_num"] >0 and k>0:
                community["available"]= True
                k-=1
                print(community["community_name"]+"  发布新房子了!!!!!\n")
    
    def community_str(self,curcommunity_list,furcommunity_list):
        len_curcommunity= len(curcommunity_list)
        len_furcommunity = len(furcommunity_list)
        template = """\
{community_id}. {community_name} is located at {en_location}. The rent for this community is {value_inch} dollars per square meter.\
In this community, {description}. {nearby_info}."""

        housetype_template = """\
The {housetype} in this community is a {living_room} apartment, with an area of about {size}, the monthly rent  is about {cost} dollars, and there are still {remain_number} houses."""
        curcommunity_description = ""
        furcommunity_description = ""
        
        for community_info in curcommunity_list:
            curcommunity_description += template.format(community_id=community_info["community_id"],
                                                     community_name=community_info["community_name"],
                                                     en_location=community_info["en_location"],
                                                     value_inch=community_info["value_inch"],
                                                     description=community_info["description"],
                                                     nearby_info=community_info["nearby_info"],
                                                     )
            house_types = ['small_house', 'middle_house', 'large_house']
            house_typs=[]
            for house_type in house_types:
                if house_type in community_info:
                    curcommunity_description += housetype_template.format(housetype=house_type,
                                                                       living_room=community_info[house_type][
                                                                           "living_room"],
                                                                       size=community_info[house_type]["size"],
                                                                       cost=community_info[house_type]["cost"],
                                                                       remain_number=community_info[house_type][
                                                                           "remain_number"]
                                                                       )
                    house_typs.append(house_type)
            house_type_describe_prompt = "There are {num_house_type} room types in this community,including {house_type}. The infomation of room types are listed as follows:\n{room_type}"
            house_type_describe=house_type_describe_prompt.format(num_house_type=len(house_typs),house_type=",".join(house_typs),room_type=curcommunity_description)
            house_type_describe += "\n"

        curcommunitys_describe_prompt = "There are {num_communitys} communities available. The infomation of these communitys are listed as follows:\n{communitys}"
        curstr = curcommunitys_describe_prompt.format(num_communitys=len_curcommunity,
                                                                      communitys=curcommunity_description)
        if len(furcommunity_list)==0:
            return curstr,""
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
            house_types = ['small_house', 'middle_house', 'large_house']
            house_typs = []
            for house_type in house_types:
                if house_type in furcommunity_info:
                    furcommunity_description += housetype_template.format(housetype=house_type,
                                                                       living_room=furcommunity_info[house_type][
                                                                           "living_room"],
                                                                       size=furcommunity_info[house_type]["size"],
                                                                       cost=furcommunity_info[house_type]["cost"],
                                                                       remain_number=furcommunity_info[house_type][
                                                                           "remain_number"]
                                                                       )
                    house_typs.append(house_type)
            house_type_describe_prompt = "There are {num_house_type} room types in this community,including {house_type}. The infomation of room types are listed as follows:\n{room_type}"
            house_type_describe = house_type_describe_prompt.format(num_house_type=len(house_typs),
                                                                    house_type=",".join(house_typs),
                                                                    room_type=furcommunity_description)
            house_type_describe += "\n"


        furcommunitys_describe_prompt = "There are {num_communitys} communities that will be released in the future . The infomation of these communitys are listed as follows:\n{communitys}"
        furstr = furcommunitys_describe_prompt.format(num_communitys=len_furcommunity,
                                                                      communitys=furcommunity_description)
        return curstr,furstr
    


    def get_house_type(self, community_id,house_types):
        community_infos = self.data[community_id]
        #house_types = self.get_available_house_type(community_id)
        house_type_infos = {}
        for house_type in house_types:
            if house_type in community_infos.keys():
                house_type_infos[house_type] = community_infos[house_type]

        len_house_type = len(house_type_infos)
        template = """{index}:
This type house's rent is around {mean_cost},\
and it's square footage is around {mean_size}.\
There remains {remain_num} houses of this type."""

        house_types_str = [
            template.format(index=house_type_idx,
                            mean_cost=house_type_info.get("cost", ""),
                            mean_size=house_type_info.get("size", ""),
                            remain_num=house_type_info.get("remain_number", 0), )
            for house_type_idx, house_type_info in house_type_infos.items()
        ]
        house_types_str = "\n\n".join(house_types_str)
        house_types_describe_prompt = "There are {num_house_types} house types available. The infomation of these house types are listed as follows:\n{house_types} "
        str_house_type_description = house_types_describe_prompt.format(num_house_types=len_house_type,
                                                                        house_types=house_types_str)

        return str_house_type_description
    
    def jug_community_housetype_valid(self,community_id,housetype,house_type_ids):
        community_infos = self.data.get(community_id)

        if community_infos!=None and community_infos["available"] and housetype in community_infos and community_infos[housetype]["remain_number"] > 0 and housetype in house_type_ids:
            return True
        else:
            return False
        
    def jug_community_valid(self,community_id,community_ids):
        return community_id in community_ids and community_id in self.data.keys() and \
            self.data[community_id].get("available",False)
            

    
    def get_filtered_house_ids(self, community_id, house_types: Union[list,str] ):
        """
        filter from house_type (large/small/middle)
        """
        if not isinstance(house_types,list):
            house_types = [house_types]
        community_infos = self.data[community_id]
        house_indexs = [community_infos[filter_key].get('index', []) for filter_key in house_types]

        house_indexs_concat = []
        for house_index in house_indexs:
            house_indexs_concat.extend(house_index)
        return house_indexs_concat


    def get_available_house_type(self,community_id):
        house_types=[]
        community_info = self.data.get(community_id,{})
        if community_info.get("sum_remain_num",0)>  0 :
            for housetype,housetype_att in list(community_info.items()):
                if isinstance(housetype_att, dict) and 'remain_number' in housetype_att and housetype_att['remain_number'] > 0:
                        house_types.append(housetype)
        return house_types

    def get_available_community_info(self):
        community_infos=deepcopy(self.data)
        community_list=[]
        for community_id, community_info in list(community_infos.items()):
            if  community_info["sum_remain_num"] >  0 :
                for housetype,housetype_att in list(community_info.items()):
                    if isinstance(housetype_att, dict) and 'remain_number' in housetype_att and housetype_att['remain_number'] <= 0:
                            del community_info[housetype]
                community_list.append(community_info)
        return community_list



    def split(self,community_list):
        current_infos=[]
        future_infos=[]
        # print(community_infos)
        for  community_info in community_list:
            if community_info["available"] == True:
                current_infos.append(community_info)
            if community_info["available"] == False and community_info["sum_remain_num"] > 0:
                future_infos.append(community_info)
        return current_infos, future_infos

    def correct_update_remain_num(self, community_id, house_id):
        community_info = self.data[community_id]
        if community_info["available"] == True and community_info["sum_remain_num"] >= 1:
            for key, value in list(community_info.items()):
                if isinstance(value, dict) and house_id in value["index"] and value["remain_number"] > 0:
                    return True
        return False

    # def update_remain_num(self,community_name,house_id):
    #     for community_id,community_info in self.data.items():
    #         if community_info["community_name"]==community_name and community_info["available"]==True :
    #             community_info["sum_remain_num"]-=1
    #             if community_info["sum_remain_num"]<=0:
    #                 community_info["available"] = False
    #             for key, value in list(community_info.items()):
    #                 if isinstance(value, dict) and house_id in value["index"] and value["remain_number"] > 0:
    #                     value["remain_number"]-=1
    #                     value["index"].remove(house_id)
    #             return community_info["description"]




    

    def save_data(self):
        # assert os.path.exists(self.save_dir), "no such file path: {}".format(self.save_dir)
        with open(self.save_dir, 'w', encoding='utf-8') as file:
            json.dump(self.data, file, indent=4,separators=(',', ':'),ensure_ascii=False)

    def set_chosed_house(self,house_id,community_id,house_filter_ids):
        self.data[community_id]["sum_remain_num"]=self.data[community_id].get("sum_remain_num",1) - 1
        for filter_id in house_filter_ids:
            self.data[community_id][filter_id]["remain_number"] \
            = self.data[community_id][filter_id].get("remain_number",1) - 1
            if house_id in self.data[community_id][filter_id]['index']:
                self.data[community_id][filter_id]['index'].remove(house_id)

    
    def get_available_community_ids(self)->List[str]:
        community_data = self.data
        community_ids = self.data.keys()
        available_ids=list(filter(lambda community_id:community_id in community_data.keys() \
            and community_data[community_id].get("available",False), community_ids))

        return available_ids