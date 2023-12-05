
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.prompts import BaseChatPromptTemplate
from langchain import SerpAPIWrapper, LLMChain
from langchain.chat_models import ChatOpenAI
from typing import List, Union
from langchain.schema import AgentAction, AgentFinish, HumanMessage
import re
import yaml
import os
import json
import asyncio
import random
from tqdm import tqdm
import platform

if platform.system()=='Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class OutputParseError(BaseException):
    """Exception raised when parsing output from a command fails."""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "Failed to parse output of the model:%s\n " % self.message

class CustomOutputParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        
        # Parse out the action and action input
        regex = r"Thought\s*\d*\s*:(.*?)Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*?)\n"
        llm_output +="\n"
        
        match = re.search(regex, llm_output, re.DOTALL|re.IGNORECASE)
        
        
        if not match:
            raise OutputParseError("Output Format Error(choose)")
        
        
        thought = match.group(1).strip().strip(" ").strip('"')
        action = match.group(2).strip()
        action_input = match.group(3).strip().strip(" ").strip('"')

        
        if action.lower() == "choose":
            return AgentFinish(return_values={"output":
                                            {"output":action_input,
                                                "thought":thought}},
                            log=llm_output)
        elif action.lower()=="giveup":
            return AgentFinish(return_values={"output":
                                            {"output":action_input,
                                                "thought":thought}},
                            log=llm_output)
        
        # Return the action and action input
        raise OutputParseError("Output Format Error(choose)")


import unicodedata
def is_chinese(strs):
    for _char in strs:
        if '\u4e00' <= _char <= '\u9fa5':
            return True
    return False

# Set up a prompt template
class CustomPromptTemplate(BaseChatPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]
    
    

    
    def format_messages(self, **kwargs) -> str:
        
        formatted = self.template.format(**kwargs)
        return [HumanMessage(content=formatted)]



