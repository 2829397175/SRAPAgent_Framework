from langchain.llms import OpenAI   
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
from pydantic import BaseModel
from LLM_PublicHouseAllocation.manager import TenantManager,HouseManager
from LLM_PublicHouseAllocation.involvers import System
from typing import Optional
import re
import asyncio
from LLM_PublicHouseAllocation.llms import APIKeyPool
from tqdm import tqdm
import random
import numpy as np
import copy

class Global_Score(BaseModel):
    tenant_manager:Optional[TenantManager]=None
    system:Optional[System]=None
    save_dir:str=""
    result:dict={}
    llm_pool:Optional[APIKeyPool]=None
    examples :list =[]
    llm_configs:dict = {}
    
    
    def __init__(self,**kargs) -> None:
        super().__init__(**kargs)
        self.rate()
        self.save()

    
    @classmethod
    def initialization(
        cls,
        tenant_manager:TenantManager,
        system:System,
        save_dir:str,
        llm_pool:APIKeyPool,
        llm_configs:dict
    ):
        import os
        if os.path.exists(save_dir):
            with open(save_dir,'r',encoding = 'utf-8') as f:
                result = json.load(f)
        else:
            result = {}
            
#         examples= [ 
# {"reason": "The living area of the house is under my expectation, the condition of the house is poor and there are many potential risks, and the house is not pet-friendly, so I gave it a score of 2.",
# "score": 2},
# {"reason": "The house is quite expensive relative to the pool of houses, and its per capita living area is below the average for my family. Despite it having a balcony and elevator, it is falling apart and not in a safe condition, so I cannot recommend it.",
#  "score": 3},
# {"reason": "The house is more expensive than what I am willing to pay, and it is in a poor condition and needs extensive repairs and updates. The living area is slightly smaller than the average for my family, and the community does not have many convenient amenities nearby.",
# "score": 4},
# {"reason": "This house is rather expensive, costing 2324, which is above my budget of 1500. It does have some desirable features such as sports facilities nearby, supermarkets, restaurants and banks. The square footage is also larger than the average living area of the house and has a balcony. However, the house needs some repairs and updates, and the windows are drafty and basement has a musty smell. Overall, House_2 is an ok option but it is not ideal for my needs.", 
# "score": 5},
# {"reason": "This house costs about 1772, which is within my budget. The square fortage is about 44.30, which is slightly larger than average. The house has balcony and elevator, and is located in a community with sports facilities and a large green area, providing a good living environment. The per capita living area of the house is 22.15, which meets the needs of my family members. The house is in acceptable condition, with basic functions complete and few minor problems, but it may lack some modern facilities or design.",
# "score": 6},
# {"reason": "This house is relatively spacious and is located in a community with many facilities. The rent is also within my budget. However, the sofa in the living room is outdated, and there is no park, subway, shopping mall, or hospital nearby. ",
#  "score": 7},
# {"reason": "This house is very conveniently located, with supermarkets, restaurants, banks, and schools nearby, and the rent is within my budget. The house is modern and well-maintained, with a spacious kitchen and plenty of living area for my family. The elevator and sports facilities are also great bonuses. ",
# "score": 8}]
        
        examples=[]
        return cls(
            tenant_manager=tenant_manager,
            system=system,
            save_dir=save_dir,
            result=result,
            llm_pool = llm_pool,
            examples = examples,
            llm_configs = llm_configs
        )
    
    
    def object_weight_chain(self,llm):
        template="""
        
You are currently participating in a public housing allocation event.You are a tenant, willing to rent a house.     

{role_description}

Next, you may need to rate the quality of the house.You will learn about the four properties of the house, including rent money, average living area, house orientation, and floors. 

rent_money refers to the rent of a house, and you need to evaluate the importance of this indicator based on your budget range.
average_living_area: It refers to the average living area of your family members in a house.
orientation: Refers to the orientation of the house.
floor: Refers to the floor on which the house is located.


Next, please assign weights to these four indicators. The total weight required for the sum of these four indicators is 10.

- Respond in this format:
                        
    rent_money: (The numerical size of the weight (1-10))
    average_living_area: (The numerical size of the weight (1-10))
    orientation:(The numerical size of the weight (1-10))
    floor:(The numerical size of the weight (1-10))

Respond in json format:
"""

        input_variables=["role_description"]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        
        return LLMChain(
            llm=llm, prompt=prompt
        )
    
    def object_order_weight_chain(self,llm):
        template="""
{role_description}  
You are currently participating in a public housing allocation event. You are a tenant, willing to rent a house.     

Next, you may need to rate the quality of the house.You will learn about the four properties of the house, including rent, average living area, house orientation, and floors.Now You need to sort these four attributes according to your preferences and give a ranking.The number of the ranking must be between 1-4.If you decide which attribute is most important when choosing a house, your ranking score is 1 and the least important is 4.
- Respond in this format:
                        
    rent_order_number: (Ranking numbers(1-4))
    average_living_area_order_number: (Ranking numbers(1-4))
    house_orientation_order_number:(Ranking numbers (1-4))
    floors_order_number:(Ranking numbers (1-4))

Respond in json format:
        """
        input_variables=["role_description"]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        
        return LLMChain(
            llm=llm, prompt=prompt
        )
        
    def subject_chain(self,llm):
        template="""
You are a tenant, willing to rent a house. Your task is to rate score for all houses according to your own needs.


Please rate based on the information and properties of the house. Score the house from 1-10, with a higher score indicating the house better meets your requirements.
             
            1 point: The condition of the house is extremely poor, with multiple serious problems, such as structural instability, aging or severe damage to facilities, and it is basically unfit for habitation.

            2 points: The home has obvious flaws and issues, such as an old electrical system, leaks, or broken fixtures that require extensive repairs and updates.

            3 points: The basic functions of the house are acceptable, but there are still many inconveniences, such as aging facilities, many minor repairs, and low comfort.

            4 points: Although the home maintains basic functions, it may lack some comfort or modern facilities, or it may need some repairs and improvements.

            5 points: the house is basically maintained, there are many minor problems, but overall it is still acceptable.

            6 points: The house is in acceptable condition, with basic functions complete and few minor problems, but it may lack some modern facilities or design.

            7 points: The home is in good condition, features are relatively new, well maintained and may only need minor improvements or updates.

            8 points: The house is in very good condition, with modern facilities and good maintenance, providing a comfortable and convenient living environment.

            9 points: The house is almost perfect, has advanced facilities, elegant design, is well maintained and needs almost no improvements.

            10 points: The house is in immaculate condition, has advanced facilities, is elegantly designed, and is well maintained, providing a living experience that exceeds expectations.
            Please rate this house and explain why. 
            
{example}
            
            
{role_description}
            
The information of the house you need to rate:
            
House info:{house_subject_info}
            
- Respond in this format:
            
Reason: (Give reasons why you gave this score, remember to consider \
the convenience of the house, the cleanliness of the house, \
the decoration of the living environment, and so on.)
Score: (Indicates the scoring result, which must be an integer number.)

Respond in json format:
"""  
        input_variables=["role_description","house_subject_info","example"]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        
        return LLMChain(
            llm=llm, prompt=prompt
        )
    
    
        
        
    def rate(self):
        tenant_ids = list(self.tenant_manager.total_tenant_datas.keys())
        group_size = 10
        group_id = 0
        pbar_size = int((len(tenant_ids)-1)/group_size)+1
        pbar=tqdm(range(int(pbar_size)), ncols=100,desc=f"Rating the score of houses: group size {group_size}, groups:{pbar_size}") 
        # pbar.update(group_id)
        while(group_id*group_size<len(tenant_ids)):
            stop_id = group_size*(group_id+1)
            if len(tenant_ids) ==stop_id:
                asyncio.run(self.rate_score(tenant_ids[int(group_id*group_size):],group_id=group_id))            
            else:
                asyncio.run(self.rate_score(tenant_ids[int(group_id*group_size):stop_id],group_id=group_id))            
            group_id+=1
            pbar.update()

    
    
    async def rate_score(self,tenant_ids,group_id):
        pbar_size = len(tenant_ids)
        pbar=tqdm(range(pbar_size), ncols=100,desc=f"group rating, group:{group_id}") 
        async def rate_one_tenant(tenant_id):
            tenant = self.tenant_manager.total_tenant_datas[tenant_id]
            llm = self.llm_pool.get_llm_single(self.llm_configs)
            subject_llm_chain = self.subject_chain(llm)
            
            object_llm_chain = self.object_weight_chain(llm)
            
            if tenant_id not in self.result.keys():
                self.result[tenant_id]={}
            
            
            if "weights" not in self.result[tenant_id].keys():
                rated = False
            else:
                rated = True
            
            while (not rated):
                object_input={
                            "role_description":tenant.get_role_description()
                        }   
                response = await object_llm_chain.arun(object_input)
                response = response.replace("\n","").strip().lower()
        
                
                try:
                        result = json.loads(response)
                        rent_weight=result.get("rent_money")
                        if rent_weight==None:
                            rent_weight=1
                        average_living_area_weight=result.get("average_living_area")
                        if average_living_area_weight==None:
                            average_living_area_weight=1
                        house_orientation_weight=result.get("orientation")
                        if house_orientation_weight==None:
                            house_orientation_weight=1
                        floors_weight=result.get("floor")
                        if floors_weight==None:
                            floors_weight=1
                        weights={"rent_money":rent_weight,
                                 "average_living_area":average_living_area_weight,
                                 "orientation":house_orientation_weight,
                                 "floor":floors_weight}
                        self.result[tenant_id]["weights"] = weights
                        rated = True
                except json.JSONDecodeError as e:
                    try:
                        rent_match = re.search(r'rent_money:\s*(\d+)', response)
                        average_living_area_match = re.search(r'average_living_area:\s*(\d+)', response)
                        house_orientation_match = re.search(r'orientation:\s*(\d+)', response)
                        floors_match= re.search(r'floor:\s*(.+)', response)
                        
                        # 从匹配对象中提取值
                        rent_weight = rent_match.group(1)
                        average_living_area_weight = average_living_area_match.group(1)
                        house_orientation_weight = house_orientation_match.group(1)
                        floors_weight = floors_match.group(1)
                        
                        weights={"rent_money":rent_weight,
                                 "average_living_area":average_living_area_weight,
                                 "orientation":house_orientation_weight,
                                 "floor":floors_weight}
                        self.result[tenant_id]["weights"] = weights
                        rated = True
                        
                    except Exception as e:
                        print(f"Invalid JSON: {e}")  
        
            
            if "ratings" not in self.result[tenant_id].keys():
                self.result[tenant_id]["ratings"] = {}
            
            for idx,house_id in enumerate(self.system.house_manager.data.keys()):
                
                example_template = """\
Reason: {reason}
Score: {score}
"""
                examples = [example_template.format_map(example_args) for example_args in self.examples]
                
                examples_str_template ="""\
Here's some examples:

{examples}

End of example
"""
                
                if self.result[tenant_id]["ratings"].get(house_id,{}).get("llm_score",None) != None:
                    rated = True
                else:
                    rated = False
                    
                while (not rated):
                    input={
                    "role_description":tenant.get_role_description(),
                    "house_info":self.system.get_score_house_description(house_id,tenant),
                    "example":examples_str_template.format(examples = "\n".join(examples)) if len(examples)>=1 else ""
                    }   
                    response = await subject_llm_chain.arun(input)
                    response = response.replace("\n","").strip().lower()
                    
                    try:
                            result = json.loads(response)
                            if isinstance(result,list):
                                assert len(result) ==0
                                result = result[0]
                            if house_id in result.keys():
                                result = result[house_id]
                            self.result[tenant_id]["ratings"].update({house_id:result})
                            
                            
                            score = self.result[tenant_id]["ratings"][house_id].get("score")
                            if score == None:
                                score = self.result[tenant_id["ratings"]][house_id].get("rating")
                                
                            self.result[tenant_id]["ratings"][house_id]["llm_score"] = int(score)
                            rated = True
                    except json.JSONDecodeError as e:
                        try:
                            score_match = re.search(r'score:\s*(\d+)', response)
                            reason_match = re.search(r'reason:\s*(.+)', response)
                            
                            # 从匹配对象中提取值
                            score = score_match.group(1)
                            reason = reason_match.group(1)
                            # 创建结果字典
                            result_dict = {
                                "llm_score": int(score),
                                "reason": reason.replace("\"","").strip("score")
                            }
                            self.result[tenant_id]["ratings"].update({house_id:result_dict})
                            rated = True
                        except Exception as e:
                            try:
                                score_match = re.search(r'"score":\s*(\d+)', response)
                                reason_match = re.search(r'"reason":\s*(.+)', response)
                                
                                # 从匹配对象中提取值
                                score = score_match.group(1)
                                reason = reason_match.group(1)
                                # 创建结果字典
                                result_dict = {
                                    "llm_score": int(score),
                                    "reason": reason.replace("\"","").strip("score")
                                }
                                self.result[tenant_id]["ratings"].update({house_id:result_dict})
                                rated = True
                            except:
                                print(f"Invalid JSON: {e}")   
                            
                        
                            # self.result[tenant_id].update({house_id:{"score": 0, "reason": ""}})
                    if (idx%10 ==0):
                        self.save()         

            
                # if self.result[tenant_id]["ratings"].get(house_id,{}).get("objective_score",None) == None:
                objective_scores = self.objective_eval_house(tenant_id=tenant_id,house_id=house_id,weights=self.result[tenant_id]["weights"])
                self.result[tenant_id]["ratings"][house_id].update(objective_scores)
                
                # if self.result[tenant_id]["ratings"].get(house_id,{}).get("score",None) == None:
                self.result[tenant_id]["ratings"][house_id]["score"] = (self.result[tenant_id]["ratings"][house_id]["llm_score"]+\
                                                        self.result[tenant_id]["ratings"][house_id]["objective_score"])
            print(f"tenant {tenant_id} finished rating.")            
            pbar.update()
            
        await asyncio.gather(*[rate_one_tenant(tenant_id) for tenant_id in tenant_ids])
            
            
    def objective_eval_house(self,
                             tenant_id,
                             house_id,
                             weights):
        house_info = self.system.house_manager[house_id]
        tenant = self.tenant_manager.total_tenant_datas[tenant_id]

        tenant_info = tenant.infos
        ratings = []
        
        rent_price = float(house_info["rent_money"])
        budget_price = float(tenant_info["monthly_rent_budget"])
        if rent_price < budget_price:
            rating = 10
        else:
            rating = 10 - int((rent_price-budget_price)/100)
        ratings.append(rating)
            
        family_num = int(tenant_info["family_members_num"])
        house_area = float(house_info["house_area"])
        avg_living_area = house_area/family_num
        if avg_living_area>20:
            rating = 10
        elif avg_living_area>15:
            rating = 8
        elif avg_living_area>10:
            rating = 6
        else:
            rating = int(avg_living_area) - 5
        ratings.append(rating)
        
        house_orientation = house_info["toward"]
        if "S" in house_orientation:
            rating = 10
        elif "W" or "E" in house_orientation:
            rating = 5
        else:
            rating = 0
        ratings.append(rating)
        
        if int(house_info["floor"])>6 and \
            "not" in house_info["elevator"]:
            rating = 0
        else:
            rating = 10
        ratings.append(rating)
        
        ratings_dict = {
            "rent_money_score":ratings[0],
            "average_living_area_score":ratings[1],
            "orientation_score":ratings[2],
            "floor_score":ratings[3]}
        
        weights_list = []
        for k in ratings_dict.keys():
            k_weight = k.replace("_score","")
            weights_list.append(weights[k_weight])
        
        rating_weighted = np.dot(weights_list,ratings)/sum(weights_list)
        assert rating_weighted <=10,'Error'
        
        ratings_dict.update({
            "objective_score":rating_weighted
        })
        return ratings_dict

            
    def save(self):
        with open(self.save_dir, 'w', encoding='utf-8') as file:
            json.dump(self.result, file, indent=4,separators=(',', ':'),ensure_ascii=False)


    def get_result(self):
        return self.result
     
