from pydantic import BaseModel
import json
import time
import copy
# Design a basic LogRound class
class LogRound(BaseModel):
    round_id :int = 0 # 标注是哪一轮的  
    # 所有轮数的log
    # round_id : {log_round,log_social_network}
    log: dict = {}
    
    # 某一轮内部 选择过程的log (choose过程)
    log_round:dict = {} 
    log_round_prompts:dict = {}
    
    # social_network_mem: 关于一轮对话结束后每个人的memory变化情况
    # social_network: 关于一轮对话里，每个人经过的所有trajectory的 prompt和 输出的内容
    log_social_network:dict={} 
    save_dir:str=""
    
    def step(self):
        if self.round_id != 0:
            self.log[self.round_id][ "log_social_network"] = copy.deepcopy(self.log_social_network)
            
        self.round_id += 1
        self.log[self.round_id] = {} # 下一轮log的 initialize
    
    def set_one_tenant_choose_process(self,tenant_id):
        if self.round_id > 0:
            if "log_round" not in self.log[self.round_id].keys():
                self.log[self.round_id]["log_round"] = {}
            if "log_round_prompts" not in self.log[self.round_id].keys():
                self.log[self.round_id]["log_round_prompts"] = {}
            if tenant_id in self.log[self.round_id]["log_round"].keys():
                self.log[self.round_id]["log_round"][tenant_id].update(copy.deepcopy(self.log_round))
            else:
                self.log[self.round_id]["log_round"][tenant_id] = copy.deepcopy(self.log_round)
            if tenant_id in self.log[self.round_id]["log_round_prompts"].keys():
                self.log[self.round_id]["log_round_prompts"][tenant_id].update(copy.deepcopy(self.log_round_prompts))
            else:
                self.log[self.round_id]["log_round_prompts"][tenant_id] = copy.deepcopy(self.log_round_prompts)
    
    
    def set_group_log(self,tenant_id):
        if "group" not in self.log.keys():
            self.log["group"] = {}
        self.log["group"][tenant_id] = {
            "log_round" : copy.deepcopy(self.log_round),
            "log_round_prompts": copy.deepcopy(self.log_round_prompts)
        }
    
    
    def save_social_network(self,
                            dir:str):
        
        with open(dir, encoding='utf-8', mode='w') as fr:
            json.dump(self.log_social_network, fr, indent=4, separators=(',', ':'), ensure_ascii=False)
            
    def set_social_network_mem(self,social_network_mem:dict):
        self.log_social_network["social_network_mem"] = social_network_mem
        
    def set_social_network(self,
                           prompt_inputs,
                           response,
                           id,
                           name,
                           round_index, #轮内第几个发言
                           step_type):
        if round_index not in self.log_social_network.keys():
            self.log_social_network[round_index] = {}
        
        if step_type == "group_discuss_back":
            if "group_discuss_back" not in self.log_social_network[round_index].keys():
                self.log_social_network[round_index][step_type] = []
            
            self.log_social_network[round_index][step_type].append({
                "prompt_inputs":prompt_inputs,
                "response":response,
                "id":id,
                "name":name
            } )
        else:
            self.log_social_network[round_index][step_type] = {
                "prompt_inputs":prompt_inputs,
                "response":response,
                "id":id,
                "name":name
            }   
            
    def set_choose_history(self,
                           step_type,
                           **kwargs):
        self.log_round_prompts[step_type] = kwargs
        
        
    def init_log_round_from_dict(self, kwargs):
        self.log_round = kwargs 
    
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
        
    def get_choose_community(self):
        assert "choose_community_id" in self.log_round.keys(), "Not chosen community yet"
        return self.log_round["choose_community_id"],self.log_round["choose_community_reason"]
        
    def set_available_house_type(self,available_house_type):
        self.log_round["available_house_type"] = available_house_type
        
    def set_choose_house_type(self,house_type,reason):
        self.log_round["choose_house_type"] = house_type
        self.log_round["choose_house_type_reason"] = reason
        
    def set_choose_house_orientation(self,house_orientation,reason):
        self.log_round["choose_house_orientation"] = house_orientation
        self.log_round["choose_house_orientation_reason"] = reason
        
    def set_choose_floor_type(self,floor_type,reason):
        self.log_round["choose_floor_type"] = floor_type
        self.log_round["choose_floor_type_reason"] = reason
        
        
    def get_choose_house_type(self):
        assert "choose_house_type" in self.log_round.keys(), "Not chosen house type yet"
        return  self.log_round["choose_house_type"],self.log_round["choose_house_type_reason"]
        
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
            
    def set_message(self,messages):
        template="""{sname}->{rname}:{content}"""
        message_str=[]
        for message in messages:
            message_str.append(template.format(sname=list(message.sender.values())[0],rname=list(message.receiver.values())[0],content=str(message)))
        self.log_round["social_net_message"]= copy.deepcopy(message_str)

    def save_data(self):
        self.log_round={}
        with open(self.save_dir, 'w', encoding='utf-8') as file:
            json.dump(self.log, file, indent=4,separators=(',', ':'),ensure_ascii=False)

    def reset(self):
        self.log_round={}
        self.log={}
