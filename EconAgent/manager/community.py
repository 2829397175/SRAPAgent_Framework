import json
import os
from .base import BaseManager
from . import manager_registry as ManagerRgistry
import EconAgent.map as map
from typing import List,Union
from copy import deepcopy
@ManagerRgistry.register("community")
class CommunityManager(BaseManager):
    """
        manage infos of different community.
    """
    total_community_datas:dict={}
    distribution_batch_data:dict={}
    patch_method = "random_avg"
    
    
    @classmethod
    def load_data(cls,
                  data_dir,
                  **kwargs):

        assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
        with open(data_dir,'r',encoding = 'utf-8') as f:
            total_community_datas = json.load(f)
            
        distribution_path = kwargs.pop("distribution_batch_dir")
        with open(distribution_path,'r',encoding = 'utf-8') as f:
            distribution_batch_data = json.load(f)

        return cls(
            total_community_datas = total_community_datas,
            data = {},
            distribution_batch_data = distribution_batch_data,
            data_type= "community_data",
            **kwargs
            )
        
    def get_house_info(self,house_id):
        for community in self.total_community_datas.values():
            for house_type in ['large_house','middle_house', 'small_house']:
                if house_type in community and house_id in community[house_type]['index']:
                    house_info = community.copy()
                    house_info[house_type] = community[house_type].copy()
                    house_info[house_type]['index'] = [house_id]
                    house_info[house_type]['remain_number'] = 1
                    house_info['sum_num'] = 1
                    house_info['sum_remain_num'] = 1
                    house_info['available']=True
                    #删除其他房型的内容
                    house_type_list=['large_house','middle_house', 'small_house']
                    house_type_list.remove(house_type)
                    
                    for other_type in house_type_list:
                        if other_type in house_info:
                            del house_info[other_type]
                    return house_info
        return None
        
    def merge_community_info(self,com_a, com_b):
        if com_a=={}:
            return com_b
        if com_b=={}:
            return com_a
        # 创建一个新的空字典用于存储合并后的信息
        merged_community = {}
    
        # 合并sum_num和sum_remain_num
        merged_community["sum_num"] = com_a["sum_num"] + com_b["sum_num"]
        merged_community["sum_remain_num"] = com_a["sum_remain_num"] + com_b["sum_remain_num"]

        # 合并每种房型的信息
        for house_type in ["large_house","middle_house","small_house"]:
            if house_type in com_a and house_type in com_b:
                merged_community[house_type] = {}
                
                # 合并remain_number
                merged_community[house_type]["remain_number"] = com_a[house_type]["remain_number"] + com_b[house_type]["remain_number"]
                
                # 合并index
                merged_community[house_type]["index"] = com_a[house_type]["index"] + com_b[house_type]["index"]
                
                # 对于其他的字段（例如living_room、size和cost），可以选择保留其中一个或按需合并。这里仅作为示例保留community_1的内容。
                for key in ["living_room", "size", "cost"]:
                    merged_community[house_type][key] = com_a[house_type][key]
            elif house_type in com_a:
                merged_community[house_type]=com_a[house_type]
            elif house_type in com_b:
                merged_community[house_type]=com_b[house_type]
                       
        # 对于其他的字段（例如location、community_name等），可以选择保留其中一个或按需合并。这里仅作为示例保留community_1的内容。
        for key in ["community_id", "community_name", "location", "en_location", "value_inch", "description", "nearby_info","available"]:
            merged_community[key] = com_a[key]
            
        return merged_community
    
    #为队列添加房子
    def add_community_pool(self,add_pool):
        for queue_name,house_pool in add_pool.items():
            if queue_name not in self.data:
                self.data[queue_name] = {}
            for house_id in house_pool:
                house_info = self.get_house_info(house_id)
                if house_info["community_id"] not in self.data[queue_name]:
                    self.data[queue_name][house_info["community_id"]]={}
                self.data[queue_name][house_info["community_id"]]=self.merge_community_info(
                    self.data[queue_name][house_info["community_id"]],house_info)
    
    
    def patch_houses(self,
                     tenant_manager,
                     house_manager,
                     cnt_turn):
        tenant_groups = tenant_manager.groups
        queue_names = list(tenant_groups.keys())
        
        # 平均分组
        import numpy as np
        import random
        def avg_groups(data, num_groups,queue_names):
            random.shuffle(data)
            n_per_group = len(data) // num_groups
            end_p = n_per_group*num_groups
            if end_p == len(data):
                end_p = -1
                groups = np.array(data).reshape(num_groups, n_per_group)
            else:
                groups = np.array(data[:end_p]).reshape(num_groups, n_per_group)
                
            groups = groups.tolist()
            if (end_p != -1):
                groups[-1].extend(data[end_p:])
                
            queue_group_h_ids = {}
            for idx,queue_name in enumerate(queue_names):
                queue_group_h_ids[queue_name] = groups[idx]
            return queue_group_h_ids
        
        def house_type_groups(house_ids,
                              queue_names): # 默认返回三个group
            
            # if tenant_manager.policy.group_policy.type == "portion":
            #     assert len(queue_names) <=3, "unsupported length of queue!"
            #     import re
            #     regex = f"(\d+\.*\d*)<(.*)<(\d+\.*\d*)"
                
            #     portions = []
            #     attr =""
            #     valid_tenant_postive_attr = ["family_members_num",
            #                         "monthly_income",
            #                         "monthly_rent_budget"] # 指标越大 选 越大的房子（正向指标）
            #     for queue_name in queue_names:
            #         try:
            #             match = re.search(regex, queue_name)
            #             attr = match.group(2)
            #             portions.append((queue_name,float(match.group(3))))
            #             assert attr in valid_tenant_postive_attr
            #         except:
            #             raise Exception(f"invalid queue name! :{queue_name}")
                
            #     portions.sort(key=lambda x:x[1])
                
            #     for (queue_name,portion_left), house_type in zip()
                
                
                
            queue_houses = {}
            random.shuffle(house_ids)
            for house_id in house_ids:
                house_type = house_manager.data[house_id]["house_type"]
                if house_type not in queue_houses:
                    # assert house_type in queue_names
                    queue_houses[house_type]=[]

                queue_houses[house_type].append(house_id)
            return queue_houses
            
        def portion_groups(house_ids,
                           queue_names,
                           portion_attr ="house_area"): # 默认按照房子大小按比例分配
            
            queue_lens = len(queue_names)
            if queue_lens ==1:
                return {queue_names[0]:house_ids}
            
            if tenant_manager.policy.group_policy.type != "portion": 
                # 自选房型 或者 房型标签的方式
                
                queue_names_sorted = []
                for house_type in ["small_house","middle_house","large_house"]:
                    if house_type in queue_names:
                        queue_names_sorted.append(house_type)
                
                queue_portion_lens_dict ={
                    1:[1],
                    2:[0.5,1],
                    3:[0.3,0.7,1],
                }
                portions = list(zip(queue_names_sorted,queue_portion_lens_dict[len(queue_names_sorted)]))
            else:
                import re
                regex = f"(\d+\.*\d*)<(.*)<(\d+\.*\d*)"
                
                portions = []
                attr =""
                valid_tenant_postive_attr = ["family_members_num",
                                    "monthly_income",
                                    "monthly_rent_budget"] # 指标越大 选 越大的房子（正向指标）
                for queue_name in queue_names:
                    try:
                        match = re.search(regex, queue_name)
                        attr = match.group(2)
                        portions.append((queue_name,float(match.group(3))))
                        assert attr in valid_tenant_postive_attr
                    except:
                        raise Exception(f"invalid queue name! :{queue_name}")
                    
            index_house_basic_infos = {house_id:house_manager[house_id] for house_id in house_ids}
            list_sorted_index_house_basic_infos = sorted(index_house_basic_infos.items(),key =lambda x: float(x[1].get(portion_attr,0)))
            
            portions.sort(key=lambda x:x[1])
            
            queue_houses = {}
            ptr_l =0
            n = len(list_sorted_index_house_basic_infos)
            for idx_group,portion_tuple in enumerate(portions):
                ptr_r = int(portion_tuple[1]*n)
                if idx_group == len(portions) - 1:
                    portion_indexs = [ x[0] for x in list_sorted_index_house_basic_infos[ptr_l:]]
                else:
                    portion_indexs = [ x[0] for x in list_sorted_index_house_basic_infos[ptr_l:ptr_r]]
                
                queue_houses[portion_tuple[0]] = portion_indexs
                
                ptr_l = ptr_r
                
            return queue_houses
            
            
        
        # 将每个queue新加的房子， 随机分配到三个queue的队列内
        if (str(cnt_turn) not in self.distribution_batch_data.keys()):
            return

        queue_house_ids = self.distribution_batch_data[str(cnt_turn)]
        assert isinstance(queue_house_ids,list), "error in queue house format!"
        
        if self.patch_method == "single_list":
            queue_group_h_ids = {queue_names[0]:queue_house_ids}
        
        elif self.patch_method == "house_type":
            queue_group_h_ids = house_type_groups(queue_house_ids,
                                                queue_names)
            
        elif self.patch_method == "random_avg":
            queue_group_h_ids = avg_groups(queue_house_ids,
                                           len(queue_names),
                                                queue_names)
        elif self.patch_method == "portion_housesize":
            queue_group_h_ids = portion_groups(queue_house_ids,
                                             queue_names,
                                            "house_area")
        elif self.patch_method == "portion_rentmoney":
            queue_group_h_ids = portion_groups(queue_house_ids,
                                             queue_names,
                                            "rent_money")
        else:
            raise NotImplementedError("This type of patch method is not supported.")
        
        
        """random group"""
        # queue_group_h_ids = avg_groups(queue_house_ids,queue_names)
       
        
        self.distribution_batch_data[str(cnt_turn)] = {}
        for queue_name, group_ids in queue_group_h_ids.items():
            self.distribution_batch_data[str(cnt_turn)][queue_name] = group_ids
        
    
    def publish_house(self,cnt_turn):
        if str(cnt_turn) in self.distribution_batch_data.keys():
            self.add_community_pool(self.distribution_batch_data[str(cnt_turn)])
            print("New houses are added!")
            
    #查看每个池子的大小
    def get_pool_num(self):
        pool_num_dict={}
        for pool_name,pool in self.data.items():
            cur_house_num = 0
            for c_id,c_info in pool.items():
                cur_house_num += c_info["sum_remain_num"]
            
            pool_num_dict[pool_name] = cur_house_num
        return pool_num_dict
    
    def get_unreleased_house_num(self,
                                 cnt_turn):
        add_turn_future = []
        for add_turn  in self.distribution_batch_data.keys():
            if int(add_turn)> int(cnt_turn):
                add_turn_future.append(add_turn)
                
        future_add_houses_num = [len(self.distribution_batch_data.get(str(add_turn),[]))
                             for add_turn in add_turn_future]    
        
        return sum(future_add_houses_num)
            
    
    def community_str(self,
                      curcommunity_list,
                      furcommunity_list,
                      concise = False):
        if concise:
            curcommunity_description = []
            furcommunity_description = []
            template = """\
{community_id}. The rent for this community is {value_inch} dollars per square meter."""
            if len(curcommunity_list) ==0:
                curstr = ""
            else:
                for community_info in curcommunity_list:
                    curcommunity_description.append(template.format_map(community_info))
                
                curcommunitys_describe_prompt = """There are {len_cm} communities available in the system:{cm_info}"""
                curstr = curcommunitys_describe_prompt.format(len_cm = len(curcommunity_list),
                                                            cm_info = "\n\n".join(curcommunity_description))
            if len(furcommunity_list) ==0:
                furstr = ""
            else:
                for furcommunity_info in furcommunity_list:
                    furcommunity_description.append(template.format_map(furcommunity_info))
                furcommunitys_describe_prompt = """There are {len_cm} communities to be published:{cm_info}"""
                furstr = furcommunitys_describe_prompt.format(len_cm = len(furcommunity_list),
                                                            cm_info = "\n\n".join(furcommunity_description))
            return curstr,furstr
            
            
        len_curcommunity= len(curcommunity_list)
        len_furcommunity = len(furcommunity_list)
        template = """\
{community_id}. {community_name} is located at {en_location}. The rent for this community is {value_inch} dollars per square meter.\
In this community, {description}. {nearby_info}."""

        housetype_template = """\
The {housetype} in {community_id} is a {living_room} apartment, with an area of about {size}, the monthly rent  is about {cost} dollars, and there are still {remain_number} houses."""
        curcommunity_description = []
        furcommunity_description = []
        
        for community_info in curcommunity_list:
            curcommunity_description.append(template.format(community_id=community_info["community_id"],
                                                     community_name=community_info["community_name"],
                                                     en_location=community_info["en_location"],
                                                     value_inch=community_info["value_inch"],
                                                     description=community_info["description"],
                                                     nearby_info=community_info["nearby_info"],
                                                     ))
            house_types = ['small_house', 'middle_house', 'large_house']
            house_typs=[]
            for house_type in house_types:
                if house_type in community_info:
                    curcommunity_description.append("\t"+housetype_template.format(housetype=house_type,
                                                                       community_id =community_info["community_id"],
                                                                       living_room=community_info[house_type][
                                                                           "living_room"],
                                                                       size=community_info[house_type]["size"],
                                                                       cost=community_info[house_type]["cost"],
                                                                       remain_number=community_info[house_type][
                                                                           "remain_number"]
                                                                       ))
                    house_typs.append(house_type)
            # house_type_describe_prompt = "There are {num_house_type} room types in this community,including {house_type}. The infomation of room types are listed as follows:\n{room_type}"
            # house_type_describe=house_type_describe_prompt.format(num_house_type=len(house_typs),house_type=",".join(house_typs),room_type=curcommunity_description)
            # house_type_describe += "\n"

        curcommunitys_describe_prompt = "There are {num_communitys} communities available. The infomation of these communitys are listed as follows:\n\n{communitys}"
        if len_curcommunity>=1:
            curstr = curcommunitys_describe_prompt.format(num_communitys=len_curcommunity,
                                                communitys="\n\n".join(curcommunity_description))
        else:curstr =""
        
        if len(furcommunity_list)==0:
            return curstr,""
        
        for furcommunity_info in furcommunity_list:
            furcommunity_description.append(template.format(community_id=furcommunity_info["community_id"],
                                                     community_name=furcommunity_info["community_name"],
                                                     en_location=furcommunity_info["en_location"],
                                                     value_inch=furcommunity_info["value_inch"],
                                                     description=furcommunity_info["description"],
                                                     nearby_info=furcommunity_info["nearby_info"],
                                                     ))
            house_types = ['small_house', 'middle_house', 'large_house']
            house_typs = []
            for house_type in house_types:
                if house_type in furcommunity_info:
                    furcommunity_description.append("\t"+housetype_template.format(housetype=house_type,
                                                                       living_room=furcommunity_info[house_type][
                                                                           "living_room"],
                                                                       size=furcommunity_info[house_type]["size"],
                                                                       cost=furcommunity_info[house_type]["cost"],
                                                                       remain_number=furcommunity_info[house_type][
                                                                           "remain_number"],
                                                                       community_id = furcommunity_info["community_id"]
                                                                       ))
                    house_typs.append(house_type)
            # house_type_describe_prompt = "There are {num_house_type} room types in this community, including {house_type}. The infomation of room types are listed as follows:\n{room_type}"
            # house_type_describe = house_type_describe_prompt.format(num_house_type=len(house_typs),
            #                                                         house_type=",".join(house_typs),
            #                                                         room_type="\n".join(furcommunity_description))
            # house_type_describe += "\n"


        furcommunitys_describe_prompt = "There are {num_communitys} communities that will be released in the future . The infomation of these communitys are listed as follows:\n\n{communitys}"
        furstr = furcommunitys_describe_prompt.format(num_communitys=len_furcommunity,
                                                      communitys="\n\n".join(furcommunity_description))
        return curstr,furstr
    


    def get_house_type(self, community_id,house_types,queue_name):
        community_whole_info = self.data.get(queue_name)
        if community_whole_info== None:
            return ""
        community_infos=community_whole_info.get(community_id)
        if community_infos== None:
            return ""
        
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
    
    def jug_community_housetype_valid(self,community_id,housetype,house_type_ids,queue_name):
        community_infos = self.data.get(queue_name)
        if community_infos==None:
            return False
        community_info = community_infos.get(community_id)
        
        if community_info!=None and community_info["available"] and housetype in community_info and community_info[housetype]["remain_number"] > 0 and housetype in house_type_ids:
            return True
        else:
            return False
        
    def jug_community_valid(self,community_id,community_ids,queue_name):
        
        return community_id in community_ids and self.data.get(queue_name)!=None and community_id in self.data[queue_name].keys() and \
            self.data[queue_name][community_id].get("available",False)
            

    
    def get_filtered_house_ids(self, community_id,queue_name, house_types: Union[list,str] ):
        """
        filter from house_type (large/small/middle)
        """
        if not isinstance(house_types,list):
            house_types = [house_types]
        community_infos = self.data[queue_name][community_id]
        house_indexs = [community_infos.get(filter_key,{}).get('index', []) for filter_key in house_types]

        house_indexs_concat = []
        for house_index in house_indexs:
            house_indexs_concat.extend(house_index)
        return house_indexs_concat


    def get_available_house_type(self,community_id,queue_name):
        house_types=[]
        queue_community_info = self.data.get(queue_name,{})
        community_info=queue_community_info.get(community_id,{})
        if community_info.get("sum_remain_num",0)>  0 :
            for housetype,housetype_att in list(community_info.items()):
                if isinstance(housetype_att, dict) and 'remain_number' in housetype_att and housetype_att['remain_number'] > 0:
                        house_types.append(housetype)
        return house_types

    def get_available_community_info(self,queue_name=None):

        if self.data.get(queue_name)==None:
            return [],[]
        community_infos=deepcopy(self.data[queue_name])
        community_list=[]
        
        community_ids =[]
        for community_id, community_info in list(community_infos.items()):
            if  community_info["sum_remain_num"] >  0 :
                for housetype,housetype_att in list(community_info.items()):
                    if isinstance(housetype_att, dict) and 'remain_number' in housetype_att and housetype_att['remain_number'] <= 0:
                            del community_info[housetype]
                community_list.append(community_info)
                community_ids.append(community_id)
        return community_list,community_ids

    def get_publish_community_info(self):
        cur_cm_ids = []
        for queue in self.data.values():
            if isinstance(queue,dict):
                cur_cm_ids.extend(list(queue.keys()))
        fur_cm_ids = []
        fur_cm_list = []
        for comunity_id in self.total_community_datas.keys():
            if comunity_id not in cur_cm_ids:
                if self.total_community_datas[comunity_id]["sum_remain_num"] >  0 :
                    fur_cm_ids.append(comunity_id)
                    fur_cm_list.append(self.total_community_datas[comunity_id])
        return fur_cm_list,fur_cm_ids

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

    def correct_update_remain_num(self, community_id, queue_name,house_id):
        if self.data.get(queue_name)==None:
            return False
        if self.data[queue_name].get(community_id)==None:
            return False
        community_info = self.data[queue_name][community_id]
        
        if community_info["available"] == True and community_info["sum_remain_num"] >= 1:
            for key, value in list(community_info.items()):
                if isinstance(value, dict) and house_id in value["index"] and value["remain_number"] > 0:
                    return True
        return False





    

    def save_data(self):
       
        with open(self.save_dir, 'w', encoding='utf-8') as file:
            json.dump(self.data, file, indent=4,separators=(',', ':'),ensure_ascii=False)

    def set_chosed_house(self,house_id,community_id,queue_name,house_types:Union[list,str]):
        if not isinstance(house_types,list):
            house_types = [house_types]
        self.data[queue_name][community_id]["sum_remain_num"]=self.data[queue_name][community_id].get("sum_remain_num",1) - 1
        for filter_id in house_types:
            self.data[queue_name][community_id][filter_id]["remain_number"] \
            = self.data[queue_name][community_id][filter_id].get("remain_number",1) - 1
            if house_id in self.data[queue_name][community_id][filter_id]['index']:
                self.data[queue_name][community_id][filter_id]['index'].remove(house_id)

    
    def get_available_community_ids(self,queue_name) -> List[str]:
        if queue_name not in self.data.keys():
            return []
        
        
        
        community_data = self.data[queue_name]
        community_ids = self.data[queue_name].keys()
        available_ids=list(filter(lambda community_id:community_id in community_data.keys() \
            and community_data[community_id].get("available",False), community_ids))

        return available_ids
    
    def get_system_competiveness_description(self,queue_name) -> str:
        description_general={
            "large_portion":"The {c_name} has been almost fully selected.",
            "small_portion": "A small portion of properties in {c_name} have been selected.",
            "none":"The {c_name} has not been chosen yet."
        } # 注：选完了的项目不会出现在description里面
        
        available_c_ids = self.get_available_community_ids(queue_name)
        system_competiveness_description = []
        for c_id in available_c_ids:
            chosen_portion = self.data[queue_name][c_id].get("sum_remain_num",0)/self.data[queue_name][c_id].get("sum_num",1)
            if (chosen_portion ==0):
                system_competiveness_description.append(description_general["none"].format(
                    c_name = f"{c_id}({self.data[queue_name][c_id].get('community_name')})"
                    ))
            elif (chosen_portion >0.5):
                system_competiveness_description.append(description_general["large_portion"].format(
                    c_name = f"{c_id}({self.data[queue_name][c_id].get('community_name')})"
                    ))
            else:
                system_competiveness_description.append(description_general["small_portion"].format(
                    c_name = f"{c_id}({self.data[queue_name][c_id].get('community_name')})"
                    ))
        return " ".join(system_competiveness_description)
    
    
