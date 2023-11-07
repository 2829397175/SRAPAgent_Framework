from LLM_PublicHouseAllocation.manager import HouseManager,CommunityManager
from pydantic import BaseModel
from typing import List
from LLM_PublicHouseAllocation.tenant.langchain_tenant import LangchainTenant
from LLM_PublicHouseAllocation.environments.rules import Rule
class System(BaseModel):
   
    house_manager:HouseManager
    community_manager:CommunityManager
    
    def __init__(self,**kargs):
        super().__init__(**kargs)
        # 为各个house设定house_type 属性
        self.house_manager.set_house_type(self.community_manager)
    
    def reset(self):
        pass
    
    def save_data(self):
        self.community_manager.save_data()
        self.house_manager.save_data()
        
    def set_chosed_house(self,house_id,community_id,queue_name,house_filter_ids:dict):
        house_types = house_filter_ids.get("house_type")
        self.community_manager.set_chosed_house(house_id,community_id,queue_name,house_types)
        self.house_manager.set_chosed_house(house_id)
        
    
        
    
    def available_house_num(self):
        pool_num_dict = self.community_manager.get_pool_num() 
        num = sum(pool_num_dict.values())    
        return num
    
    
    def get_community_abstract(self,
                               queue_name=None,
                               rule=None, 
                               tenant=None, 
                               house_type = None,
                               concise = False):

        curcommunity_list,cur_community_ids = self.community_manager.get_available_community_info(queue_name)
        furcommunity_list,fur_community_ids = self.community_manager.get_publish_community_info()
        if not queue_name==None and isinstance(rule,Rule):
            curcommunity_list = rule.filter_community(tenant = tenant,
                                                    community_list = curcommunity_list,
                                                        house_type = house_type)
            cur_community_ids = [cm_info['community_id'] for cm_info in curcommunity_list]
                                                    
        cur_str,furstr=self.community_manager.community_str(curcommunity_list,
                                                                furcommunity_list,
                                                                concise = concise)
        community_str = furstr +"\n\n"+ cur_str
        # 返回所有的小区信息 加上 可选的小区列表
        return community_str,cur_community_ids
    

        
    
    def get_split_community_abstract(self,queue_name):
        community_list,_=self.community_manager.get_available_community_info(queue_name)
        curcommunity_list,furcommunity_list = self.community_manager.split(community_list)
        curstr,furstr=self.community_manager.community_str(curcommunity_list,furcommunity_list)
        return curstr,furstr
        
        
    # 这里不做对可见house type的限制
    def get_house_type(self,queue_name,community_id = None,rule=None,tenant=None):
        if community_id == None:
            house_types = ["large_house","middle_house","small_house"]
            default_house_type_description ={
                "large_house":"This type of house can accommodate more than three people.",
                "middle_house":"This type of house is suitable for families of two people,\
and can also accommodate a younger child.",
                "small_house":"This type of house is suitable for one person to live alone."
            }
            house_type_description = ["{index}:{description}".format(index = index,
                                      description = default_house_type_description[index]) 
                                      for index in house_types]
            house_types_str = "\n\n".join(house_type_description)
            house_types_describe_prompt = "There are {num_house_types} house types available. The infomation of these house types are listed as follows:\n{house_types} "
            str_house_type_description = house_types_describe_prompt.format(num_house_types=len(house_types),
                                                                            house_types=house_types_str)
            return str_house_type_description,house_types
            
        if isinstance(rule,Rule) and isinstance(tenant,LangchainTenant):
            house_types = self.community_manager.get_available_house_type(community_id,queue_name)

            return self.community_manager.get_house_type(community_id,house_types,queue_name),\
                house_types
        else:
            house_types = self.community_manager.get_available_house_type(community_id,queue_name)
            return self.community_manager.get_house_type(community_id,house_types,queue_name),\
                house_types
                
                
    def get_house_floor(self,community_id = None,rule=None,tenant=None):
        
        common_knowledge_orientation ={
"high":"""it is on the 10th floor or above.""",
"low":"""it is below 10th floor.""",
}
        if community_id is None:
            available_communitys = list(self.community_manager.data.keys())
        else:
            available_communitys = [community_id]
            
        # 楼层高低设定：<10 :low , >=10 :high
            
        floor_types = []
        for c_id in available_communitys:
            community_name = self.community_manager.total_community_datas[c_id].get("community_name")
            if (len(floor_types)==2):
                break
            for house_id in self.house_manager.community_to_house[community_name]:
                house_info = self.house_manager[house_id]
                floor = house_info.get("floor") 
                floor_type = "high" if floor>= 10 else "low"
                if floor_type not in floor_types:
                    floor_types.append(floor_type)
                    
            
        floor_description = ""
        for floor_type in floor_types:
            floor_description +="{floor_type}:{floor_description}\n".format(floor_type = floor_type,
                                                                          floor_description = common_knowledge_orientation[floor_type])
        
        head_prompt = "There are {num_floor} types of house floors available. \
The infomation of these floor types are listed as follows:\n{floor_description} "
        str_head_floor_description = head_prompt.format(num_floor = len(floor_types),
                                                              floor_description = floor_description)
        return str_head_floor_description, floor_types
               
            
        
    
    def get_house_orientation(self,queue_name,community_id = None,rule=None,tenant=None):
        # se,sw 算s ne,nw 算w
        common_knowledge_orientation ={
"S":"""South orientation: The north and south are well ventilated, \
with sufficient lighting, and have the characteristics of warm winter and cool summer;""",

"E":"""Eastward orientation: In areas where the sun shines, \
the lighting is good, and winter is warm, but summer can be very hot in the early morning, with poor ventilation""",

"N":"""North orientation: This orientation has poor lighting, with no sunlight throughout the year.\
However, in summer, it feels cooler, while in winter, it becomes colder. \
Over time, the room's Yin Qi becomes heavier, which is not very good for physical health;""",

"W":"""West orientation: The lighting time is relatively short, \
which means there can never be sun exposure on the buttocks, \
and there will be exposure to sunlight indoors on summer afternoons."""}
        
        if community_id is None:
            available_communitys = list(self.community_manager.data[queue_name].keys())
        else:
            available_communitys = [community_id]
            
        orientations = []
        for c_id in available_communitys:
            community_name = self.community_manager[queue_name][c_id].get("community_name")
            for house_id in self.house_manager.community_to_house[community_name]:
                house_info = self.house_manager[house_id]
                if house_info.get("toward") not in orientations:
                    orientations.append(house_info.get("toward"))
        
        return_orientation = []
        orientation_description = []
        orientation_description_template = """({orientation}){description}"""
        for orientation in orientations:
            for key in common_knowledge_orientation.keys():
                if (key in orientation.upper()) and \
                    (key not in return_orientation):
                    return_orientation.append(key)
                    orientation_description.append(orientation_description_template.format(orientation = key,
                                                    description = common_knowledge_orientation[key]))
                    break
        
        str_orientation_description = "\n\n".join(orientation_description)
        head_prompt = "There are {num_ori} types of house orientation available. The infomation of these house orientations are listed as follows:\n{house_orientations} "
        str_head_orientation_description = head_prompt.format(num_ori=len(return_orientation),
                                                            house_orientations=str_orientation_description)
        return str_head_orientation_description, return_orientation
    
    
    def get_filtered_houses_ids(self,community_id,queue_name,house_filter_ids:dict):
        house_types =  house_filter_ids.get("house_type")
        house_ids = self.community_manager.get_filtered_house_ids(
            community_id = community_id,
            queue_name = queue_name,
            house_types = house_types
        )
        house_ids = self.house_manager.get_filtered_house_ids(
            house_filter_ids = house_filter_ids,
            house_ids = house_ids
        )
        
        return house_ids
    
    
    def get_house_dark_info(self,house_id):
        dark_info=""
        if house_id in self.house_manager.data.keys():
            dark_info=self.house_manager.data[house_id].get("potential_information_house","")
        return dark_info
    
    def get_community_data(self):
        return self.community_manager.total_community_datas
    
    def jug_community_valid(self,community_id,community_ids,queue_name):
        return self.community_manager.jug_community_valid(community_id.lower(),community_ids,queue_name)
    
    def get_available_house_type(self,community_id,queue_name):
        return self.community_manager.get_available_house_type(community_id,queue_name)
    
    def jug_community_housetype_valid(self,community_id,house_type,house_type_ids,queue_name):
        return self.community_manager.jug_community_housetype_valid(community_id,house_type.lower(),house_type_ids,queue_name)
    
    def jug_house_valid(self,choose_house_id):
        return self.house_manager.jug_house_valid(choose_house_id)
    
    def community_id_to_name(self,community_id):
        return self.community_manager.total_community_datas[community_id].get("community_name","")
    def house_ids_to_infos(self,house_ids):
        house_infos={}
        for house_id in house_ids:
            house_infos.update({house_id:
                                self.house_manager.data[house_id]})
        return house_infos
    
    def get_available_community_ids(self,queue_name):
        return self.community_manager.get_available_community_ids(queue_name)
    
    def get_system_competiveness_description(self,queue_name):
        # test:experiment
