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
            
        examples= [ 
{"reason": "The living area of the house is under my expectation, the condition of the house is poor and there are many potential risks, and the house is not pet-friendly, so I gave it a score of 2.",
"score": 2},
{"reason": "The house is quite expensive relative to the pool of houses, and its per capita living area is below the average for my family. Despite it having a balcony and elevator, it is falling apart and not in a safe condition, so I cannot recommend it.",
 "score": 3},
{"reason": "The house is more expensive than what I am willing to pay, and it is in a poor condition and needs extensive repairs and updates. The living area is slightly smaller than the average for my family, and the community does not have many convenient amenities nearby.",
"score": 4},
{"reason": "This house is rather expensive, costing 2324, which is above my budget of 1500. It does have some desirable features such as sports facilities nearby, supermarkets, restaurants and banks. The square footage is also larger than the average living area of the house and has a balcony. However, the house needs some repairs and updates, and the windows are drafty and basement has a musty smell. Overall, House_2 is an ok option but it is not ideal for my needs.", 
"score": 5},
{"reason": "This house costs about 1772, which is within my budget. The square fortage is about 44.30, which is slightly larger than average. The house has balcony and elevator, and is located in a community with sports facilities and a large green area, providing a good living environment. The per capita living area of the house is 22.15, which meets the needs of my family members. The house is in acceptable condition, with basic functions complete and few minor problems, but it may lack some modern facilities or design.",
"score": 6},
{"reason": "This house is relatively spacious and is located in a community with many facilities. The rent is also within my budget. However, the sofa in the living room is outdated, and there is no park, subway, shopping mall, or hospital nearby. ",
 "score": 7},
{"reason": "This house is very conveniently located, with supermarkets, restaurants, banks, and schools nearby, and the rent is within my budget. The house is modern and well-maintained, with a spacious kitchen and plenty of living area for my family. The elevator and sports facilities are also great bonuses. ",
"score": 8}]
        
        
        return cls(
            tenant_manager=tenant_manager,
            system=system,
            save_dir=save_dir,
            result=result,
            llm_pool = llm_pool,
            examples = examples,
            llm_configs = llm_configs
        )
    
    
    
    
    def chain(self,llm):
        template="""
You are a tenant, willing to rent a house. Your task is to rate score for all houses according to your own needs.

Here's some important background information:

1. The average living area of these houses is around 20 square meters. If the average living area exceeds 20 for you, the house should be relatively spacious, while if it's less than 20, it would be rather cramped.
2. For this pool of houses: the price range is roughly between 900 and 2600, and the house area is approximately 35-65 square meters. Please keep this distribution in mind and evaluate the value of the house relative to this pool of houses.
3. Please remember your persona and make evaluations of the houses that align with that persona.
4. Try to distribute your ratings evenly.


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
            
House info:{house_info}
            
- Respond in this format:
            
Reason: (Give reasons why you gave this score, remember to consider \
the price of the house and your budget, the per capita living area of the house, \
the convenience of the house, the cleanliness of the house, \
the decoration of the living environment, and so on.)
Score: (Indicates the scoring result, which must be an integer number.)

Respond in json format:
"""  
        input_variables=["role_description","house_info","example"]
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
        group_id = 4
        pbar_size = int((len(tenant_ids)-1)/group_size)+1
        pbar=tqdm(range(int(pbar_size)), ncols=100,desc=f"Rating the score of houses: group size {group_size}, groups:{pbar_size}") 
        pbar.update(group_id)
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
            llm_chain = self.chain(llm)
            if tenant_id not in self.result.keys():
                self.result[tenant_id]={}
            
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
                
                input={
                    "role_description":tenant.get_role_description(),
                    "house_info":self.system.get_score_house_description(house_id,tenant),
                    "example":examples_str_template.format(examples = "\n".join(examples)) if len(examples)>=1 else ""
                }
                if self.result[tenant_id].get(house_id,{}).get("score",None) == None:
                    rated = False
                else:
                    rated = True
                    
                while (not rated):
                    response = await llm_chain.arun(input)
                    response = response.replace("\n","").strip().lower()
                    
                    try:
                            result = json.loads(response)
                            if isinstance(result,list):
                                assert len(result) ==0
                                result = result[0]
                            if house_id in result.keys():
                                result = result[house_id]
                            self.result[tenant_id].update({house_id:result})
                            
                            
                            score = self.result[tenant_id][house_id].get("score")
                            if score == None:
                                score = self.result[tenant_id][house_id].get("rating")
                                
                            self.result[tenant_id][house_id]["score"] = int(score)
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
                                "score": int(score),
                                "reason": reason.replace("\"","").strip("score")
                            }
                            self.result[tenant_id].update({house_id:result_dict})
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
                                    "score": int(score),
                                    "reason": reason.replace("\"","").strip("score")
                                }
                                self.result[tenant_id].update({house_id:result_dict})
                                rated = True
                            except:
                                print(f"Invalid JSON: {e}")   
                    
                    
                        
                            # self.result[tenant_id].update({house_id:{"score": 0, "reason": ""}})
                    if (idx%10 ==0):
                        self.save()         
            
            print(f"tenant {tenant.id} finished rating.")            
            pbar.update()
            
        await asyncio.gather(*[rate_one_tenant(tenant_id) for tenant_id in tenant_ids])
            
            
        
            
    def save(self):
        with open(self.save_dir, 'w', encoding='utf-8') as file:
            json.dump(self.result, file, indent=4,separators=(',', ':'),ensure_ascii=False)


    def get_result(self):
        return self.result
     
