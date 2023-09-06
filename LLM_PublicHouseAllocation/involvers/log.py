from pydantic import BaseModel
import json
# Design a basic LogRound class
class LogRound(BaseModel):
    log_list:list=[]
    log_round:dict={}
    save_dir:str=""
    def set_tenant_information(self,id,name,available_times):
        self.log_round["tenant_id"] = id
        self.log_round["tenant_name"] = name
        self.log_round["available_times"] = available_times
        
    def set_forum_conclusion(self,return_infos):
        template = """{community_index}:{search_info}{get_shortest_commute_time_str}."""
        
        return_infos_str = [template.format_map({"community_index":community_index,
                                                **search_info}) 
                            for community_index,search_info in return_infos.items()]
        forum_conclusion = "\n".join(return_infos_str) 
        self.log_round["forum_conclusion"] = forum_conclusion
        return return_infos_str
        
    def set_available_community_description(self, community_description):
        self.log_round["community_available_description"] = community_description
    def set_choose_community(self,community_id,reason):
        self.log_round["choose_community_id"] = community_id
        self.log_round["choose_community_reason"] = reason
    def set_available_house_type(self,available_house_type):
        self.log_round["available_house_type"]=available_house_type
    def set_choose_house_type(self,house_type,reason):
        self.log_round["choose_house_type"] = house_type
        self.log_round["choose_house_type_reason"] = reason
    def set_available_house_description(self,housedic):
        house_info_description = "{house_id}: The house is a {house_type} with an area of {house_area} square meters and a monthly rent of {rent_money} yuan." \
                                     "It {balcony} a balcony and {elevator} an elevator. " \
                                     "It's on the {floor}th floor. Its description is that {description}"
        housedes_list = []
        for house_id, house_info in housedic.items():
            h = house_info_description.format(house_id=house_id,
                                                house_type=house_info["house_type"],
                                                house_area=house_info["house_area"],
                                                rent_money=house_info["rent_money"],
                                                balcony=house_info["balcony"],
                                                elevator=house_info["elevator"],
                                                floor=house_info["floor"],
                                                description=house_info["description"],
                                                )
            housedes_list.append(h.replace("\n", ""))
        self.log_round["house_available_description"] = housedes_list
        
    def set_choose_house(self,choose_house_id,reason):
        self.log_round["choose_house_id"] = choose_house_id
        self.log_round["choose_house_reason"] = reason
        
    def set_choose_house_state(self,choose_house_state):
        self.log_round["choose_house_state"] = choose_house_state
        
    def set_comment(self,comment):
        self.log_round["produce_comment"] = comment
    def set_log_list(self):
        if self.log_round!={}:
            self.log_list.append(self.log_round)
            
    def set_message(self,messages):
        template="""{sname}->{rname}:{content}"""
        message_str=[]
        for message in messages:
            message_str.append(template.format(sname=list(message.sender.values())[0],rname=list(message.receiver.values())[0],content=str(message)))
        self.log_round["social_net_message"]=message_str

    def save_data(self):
        self.log_round={}
        # assert os.path.exists(self.save_dir), "no such file path: {}".format(self.save_dir)
        with open("LLM_PublicHouseAllocation/tasks/PHA_50tenant_3community_19house/result/tenantal_system.json", 'w', encoding='utf-8') as file:
            json.dump(self.log_list, file, indent=4,separators=(',', ':'),ensure_ascii=False)
    def reset(self):
        self.log_round={}
        self.log_list=[]