class Robot_Simulater():
    def __init__(self):
        
        prompt_path = "LLM_PublicHouseAllocation/utils/chat_prompt.yaml"
        prompt_yaml = yaml.safe_load(open(prompt_path,encoding="utf-8"))
        self.prompt_templates = prompt_yaml
        
        self.apis_a=[
            "sk-n96DTK9y2MV9oS6m1eBc68E6C4Ab419b95F68f91F8A4C6Fc",
            "sk-UduOWZ3yEtC9mFxy52397cB469884a288f6dC565Fd33377d",
            "sk-IBDKadyW7ri8QTRJEdA4F5C9694d40138b5f0d1e43FcE52d",
            "sk-ijlq4P88sm3XymKi86Ff380a07Dd48F39c9c4eCc0555BcE8",
            "sk-cIrswbIqa0Josai1263f2aA963A94d7eA224B843BaBb4dE4",
            "sk-ZFwHPfw86b6sRdAOEe3dE7508dE0451596Da9a18613f6d2c",
            "sk-CImwWzGewBSmm6aR4d69016423Ed42C9Ad90585e510386C9"]
    
        self.apis_u =[]
        self.output_parser = CustomOutputParser()
        self.tenant_json = readinfo("LLM_PublicHouseAllocation/tasks/PHA_70tenant_5community_100house/data/tenant_70.json")
    
    def get_llm(self):
        if self.apis_a == []:
            self.apis_a = self.apis_u
            self.apis_u = []
        
        api = self.apis_a.pop()
        self.apis_u.append(api)
        llm = ChatOpenAI(
                        # model_name="gpt-3.5-turbo-16k-0613",
                        model_name="gpt-4",
                       verbose = False,
                       max_tokens = 3000,
                       openai_api_key=api
                       )  
        return llm   
    
    def chain(self,prompt):
        
        llm = self.get_llm()
        chain = LLMChain(llm=llm, prompt=prompt)
        return chain
    

    def get_update_role_description(self,role_description):
        regex = r"Your budget for renting a house for (\d+.\d+).Your acceptable price beyond the rental budget is (\d+)."
        try:
            match = re.search(regex, role_description, re.DOTALL|re.IGNORECASE)
            
            rent_budget = int(float(match.group(1)))
            rent_outrange = int(match.group(2))
            
            role_description_b = "Your budget for renting a house for {budget}.The maximum rent you can accept is {max_budget}. "
            role_description_b = role_description_b.format(budget = rent_budget,
                                                    max_budget = rent_budget+rent_outrange)
            
            role_description = role_description.replace(match.group(0),role_description_b)
            
            return role_description
        except:
            return role_description
        
    async def get_robot_response(self,
                        type_data,
                        prompt_inputs,
                        ):
       
        prompt_template = self.prompt_templates["choose_template"]
        # LLM chain consisting of the LLM and a prompt
        prompt = CustomPromptTemplate(
            template=prompt_template,
            tools=[],
            # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
            # This includes the `intermediate_steps` variable because that is needed
            input_variables=["task", 
                     "role_description",
                     "house_info",
                     "thought_type",
                     "thought_hint",
                     "choose_type",
                     "memory",
                     "agent_scratchpad"])
        
        llm_chain = self.chain(prompt=prompt)
        
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain, 
            output_parser=self.output_parser,
            stop=["\nObservation"],
            allowed_tools=[]
        )

        agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=[], verbose=True)
        input_arguments = prompt_inputs
        
        input_prompt_types={
            "community":{
                'thought_hint':"""Remember to consider the following things before choosing community:
1. The price, location of this community should be taken into consideration.
2. Remember to give the reason why the selected community meets your needs in thought(exp. \
This community meets my request for a walk in the nearby park).
3. If you have already made a choice of community in your memory, 
You can choose to abandon all the current residential areas and wait for the ones you want to be released later (choose Giveup Action)\
Alternatively, provide specific reasons for why you want to abandon the previously selected residential area and change your choice
4. You can choose to give up if none of these communities meet your requiremtent, but remember to consider your valuable chances to choose house you have within the queue \
and the remaining chances you have to select a house.""",
                'thought_type':"请用【中文】输出你对于这些小区的评价，以及做出决策的原因； 请注意放弃的情况同样用【中文】给出原因"
            },
            "housetype":{
                'thought_hint':"""Remember to consider the following things before choosing house:
1. The price of this house type should be within your budget.
2. The per capita living area should be taken into consideration.
3. Remember to give the reason why the selected house type meets your needs in thought(exp. \
My family has a large population and needs a larger house to live in)
4. You can choose to give up if none of these house types meet your requiremtent, \
but remember to consider your valuable chances to choose house you have within the queue \
and the remaining chances you have to select a house.""",
                'thought_type':"请用【中文】输出你对于这些房屋类型的评价，以及做出决策的原因； 请注意放弃的情况同样用【中文】给出原因"
            },
            "house":{
                'thought_hint':"""Remember to consider the following things before choosing house:
1. The price of this house should be within your budget.
2. The per capita living area should be taken into consideration.
3. Remember to give specific reason why the selected house meets your needs in thought (exp. \
This house meets my requirement of having a elevator).
4. You can choose to give up if none of these houses meet your requiremtent, \
but remember to consider your valuable chances to choose house you have within the queue \
and the remaining chances you have to select a house.""",
                'thought_type':"请用【中文】输出你对于这些房屋的评价，以及做出决策的原因；请注意放弃的情况同样用【中文】给出原因"
            },
            
        }
        
        input_prompt_types={
            "community":{
                'thought_hint': """在选择小区之前，请记住考虑以下事项：
1. 应考虑该小区的价格和位置。
2. 请在思考中说明为什么选择的小区符合您的需求（例如：这个小区符合我附近有公园散步的要求）。
3. 如果您已经在记忆中选择了一个小区，
   您可以选择放弃当前所有的居住区，并等待后续的选择释放（选择“放弃行动”），
   或者提供具体的原因，解释为什么要放弃先前选择的居住区并改变选择。
4. 如果这些小区都不符合您的要求，您可以选择放弃，但请记住要考虑您在队列中拥有的选择住房的机会，
   以及您选择房屋的剩余机会。""",
                'thought_type':"请用【中文】输出你对于这些小区的评价，以及做出决策的原因； 请注意放弃的情况同样用【中文】给出原因"
            },
            "housetype":{
                'thought_hint': """在选择房屋类型之前，请记住考虑以下事项：
1. 该房屋类型的价格应在您的预算范围内。
2. 应考虑每人的居住面积。
3. 请在思考中说明为什么选择的房屋类型符合您的需求（例如：我的家庭人口众多，需要一个更大的住房）。
4. 如果这些房屋类型都不符合您的要求，您可以选择放弃，但请记住要考虑您在队列中拥有的选择住房的机会，
   以及您选择房屋的剩余机会。""",
                'thought_type':"请用【中文】输出你对于这些房屋类型的评价，以及做出决策的原因； 请注意放弃的情况同样用【中文】给出原因"
            },
            "house":{
                'thought_hint':"""在选择房屋之前，请记住考虑以下事项：
1. 该房屋的价格应在您的预算范围内。
2. 应考虑每人的居住面积。
3. 请具体说明为什么选择的房屋符合您的需求（例如：这个房屋满足我需要有电梯的要求）。
4. 如果这些房屋都不符合您的要求，您可以选择放弃，但请记住要考虑您在队列中拥有的选择住房的机会，
   以及您选择房屋的剩余机会。""",
                'thought_type':"请用【中文】输出你对于这些房屋的评价，以及做出决策的原因；请注意放弃的情况同样用【中文】给出原因"
            },
            
        }
        
        input_arguments.update(input_prompt_types[type_data])
        choose_chinese_vers = ["我的选择是",
                               "我选择",
                               "我决定选择",
                               "我的选择是",
                               "我想选",
                               "我的选择是"]
        
        chinese_ver = random.sample(choose_chinese_vers,1)[0]
        input_arguments["choose_type"] = input_arguments["choose_type"].replace("My choice is",chinese_ver)
        input_arguments['agent_scratchpad']=""
        role_des = input_arguments["role_description"]
        input_arguments["role_description"] = self.get_update_role_description(role_des)
        
        for i in range(5):
            try:
                response = await agent_executor.arun(input_arguments)
                return response
            except:continue
        return None
            