#         return """"competitive, the community_1 has been almost \
# fully selected, the community_2 has a relatively sufficient house, the community_3 has not \
# been chosen yet."""
        return self.community_manager.get_system_competiveness_description(queue_name)
    
    def get_score_house_description(self,
                                    house_id,
                                    tenant):
        community_name=None
        for cn,house_list in self.house_manager.community_to_house.items():
            if house_id in house_list:
                community_name=cn
                break
        if not community_name:
            return None
        house_description_template="""
                {index}: 
                {index} is located in {community_id}. {community_id}({community_name}) is located at {en_location}. The rent for this community is {value_inch} dollars per square meter.\
In this community, {community_description}. {nearby_info}.
                {index} costs about {rent_money}. \
                {index}'s square fortage is about {house_area}. The orientation of {index} is {toward}. {index} is located at floor {floor}. {index} {elevator} elevator. {index} {balcony} balcony. \
                {description}\
                For my family members, the average living area for {index} is {average_living_area:.3f}.
        """
        # for _,communities in self.community_manager.total_community_datas.items():
        for community_id,community_details in self.community_manager.total_community_datas.items():
            if community_details["community_name"]==community_name:
                house_description=house_description_template.format(index=house_id,
                                                    rent_money=self.house_manager.data[house_id]["rent_money"],
                                                    house_area=self.house_manager.data[house_id]["house_area"],
                                                    toward=self.house_manager.data[house_id]["toward"],
                                                    floor=self.house_manager.data[house_id]["floor"],
                                                    elevator=self.house_manager.data[house_id]["elevator"],
                                                    description=self.house_manager.data[house_id]["description"],
                                                    balcony=self.house_manager.data[house_id]["balcony"],
                                                    community_id=community_details["community_id"],
                                                    community_name=community_details["community_name"],
                                                    en_location=community_details["en_location"],
                                                    value_inch=community_details["value_inch"],
                                                    community_description=community_details["description"],
                                                    nearby_info=community_details["nearby_info"],
                                                    average_living_area = float(self.house_manager.data[house_id]["house_area"])/tenant.family_num
                                                    )
                return   house_description  
        return None   
            
    
    # fixed , 需要改
    def get_goal(self): # 给出租房系统中，所有人的整体目标
        return "Your goal is to develop a plan that is most beneficial to you \
to increase your chances of choosing a house in the current situation."