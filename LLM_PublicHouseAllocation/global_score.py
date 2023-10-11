from langchain.llms import OpenAI   
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
from pydantic import BaseModel
from LLM_PublicHouseAllocation.manager import TenantManager,HouseManager
from LLM_PublicHouseAllocation.involvers import System
from typing import Optional
import re

from tqdm import tqdm

class Global_Score(BaseModel):
    tenant_manager:Optional[TenantManager]=None
    system:Optional[System]=None
    save_dir:str=""
    result:dict={}
    llm: Optional[LLMChain]=None
    @classmethod
    def initialization(
        cls,
        tenant_manager:TenantManager,
        system:System,
        save_dir:str
    ):
        llm = OpenAI(temperature=1)
        template="""
            {role_description}\
            {house_info}
            {example}
            Please rate based on the information and properties of the house. 
            1 point: Very dissatisfied - The condition of the house is extremely poor, with multiple serious problems, such as structural instability, aging or severe damage to facilities, and it is basically unfit for habitation.

            2 points: Very Unsatisfactory - The home has obvious flaws and issues, such as an old electrical system, leaks, or broken fixtures that require extensive repairs and updates.

            3 points: Unsatisfactory - The basic functions of the house are acceptable, but there are still many inconveniences, such as aging facilities, many minor repairs, and low comfort.

            4 points: Unsatisfactory - Although the home maintains basic functions, it may lack some comfort or modern facilities, or it may need some repairs and improvements.

            5 points: Slightly dissatisfied - the house is basically maintained, there are many minor problems, which may affect the daily life of the residents, but overall it is still acceptable.

            6 points: Passing - The house is in acceptable condition, with basic functions complete and few minor problems, but it may lack some modern facilities or design.

            7 points: Satisfactory - The home is in good condition, features are relatively new, well maintained and may only need minor improvements or updates.

            8 points: Very satisfied - the house is in very good condition, with modern facilities and good maintenance, providing a comfortable and convenient living environment.

            9 points: Extremely Satisfied - The house is almost perfect, has advanced facilities, elegant design, is well maintained and needs almost no improvements.

            10 points: Completely satisfied - the house is in immaculate condition, has advanced facilities, is elegantly designed, and is well maintained, providing a living experience that exceeds expectations.
            Please rate this house and explain why. 

            -The required results must conform to the following format of output results:

            Score: Indicates the scoring result, which must be an integer number. 
            Reason: Give reasons why you gave this score

            Return using JSON format.
        """  
        input_variables=["role_description","house_info","example"]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        chain = LLMChain(llm=llm, prompt=prompt)

        return cls(
            tenant_manager=tenant_manager,
            system=system,
            save_dir=save_dir,
            result={},
            llm=chain
        )
    
    def rate_score(self):
        for tenant_id,tenant in tqdm(self.tenant_manager.data.items(),desc="Rating the score of houses."):
            self.result[tenant_id]={}
            for house_id,_ in self.system.house_manager.data.items():
                input={
                    "role_description":tenant.get_role_description(),
                    "house_info":self.system.get_score_house_description(house_id),
                    "example":""
                }
                response=self.llm.run(input)
                response=response.replace("\n","").strip().lower()
                score_match = re.search(r'score:\s*(\d+)', response)
                reason_match = re.search(r'reason:\s*(.+)', response)
                if score_match and reason_match:
                    # 从匹配对象中提取值
                    score = score_match.group(1)
                    reason = reason_match.group(1)
                    # 创建结果字典
                    result_dict = {
                        "score": int(score),
                        "reason": reason
                    }
                    self.result[tenant_id].update({house_id:result_dict})
                else:
                    try:
                        result=json.loads(response)
                        self.result[tenant_id].update({house_id:result})
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON: {e}")   
                        self.result[tenant_id].update({house_id:{"Score": 0, "Reason": ""}})
            
    def save_score(self):
        with open(self.save_dir, 'w', encoding='utf-8') as file:
            json.dump(self.result, file, indent=4,separators=(',', ':'),ensure_ascii=False)


     