def readinfo(data_dir):
    assert os.path.exists(data_dir),"no such file path: {}".format(data_dir)
    with open(data_dir,'r',encoding = 'utf-8') as f:
        data_list = json.load(f)
    return data_list

async def get_all_robot_response():
    
    data_paths =[
        # "LLM_PublicHouseAllocation/LLM_decision_test/11_26_data/denotes_save_response/0.json",
        # "LLM_PublicHouseAllocation/LLM_decision_test/11_26_data/denotes_save_response/2.json",
        # "LLM_PublicHouseAllocation/LLM_decision_test/11_26_data/denotes_save_response/5.json",
        # "LLM_PublicHouseAllocation/LLM_decision_test/11_28_data/denotes_save_response/28_1.json"
        # "LLM_PublicHouseAllocation/LLM_decision_test/11_28_data/denotes_save_response/28_2.json",
        # "LLM_PublicHouseAllocation/LLM_decision_test/11_26_data/denotes_save_response/6.json",
        "LLM_PublicHouseAllocation/LLM_decision_test/11_28_data/denotes_save_response/28_0.json"
        ]
            
    
    simulator = Robot_Simulater()
    
    async def async_simulate_one_type(data_path,
                                      robot_response_key = "robot_response"):

        data_responses = readinfo(data_path)

        pbar_size =len(data_responses)
        pbar=tqdm(range(int(pbar_size)), ncols=100,desc=f"simulating {os.path.basename(data_path)}") 

        
        
        for response in data_responses:
            done = False
            
            if "community" in response["prompt_inputs"]["choose_type"]:
                data_type = "community"
            elif "house type" in response["prompt_inputs"]["choose_type"]:
                data_type = "housetype"
            else:
                data_type = "house"
            
            for i in range(5):
                
                if robot_response_key in response.keys():
                    robot_response = response[robot_response_key]
                    thought = robot_response["thought"]
                    output = robot_response["output"].strip()
                    if is_chinese(thought):
                        if "放弃" in output:
                            done = True
                            break
                        if data_type == "housetype":
                            if "small" in output or \
                                "middle" in output or \
                                "large" in output:
                                done = True
                                break
                        else:
                            if data_type in output:
                                done = True
                                break
                    else:
                        pass
                    

                response_robot = await simulator.get_robot_response(data_type,response["prompt_inputs"])
                if response_robot == None:
                    continue
                response[robot_response_key] = response_robot
            
            pbar.update()
        
        
        with open(data_path,'w',encoding = 'utf-8') as f:
            json.dump(data_responses, f, indent=4,separators=(',', ':'),ensure_ascii=False)  
    
    # await asyncio.gather(*[async_simulate_one_type(data_path=data_path,
    #                                                robot_response_key="robot_response_3.5_chinese") 
    #                        for data_path in data_paths])
    await asyncio.gather(*[async_simulate_one_type(data_path=data_path,
                                                   robot_response_key="robot_response_4_chinese") 
                           for data_path in data_paths])

            
            

   
if __name__ =="__main__":
    asyncio.run(get_all_robot_response())