from pydantic import BaseModel
import json
import time
import copy
import os

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
                           step_type,
                           key_social_network):
        
        key_social_network += 1
        
        if round_index not in self.log_social_network.keys():
            self.log_social_network[round_index] = {}
        
        if step_type == "group_discuss_back":
            if "group_discuss_back" not in self.log_social_network[round_index].keys():
                self.log_social_network[round_index][step_type] = []
            
            self.log_social_network[round_index][step_type].append({
                "prompt_inputs":prompt_inputs,
                "response":response,
                "id":id,
                "name":name,
                "key_social_network":key_social_network
            } )
            
            
        else:
            self.log_social_network[round_index][step_type] = {
                "prompt_inputs":prompt_inputs,
                "response":response,
                "id":id,
                "name":name,
                "key_social_network":key_social_network
            }   
            
        
        return key_social_network
            
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
        template = """{community_index}:{search_info}
It only takes {get_shortest_commute_time_str} to commute to my workplace."""
        
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
        
    def set_choose_house_rating_score(self,ratings):
        self.log_round["choose_house_ratings"] = ratings
        if len(rating_scores)>0:
            rating_scores =[rating[1] for rating in ratings]
            self.log_round["utility"] = sum(rating_scores)/len(rating_scores)
        else:
            self.log_round["utility"] = 0
        
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
    
    
    def evaluation_matrix(self,
                          tenant_manager,
                          global_score,
                          system): # 评价系统的公平度，满意度
        
        save_dir = os.path.dirname(self.save_dir)
        
        """this function must be called at the end of running this system."""
        
        
        # 这部分的计算代码：侵入式的utility评价 ，已经抛弃
        # utility = {}
        # for log_id,log in self.log.items():
        #     log_round = log["log_round"]
        #     if log_id == "group":
        #         continue
        #     for tenant_id, tenant_info in log_round.items():
        #         ratings = tenant_info["choose_house_ratings"]
        #         rating_houses = {}
        #         for rating_round,rating_score in ratings.items():
        #             for rating_pair in rating_score:
        #                 if rating_pair[0] not in rating_houses.keys():
        #                     rating_houses[rating_pair[0]] = [rating_pair[1]]
        #                 else:
        #                     rating_houses[rating_pair[0]].append(rating_pair[1])
        #         for k,v in rating_houses.items():
        #             v = sum(v)/len(v)
                    
        #         rating_score_vis_u = sum(list(rating_houses.values()))/len(rating_houses)
        #         rating_score_choose_u = rating_houses[tenant_info["choose_house_id"]]
        #         group_id_t = -1
        #         for group_id,tenant_ids in tenant_manager.groups.items():
        #             if tenant_id in tenant_ids:
        #                 group_id_t = group_id
        #                 break
                    
        #         utility[tenant_id] = {
        #             "vis_u":rating_score_vis_u,
        #             "choose_u":rating_score_choose_u,
        #             "group_id":group_id_t 
        #         } 
                
        utility = global_score.get_result()
        utility_choosed = {}
        for log_id,log in self.log.items():
            log_round = log["log_round"]
            if log_id == "group":
                continue
            for tenant_id, tenant_info in log_round.items():
                if "choose_house_id" in tenant_info.keys():
                    rating_score_choose_u = utility[str(tenant_id)][tenant_info["choose_house_id"]]
                    group_id_t = -1
                    for group_id,tenant_ids in tenant_manager.groups.items():
                        if tenant_id in tenant_ids:
                            group_id_t = group_id
                            break
                    assert tenant_id not in utility_choosed.keys(),f"Error!! Tenant {tenant_id} chosing house twice."
                    tenant = tenant_manager.data[tenant_id]
                    utility_choosed[tenant_id] = {
                                "choose_u":rating_score_choose_u,
                                "group_id":group_id_t,
                                "priority": all(not value for value in tenant.priority_item.values()),
                                "choose_house_id":tenant_info["choose_house_id"]
                            } 
                
        
        import pandas as pd
        import numpy as np
        
        utility_matrix = pd.DataFrame()
        for tenant_id,utility_one in utility_choosed.items():
            for k,v in utility_one.items():
                utility_matrix.loc[tenant_id,k] = v
        utility_matrix.to_csv(os.path.join(save_dir,"utility_choosed.csv"))
        
        utility_eval_matrix = pd.DataFrame()

        """各个组内的公平性、满意度打分"""
        utility_grouped = utility_matrix.groupby(by = ["group_id"])
        
        for group_id, group_utility in utility_grouped:
            # 公平度
            
            scores = group_utility["choose_u"]
            utility_eval_matrix.loc[f"least_misery",group_id] = min(scores)
            utility_eval_matrix.loc[f"variance",group_id] = 1 - np.var(scores)
            utility_eval_matrix.loc[f"jain'sfair",group_id] = np.square(np.sum(scores))/(np.sum(np.square(scores)) * utility_matrix.size[0])
            utility_eval_matrix.loc[f"min_max_ratio",group_id] = np.min(scores)/np.max(scores)
            
            # 满意度
            utility_eval_matrix.loc[f"sw",group_id] = np.sum(scores)/group_utility.size[0]
                
        """弱势群体的公平度"""
        # utility_grouped = utility_matrix.groupby(by = ["priority"])
        # for priority_lable, group_utility in utility_grouped:
        #     scores = group_utility["choose_u"]
        utility_p = utility_matrix[utility_matrix["priority"]]
        utility_np = utility_matrix[not utility_matrix["priority"]]
        utility_eval_matrix.loc["F(W,G)","utility"] = np.sum(utility_p["choose_u"])/utility_p.size[0] -\
            np.sum(utility_np["choose_u"])/utility_np.size[0]
        
        utility_eval_matrix.loc["SW","utility"] = np.sum(utility_matrix["choose_u"])
        
        """计算基尼指数,原本的定义是将收入分配作为输入,
        这里为了衡量公平性, 将房屋分配的utitlity作为输入"""
        # Calculate Gini coefficient and Lorenz curve coordinates
        gini, x, y = self.calculate_gini(utility_matrix["choose_u"])
        import matplotlib.pyplot as plt
        # Plot the Lorenz curve
        plt.figure(figsize=(6, 6))
        plt.plot(x, y, marker='o', linestyle='-', color='b')
        plt.plot([0, 1], [0, 1], linestyle='--', color='k')
        plt.fill_between(x, x, y, color='lightgray')
        plt.xlabel("Cumulative % of Population")
        plt.ylabel("Cumulative % of Income/Wealth")
        plt.title(f"Lorenz Curve (Gini Index: {gini:.2f})")
        plt.grid(True)
        plt.show()
        
        utility_eval_matrix.loc["GINI_index","utility"] = gini
        
        
        utility_eval_matrix.to_csv(os.path.join(save_dir,"utility_eval_matrix.csv"))

        
        
        """一些客观的指标（例如人均住宅面积）"""
        objective_evaluation = pd.DataFrame()
        for tenant_id, choosed_info in utility_choosed.items():
            house_id  = choosed_info["choose_house_id"]
            utility_matrix.loc[tenant_id,"family_members_num"] = tenant_manager[tenant_id].get("family_members_num")
            try:
                house_size = system.house_manager.data.get(house_id).get("house_area")
                house_size = float(house_size.strip())
                utility_matrix.loc[tenant_id,"house_size"] = house_size

                
            except Exception as e:
                utility_matrix.loc[tenant_id,"house_size"] = None
        
        utility_matrix_objective = utility_matrix[utility_matrix["house_size"]!=None]
        utility_matrix_objective["avg_area"] = utility_matrix_objective["house_size"]/utility_matrix_objective["family_members_num"]
        
        utility_matrix_objective_grouped = utility_matrix_objective.groupby(by = ["group_id"]) 
        
        for group_id,group_matrix in utility_matrix_objective_grouped:
            objective_evaluation.loc["mean_house_area",group_id] = np.average(group_matrix["avg_area"])
            
        objective_evaluation.to_csv(os.path.join(save_dir,"objective_evaluation_matrix.csv"))
    

        
        
    def calculate_gini(self,data):
        import numpy as np
        # Sort the data in ascending order
        data = np.sort(data)
        
        # Calculate the cumulative proportion of income/wealth
        cumulative_income = np.cumsum(data)
        
        # Calculate the Lorenz curve coordinates
        x = np.arange(1, len(data) + 1) / len(data)
        y = cumulative_income / np.sum(data)
        
        # Calculate the area under the Lorenz curve (A)
        area_under_curve = np.trapz(y, x)
        
        # Calculate the area under the line of perfect equality (B)
        area_perfect_equality = 0.5
        
        # Calculate the Gini coefficient
        gini_coefficient = (area_perfect_equality - area_under_curve) / area_perfect_equality
        
        return gini_coefficient, x, y