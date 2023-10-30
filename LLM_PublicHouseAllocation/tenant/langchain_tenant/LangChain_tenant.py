# from LLM_PublicHouseAllocation.manager import ForumManager
# from LLM_PublicHouseAllocation.involvers import System,Tool,Search_forum_topk
from LLM_PublicHouseAllocation.memory import ActionHistoryMemory
from LLM_PublicHouseAllocation.message import Message
import asyncio
from LLM_PublicHouseAllocation.prompt.chat_prompt import (ForumPromptTemplate,
                                                          ChoosePromptTemplate,
                                                          PublishPromptTemplate,
                                                          CommentPromptTemplate,                                                          
                                                          ActionPlanPromptTemplate,
                                                          GroupDiscussPlanPromptTemplate,
                                                          GroupDiscussPromptTemplate,
                                                          GroupDiscussBackPromptTemplate,
                                                          RelationPromptTemplate,
                                                          chat_prompt_registry)

from LLM_PublicHouseAllocation.output_parser import (OutputParseError,
                                                     ForumParser,
                                                     ChooseParser,
                                                     PublishParser,
                                                     CommentParser,
                                                     GroupDiscussParser,
                                                     ActionPlanParser,
                                                     GroupDiscussPlanParser,
                                                     GroupDiscussBackParser,
                                                     RelationParser,
                                                     output_parser_registry
                                                     )
import LLM_PublicHouseAllocation.map as map

from langchain.agents.agent import Agent as langchainAgent

from langchain.agents.agent import AgentOutputParser
from langchain.agents.conversational_chat.output_parser import ConvoOutputParser
from langchain.base_language import BaseLanguageModel
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
# from langchain.agents import AgentExecutor
from typing import Any, List, Optional, Tuple, Union,Dict
from pydantic import root_validator
from langchain.schema import AgentAction,AgentFinish
from langchain.callbacks.manager import (
    Callbacks,
)
from LLM_PublicHouseAllocation.tenant.langchain_tenant.utils import load_memory

from LLM_PublicHouseAllocation.tenant.langchain_tenant.Langchain_agent_executor import House_AgentExecutor
import re
import random
import copy
from LLM_PublicHouseAllocation.tenant.agent_rule import AgentRule
from LLM_PublicHouseAllocation.tenant.policy import BasePolicy

from LLM_PublicHouseAllocation.tenant.langchain_tenant.tenant_log import Log_Round_Tenant

from openai.error import RateLimitError

class LangchainTenant(langchainAgent):
    id :str
    name :str 
    family_num:int=0
    infos : dict 
    memory : ActionHistoryMemory
    choose_times:int = 0
    max_choose:int = 3
    available:bool = True
    max_jug_time : int = 2 # 错误结果的retry次数
    max_retry:int = 5 #访问api
    workplace: str = ""  # 用来记录工作点的中文名
    # social_network: dict = {}
    mode : str ="choose" # 控制llm_chain 状态（reset_state中改）
    # 这个是为了更改llm_chain
    llm: BaseLanguageModel
    priority_item:dict = {}
    
    agentrule:AgentRule
    queue_name:str=""
    policy: BasePolicy
    choose_rating: bool = False
    
    log_round_tenant: Log_Round_Tenant
    
    llm_config:dict={
        "self":{},
        "memory":{}
    } # 存储llm的参数设置，为了后续改api用
    
    def __init__(self, rule, **kwargs):
        rule_config = rule
        readhouse_config = rule_config.get('readhouse_rule','topk')
        readforum_config = rule_config.get('readforum_rule','topk')
        read_community_config = rule_config.get('readcommunity_rule','available')
        write_forum_config = rule_config.get('writeforum_rule','append')
        rule = AgentRule(readhouse_config,
                         readforum_config,
                         read_community_config,
                         write_forum_config)
        infos = kwargs.pop("infos")
        if "extra_info" in infos.keys():
            infos["extra_info"] = "\nYou sincerely believe this information:{}".format(infos.get("extra_info"))
        else:
            infos["extra_info"] = ""
        # memory = ActionHistoryMemory(llm=kwargs.get("llm",OpenAI()))
        super().__init__(agentrule=rule, 
                         infos = infos,
                         **kwargs)
    
    class Config:
        arbitrary_types_allowed = True
    
    def update_times(self,chose=False):
        if chose:
            self.available = False
        else:
            self.choose_times+=1
            # if(self.choose_times>=self.max_choose):
            #     self.available = False
    
    @classmethod
    def _get_default_output_parser(cls, **kwargs: Any) -> AgentOutputParser:
        return ConvoOutputParser()
    
    @classmethod
    def create_prompt(
        cls, 
        prompt
        ):
        # not used
        # only for abstract method initilization
        return prompt
    
    @property 
    def llm_prefix(self) -> str:
        """Prefix to append the LLM call with."""
        return "Thought:"
    
    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        return "Observation: "
    
    # 这个返回值，限制output_parser的返回内容
    @property
    def return_values(self) -> List[str]:
        """Return values of the agent."""
        return ["return_values"]
    
    @property
    def input_keys(self) -> List[str]:
        """Return the input keys.

        :meta private:
        """
        
        return list(set(self.llm_chain.input_keys)-{"agent_scratchpad"})
    
    
    # @root_validator()
    # def validate_prompt(cls, values) :
    #     """Validate that prompt matches format."""
    #     prompt = values["llm_chain"].prompt
    #     if "agent_scratchpad" not in prompt.input_variables:
    #         prompt.input_variables.append("agent_scratchpad")
    #         if isinstance(prompt, ChoosePromptTemplate):
    #             prompt.template += "\n{agent_scratchpad}"
    #     return values
    
    def get_full_inputs(
        self, intermediate_steps: List[Tuple[AgentAction, str]], **kwargs: Any
    ) -> Dict[str, Any]:
        """Create the full inputs for the LLMChain from intermediate steps."""
        thoughts = self._construct_scratchpad(intermediate_steps)
        new_inputs = {"agent_scratchpad": thoughts, "stop": self._stop}
        full_inputs = {**kwargs, **new_inputs}
        return full_inputs
    
    
    def plan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> Union[AgentAction, AgentFinish]:
        """Given input, decided what to do.

        Args:
            intermediate_steps: Steps the LLM has taken to date,
                along with observations
            callbacks: Callbacks to run.
            **kwargs: User inputs.

        Returns:
            Action specifying what tool to use.
        """
        full_inputs = self.get_full_inputs(intermediate_steps, **kwargs)
        full_output = self.llm_chain.predict(callbacks=callbacks, **full_inputs)

        return self.output_parser.parse(full_output)
    
    
    def chain(self, prompt: PromptTemplate,verbose:bool=False) -> LLMChain:
        return LLMChain(
            llm=self.llm, prompt=prompt, verbose=verbose
        )
        
        
    def reset_memory_llm(self,llm):
        self.memory.reset_llm(llm)
        
    def reset_llm(self,
                  llm):
        self.llm = llm
        self.reset_state(mode ="choose") # default setting ，change llm_chain
    
    def reset_state(self,
                     mode = "access_forum",
                     verbose :bool = False,
                     allowed_tools :Optional[List[str]] = []):
        # STATES=("access_forum",
        #         "publish_forum",
        #         "choose",
        #         "comment",
        #         "group_discuss",
        #         "group_discuss_plan",
        #         "group_discuss_back",
        #         "action_plan",
        #         "relation")
        
        # assert mode in STATES
        if self.mode == mode : return
        

        if mode == "access_forum":
            prompt = ForumPromptTemplate(tools=allowed_tools)
            output_parser = ForumParser(tenant_name=self.name)
        else:
            prompt = chat_prompt_registry.build(mode)
            output_parser = output_parser_registry.build(mode)

        
        self.mode = mode
        self.llm_chain = self.chain(prompt=prompt,verbose=verbose)
        self.output_parser = output_parser
        self.allowed_tools = allowed_tools
            
    # 发消息给别人
    def send_message(self,
                    step_type,
                      sendcontent : dict= {},
                      tool_response = [],
                      receivers : dict = {}, # tenant_id: tenant_name
                      # 下面三个参数，仅在step_type == "social_network"时用到
                      conver_num = 0, # 表示本轮更新前的conver数
                      context :List[str] = [], # 表示本轮更新前的context       
                      continue_dialogue : bool = True ,    # 记录对话是否继续 
                      ):
        
        kargs={ "content":sendcontent,
                "sender":{self.id:self.name},
                "receivers":receivers,
                "message_type":step_type,
                "tool_response": tool_response,
                "conver_num":conver_num,
                "context":context,
                "continue_dialogue":continue_dialogue}
        

        sendmessage = Message(
            **kargs
        ) #给别人发的信息
            
        self.memory.add_post_meesage_buffer(messages=[sendmessage])
            
    # 更新自己的记忆（发消息给自己）
    def update_memory(self,
                      step_type,
                      selfcontent : dict= {},
                      tool_response = [],
                      receivers : dict = {}, # tenant_id: tenant_name
                      # 下面三个参数，仅在step_type == "social_network"时用到
                      conver_num = 0, # 表示本轮更新前的conver数
                      context :List[str] = [], # 表示本轮更新前的context       
                      continue_dialogue : bool = True,     # 记录对话是否继续,
                      ):
        STEP_TYPES=(
            "community",
            "house_type",
            "house",
            "publish",
            "search",
            "social_network",
            "house_orientation"
        )
        assert step_type in STEP_TYPES, "invalid type of step"
        
        kargs={ "content": selfcontent,
                "sender":{self.id:self.name},
                "receivers":receivers,
                "message_type":step_type,
                "tool_response": tool_response,
                "conver_num":conver_num,
                "context":context,
                "continue_dialogue":continue_dialogue}
        
     
        selfmessage = Message(
                **kargs
            ) 
        if step_type == "social_network":
            self.memory.add_social_network_message([selfmessage])
        elif step_type == "search":
            self.memory.add_forum_message([selfmessage])
        else:
            self.memory.add_message(messages=[selfmessage])
        return selfmessage
            
            
        
        
    # 发信息给其他tenant
    def post_messages(self):
        post_messages = self.memory.post_meesages()
        return post_messages
    
    def receive_messages(self,messages:List[Message]=[]):
        for message in messages:
            if (message.message_type == "social_network"):
                self.memory.receive_message(messages=[message])
            else:
                self.memory.add_message(messages=[message],receive=True)
    
    def step(self, 
             prompt_inputs:dict, 
             tools=[],
             ) -> Message:
        """Generate the next message"""


        
        executor = House_AgentExecutor(
            agent = self,
            tools = tools,
            verbose = True,
            return_intermediate_steps=True,
        )

        response = None
        for i in range(self.max_retry):
            try:
                response = executor(prompt_inputs)
                break
            except OutputParseError as e:
                print(e)
                print("Retrying...")
                continue
            except RateLimitError as e:
                e
        if response is None:
            # raise ValueError(f"{self.name} failed to generate valid response.")
            return {"output":f"{self.name} failed to generate valid response.",
                    "thought":""
                    }

        return response
    
    
    # 异步版本的step
    async def astep(self, 
             prompt_inputs:dict, 
             tools=[],
             ) -> Message:
        """Generate the next message"""

        
        executor = House_AgentExecutor(
            agent = self,
            tools = tools,
            verbose = True,
            return_intermediate_steps=True,
        )

        response = None
        for i in range(self.max_retry):
            try:
                response = await executor.acall(prompt_inputs)
                break
            except OutputParseError as e:
                print(e)
                print("Retrying...")
                continue
        if response is None:
            # raise ValueError(f"{self.name} failed to generate valid response.")
            return {"output":f"{self.name} failed to generate valid response.",
                    "thought":""
            }
        return response
            

    # 这里定义初始的agent，
    # 如果需要修改prompt,用self.reset_prompt()
    @classmethod
    def from_llm_and_tools(
        cls,
        id:str,
        name:str,
        infos: dict,
        memory_config: dict,
        llm: BaseLanguageModel,
        prompt: PromptTemplate,
        rule: dict,
        work_place :str,
        output_parser: Optional[AgentOutputParser],
        policy:BasePolicy,
        allowed_tools :Optional[List[str]] = None,
        max_choose:int = 3,
        priority_item:dict={},
        family_num:int=0,
        choose_rating:bool = False,
        llm_config:dict ={},
        log_round_tenant:Log_Round_Tenant = None
    ) -> langchainAgent:
        """Construct an agent from an LLM and tools."""
        llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
        )
        
        memory = load_memory(memory_config = memory_config)
        return cls(
            #llm_chain = llm_chain,
            output_parser = output_parser,
            allowed_tools = allowed_tools,
            llm = llm,
            llm_chain = llm_chain,
            id = id,
            name = name,
            rule = rule,
            infos = infos,
            memory = memory,
            max_choose = max_choose,
            workplace = work_place,
            priority_item = priority_item,
            family_num=family_num,
            policy = policy,
            choose_rating = choose_rating,
            llm_config = llm_config,
            log_round_tenant = log_round_tenant
        )
        
    def reset(self):
        self.memory.reset()
     
    def get_concise_role_description(self):
        
        template="""\
You are {name}. You earn {monthly_income} per month.\
Your family members include: {family_members}."""
        concise_role_description = template.format_map({"name":self.name,
                                    **self.infos}
                                   )
        if self.infos.get("personal_preference",False):
            concise_role_description += "Up to now, your personal preference for house is :{}".format(
                self.infos.get("personal_preference")
            )
        return concise_role_description
        
    def get_role_description(self):
        
        template="""\
You are {name}. You earn {monthly_income} per month.\
Your family members include: {family_members}.\
You are {age} years old. Your job is {profession}. \
Your company is located in {en_work_place}. \
{special_request} \
You expect to rent a house for {monthly_rent_budget}.\
You still have {chance_num} chances to choose house.\
"""
        role_description = template.format_map({"name":self.name,
                                    "chance_num":self.max_choose-self.choose_times,
                                    **self.infos}
                                   )
        if self.infos.get("personal_preference",False):
            role_description += "Up to now, your personal preference for house is :{}".format(
                self.infos.get("personal_preference")
            )
        return role_description
    
    async def action_plan(self,
                    actions:dict,
                    forum_manager,
                    system,
                    rule,
                    tool=None,
                   ):
        # actions:{action_name:action_use}
        
        template_action="{id_}. {action_name}:{action_use}"
        
        action_usages="\n".join([template_action.format_map({
            "id_":id_,
            "action_name":action_item[0],
            "action_use":action_item[1]
        })
        for id_,action_item in enumerate(actions.items())])

        action_names=",".join(list(actions.keys()))
        action_log=""
        
            
        observation=""
        #action="GroupDiscuss"
        prompt_inputs={
            'actions':action_usages,
            'action_names':action_names,
            'memory':"",
            'role_description':self.get_role_description(),
            'history':action_log
            }

        self.reset_state(mode="action_plan")
        
        # response = await self.astep(prompt_inputs)
        response = await self.astep(prompt_inputs)
        response = response.get("return_values",{})

        
        action = response.get("output","")
        thought = response.get("thought","")
        if action == "Search":
            return await self.search_forum(forum_manager,
                                system)
            # observation="I have searched some info on forum."
        elif action == "Publish":
            return await self.publish_forum(forum_manager,
                                system)
            # observation="I have published some info on forum."
        elif action == "GroupDiscuss":
            return await self.communicate(system=system)
            # observation="I have discussed with my acquaintances."
        elif action == "Choose":
            
            choose_state,choose_house_id = await self.policy.choose_pipeline(
                    tenant= self,
                    forum_manager=forum_manager,
                    system=system,
                    rule=rule,
                    tool=tool,
                    log_round=self.log_round_tenant
                    )
            
            forum_manager.save_data()
            return choose_state
        
        
            
        # action_log +=\
        #     "Thought:{thought}\nAction:{action}\nObservation:{observation}".format_map({
        #         "thought":thought,
        #         "action":action,
        #         "observation":observation
        #     })
            
    # 异步的communication过程，包括四种动作（一种放弃）
    async def async_communication(self,
                                  forum_manager,
                                  system,
                                  rule,
                                  round_index,
                                  ):
        
        # debug
        return await self.communicate(
                                system = system,
                                round_index = round_index,)
        
        # if self.memory.messages.get("search")==None:
        #     actions = {
        #         # "Search":"search house info from forum",
        #         # "Publish":"publish house info on forum",
        #         "GroupDiscuss":"discuss with other people about house renting",
        #         "Giveup":"do nothing"
        #         }
        #     self.action_plan(actions=actions,
        #                         forum_manager=forum_manager,
        #                         system=system,
        #                         rule=rule,)
        # else:
        #     actions = {
        #         #"Publish":"publish house info on forum",
        #         "GroupDiscuss":"discuss with other people about house renting",
        #         "Giveup":"do nothing"
        #         }
        #     self.action_plan(actions=actions,
        #                         forum_manager=forum_manager,
        #                         system=system,
        #                         rule=rule,
        #                         )
    
    async def group(self,
                forum_manager, 
                system,  
                rule,
                tool):
        return await self.policy.group(self,
                          forum_manager, 
                            system,  
                            rule,
                            tool,
                            self.log_round_tenant)
    
    async def choose_process(self, 
               forum_manager, 
               system, 
               rule,
               tool):
        
        actions = {
            "Choose":"Conduct the house choosing process",
            "Giveup":"do nothing"
            }
        return await self.action_plan(actions=actions,
                         forum_manager=forum_manager,
                         system=system,
                         rule=rule,
                         tool=tool) 
        # 进行1轮，先是否进行选房流程的判断，若否则直接返回
        
  
    async def communicate(self,system,round_index = 0):
        if len(self.memory.mail)>0:
            
            return await self.group_discuss_back(
                                           system=system,
                                           round_index=round_index)   
        else:
            
            return await self.group_discuss(
                                      system=system,
                                      round_index=round_index)
        
    # 一系列房子选择的函数，理想中要整合成pipeline之类的格式(待改)
    
    async def group_discuss_plan(self,
                           respond_format,
                           system,
                           memory="",
                           step_type ="group_discuss_plan",
                           round_index=10):
        self.reset_state(mode="group_discuss_plan")
        
        acquaintance_template = "Your acquaintances include {acquaintance_type}."
        ac_types=[]
        for ac_info in self.memory.social_network.values():
            ac_type = ac_info.get("relation").lower()
            if ac_type not in ac_types:
                ac_types.append(ac_type)
        ac_description = acquaintance_template.format(acquaintance_type=",".join(ac_types))
        

        personality = self.infos.get("personality")
        
        system_competiveness_description = system.get_system_competiveness_description(self.queue_name)
        
        goal = system.get_goal()
        
        concise_role_description = self.get_concise_role_description()
        
        
        prompt_inputs={
                "concise_role_description":concise_role_description,
                "acquaintance_desciption":ac_description,
                "memory":memory,
                "personality":personality,
                "system_competiveness_description":system_competiveness_description,
                "goal":goal,
                "respond_format":respond_format
                }
        
        print("The group discuss plan of:{name}".format(name=self.name)) #debug
        
        response = await self.astep(prompt_inputs)
        response = response.get("return_values")
        
        
        return response
    
    # 这里加一个recent chat
    async def group_discuss(self,
                      system,
                      round_index = 10):
        
        memory = await self.memory.memory_tenant("social_network",name=self.name) + self.infos.get("extra_info")
        
        respond_format = """Your ideal type of house: (Your personal preference for these houses)
You think (Your true opionion about these communities or houses).
For now, Whether you want to provide information honestly to acquaintances: (Yes or No)

Your current plan to respond is (Your plan to communicate with your friends, competitors, be concise)"""
        group_discuss_plan = await self.group_discuss_plan(respond_format=respond_format,
                                                     system=system,
                                                     memory = memory,
                                                     step_type = "group_discuss_plan",
                                                     round_index = round_index
                                                     )
        
        group_discuss_plan = group_discuss_plan.get("plan")
        
        recent_chats = self.memory.retrieve_recent_chat()
        if recent_chats.strip() == "":
            recent_chats = "None"
        
        # parse_preference:
        try:
            preference = group_discuss_plan.split("\n")[0]
            preference = preference.split(":")[-1].strip()
            self.infos["personal_preference"] = preference
        except:
            print("fail to parse personal preference")
        
        self.reset_state(mode="group_discuss")
        social_network = ["{name}: {relation}".format(
                    name = neigh_tenant_info.get("name",neigh_tenant_id),
                    relation =neigh_tenant_info.get("relation","friend")
                    )
                     for neigh_tenant_id,neigh_tenant_info
                     in self.memory.social_network.items()] 
        social_network_str = "\n".join(social_network)
                
        prompt_inputs={
                "concise_role_description":self.get_concise_role_description(),
                "plan":group_discuss_plan,
                "recent_chats":recent_chats,
                "acquaintances":social_network_str,
                "acquaintance_num":len(self.memory.social_network),
                "memory":memory,
                }
        
        print("SENDER:{name}".format(name=self.name)) #debug
        
        for _ in range(self.max_jug_time):

            response = await self.astep(prompt_inputs)
            response = response.get("return_values")
            
            
            if response.get("output") =="fail to discuss":
                jug_response = False
                continue
            else:
                jug_response = True
                receivers = {}
                for response_round in response["communication"]:
                    receiver_list = response_round.get("acquaintance_names")
                    receiver_list = receiver_list.split(",")

                    for receiver in receiver_list:
                        for friend_id,friend_info in self.memory.social_network.items():
                            if (receiver.strip().lower() in friend_info["name"].lower()):

                                receivers[friend_id] = friend_info["name"]
                                
                    if len(receivers) == len(receiver_list): # 所有receiver均合法
                        
                        send_str="{name} said: {content}".format(name=self.name,content=response_round["output"])
                        response_round["plan"] = group_discuss_plan
                        self.update_memory( 
                                        step_type="social_network",        
                                        selfcontent=response_round,
                                        receivers=receivers,    
                                        conver_num = 0,
                                        context = [send_str],
                                        continue_dialogue = True,
                                        )

                        
                        # 这里需要重新声明类，因为content不能重新改
                        self.send_message(step_type = "social_network", 
                                          sendcontent = {"output":response_round["output"]},# 不发送 thought，name
                                          receivers = receivers,
                                        conver_num = 0,
                                        context = [send_str],
                                        continue_dialogue = True,
                                        )
                        
                       
                        # 注： 在对话未结束之前，在buffer 和 自己记忆库（这里存在重复存储的问题） 中保留对话记录
                        
                    else:
                        jug_response = False
                        
                if jug_response: # 如果此round response 含有非法内容，rerun; 否则break
                    break
                
        return jug_response == True # 存在合法回答，则继续dialogue
                    
    # 在调用discuss_back之后，重新更新社交关系
    # context是最新，含有对话细节的message的context
    async def update_acquaintance_relation(self,
                                     context,
                                     acquaintance_id:str,
                                     round_index:int = 10):
        
        self.reset_state(mode="relation")
        
        role_description = """You are {name}. You want to rent a house, \
you're communicating with your acquaintances about house renting.""".format(name = self.name)

        comment = self.memory.social_network[acquaintance_id].get("comment","")
        if comment != "":
            comment = "and your comment on him is: {}".format(comment)
            
        relation = """So far, you think {ac_name} is a {relation} of yours.{comment}""".format(ac_name = self.memory.social_network[acquaintance_id].get("name"),
                                                                                    relation = self.memory.social_network[acquaintance_id].get("relation"),
                                                                                    comment=comment)
        communication = "\n".join(context)
        
        prompt_inputs = {
            "acquaintance_name":self.memory.social_network[acquaintance_id].get("name"), 
            "role_description":role_description,
            "memory":await self.memory.memory_tenant("relation"),
            "relation":relation,
            "communication":communication,
        }
        response = await self.astep(prompt_inputs = prompt_inputs)
        response = response.get("return_values")
        
        
        
        try:
            self.memory.social_network[acquaintance_id]["relation"] = response.get("relation")
            self.memory.social_network[acquaintance_id]["comment"] = response.get("comment")
        except Exception as e:
            print("Fail to update relation for {}".format(self.name))
              
                
    async def group_discuss_back(self, 
                           system,
                           round_index = 10):
        concise_role_description = self.get_concise_role_description()
        if self.infos.get("personal_preference",False):
            concise_role_description += "Up to now, your personal preference for house is :{}".format(
                self.infos.get("personal_preference")
            )
            
        self_continue_dialogue = False
        for message in self.memory.mail:
            memory = await self.memory.memory_tenant("social_network_message_back",name=self.name) + self.infos.get("extra_info")
            assert isinstance(message,Message)
            acquantice_name = list(message.sender.values())[0]
            acquantice_id = list(message.sender.keys())[0]
            
            if acquantice_id not in self.memory.social_network:
                self.memory.social_network[acquantice_id]= {"name":acquantice_name,
                                                     "relation":"stranger"} # 如果有陌生人给你发消息，加入到自己的社交关系中，设定陌生人。
                                
            acquantice_type = self.memory.social_network[acquantice_id].get("relation")
            acquantice_comment = self.memory.social_network[acquantice_id].get("comment","")
            
            respond_format = """
Your ideal type of house: (Your personal preference for these houses)
You think (Your true opionion about these communities or houses).
For now, Whether you want to provide information honestly to {acquantice_name}: (Yes or No)
Your relationship with {acquantice_name} is {acquantice_type}. {comment}\
You think {acquantice_name} is (your belif in the information provided by this person)

Your current plan to respond is (Your plan to communicate with your {acquantice_name}, be concise)"""
            respond_format = respond_format.format(acquantice_name=acquantice_name,
                                                   comment = acquantice_comment,
                                                   acquantice_type=acquantice_type)
            
            group_discuss_plan = await self.group_discuss_plan(respond_format = respond_format,
                                                         memory = memory,
                                                         system = system,
                                                         step_type = "group_discuss_back_plan",
                                                         round_index = round_index)
            group_discuss_plan = group_discuss_plan.get("plan")
            
            # parse_preference:
            try:
                preference = group_discuss_plan.split("\n")[0]
                preference = preference.split(":")[-1].strip()
                self.infos["personal_preference"] = preference
            except:
                print("fail to parse personal preference")
            
            self.reset_state(mode="group_discuss_back")
            
            if message.conver_num <=8 : # 大于8轮的情况会结束 
                context_str="\n".join(message.context)
                prompt_inputs={
                        "concise_role_description":concise_role_description,
                        "memory": memory,
                        "plan":group_discuss_plan,
                        "acquaintance_communication":context_str,
                        "acquaintance_name":acquantice_name
                        }
                
                print("SENDER:{name}".format(name=self.name)) #debug
                
                
                response = await self.astep(prompt_inputs = prompt_inputs)
                response = response.get("return_values")
                
                
                
                if response is None:
                    return
                else:
                    context = copy.deepcopy(message.context) # 这里需不需要deepcopy？
                    sender_id = copy.deepcopy(list(message.sender.keys())[0])
                    continue_dialogue = response.pop("continue_dialogue",True)
                    
                    send_str="{name} said: {content}".format(name=self.name,
                                                    content=response["output"])
                    context.append(send_str)
                    
                    if continue_dialogue: #希望结束对话，则不发送信息,不做这一步
                        self_continue_dialogue = True
                        kargs={ "message_type":"social_network",
                                "sender":{self.id:self.name},
                                "content":response,
                                "receivers": message.sender,
                                "conver_num": message.conver_num+1,
                                "context":context,
                                "continue_dialogue":continue_dialogue}
                        
                        message_send = Message(**kargs)
                        self.memory.add_post_meesage_buffer([message_send])
                        
                        
                        message_self = copy.deepcopy(message_send) # 必须新创建，否则传到listener那里会影响这里的内容。
                        message_self.content.update({"plan":group_discuss_plan})
                        self.memory.add_social_network_message([message_self]) 
                   

                        
                    await self.update_acquaintance_relation(context = context,
                                                      acquaintance_id = sender_id,
                                                      round_index = round_index)
                    
        self.memory.mail.clear()
        return self_continue_dialogue

    
    def comment(self,description,step_type): # description 可以是community或house_type或house
        self.reset_state(mode="comment")
        if step_type == "community":
            thought_type = "Your thought on the communities"
            comment_type = "community_index: the comments of the communities"
        elif step_type == "house_type":
            thought_type = "Your thought on the house types"
            comment_type = "house_type: the comments of the house types"
        elif step_type == "house":
            thought_type = "Your thought on the houses"
            comment_type = "house_index: the comments of the houses"
        
        prompt_inputs={
                'house_info':description,
                'memory':"",
                'thought_type':thought_type,
                'comment_type':comment_type,
                'role_description':self.get_role_description(),
                'message_type':step_type
                }
        
        response = self.step(prompt_inputs).get("return_values")
        
        
        for comment in response:
            if comment.get("output") =="I fail to make comments.":
                return
            else:
                receivers={}
                for tenant_id,tenant_info in self.memory.social_network:
                    receivers[tenant_id] = tenant_info.get("name","")
                
                self.update_memory(selfcontent = comment,
                                step_type=step_type,
                                receivers={self.id:self.name})
        
    
    # 返回：（是否选择，选择编号）
    async def choose_community(self,system,search_infos,rule) ->Tuple[bool,str]:
        mem_buffer=[]
        tip=[]
        
        choose_house_type = self.log_round_tenant.log_round.get("choose_house_type", None)
        
        community_description, community_ids = system.get_community_abstract(self.queue_name,rule, self, choose_house_type)
        self.log_round_tenant.set_available_community_description(community_description)
        self.reset_state(mode="choose")
        

        choose_type = """My choice is (The index of community, should be one of [{community_ids}])"""
        choose_type = choose_type.format(community_ids=",".join(community_ids))
        memory = await self.memory.memory_tenant("community",name=self.name) + self.infos.get("extra_info")
        prompt_inputs={
                'task':'You need to choose one type of communities.',
                'thought_type':'Your views on these communities.',
                'choose_type':choose_type,
                'house_info':community_description,
                'memory': memory,
                'role_description':self.get_role_description()        
                }
        for _ in range(self.max_jug_time):
            prompt_inputs["memory"] = memory + "\n" + "".join(tip)
            
            
            response = await self.astep(prompt_inputs)
            response = response.get("return_values")
            self.log_round_tenant.set_choose_history(prompt_inputs = prompt_inputs,
                                         response = response,
                                         step_type = "choose_community")

            choose_status = False
            try:
                content = response.get("output","")
                choose_idx = re.search("(community_\w+)",str(content),re.I | re.M)
                choose_idx = choose_idx.groups()[0]
                choose_status = True
            
            except Exception as e:
                try:
                    content = response.get("output","")
                    choose_idx = re.search("([0-9]+)",str(content),re.I | re.M)
                    choose_idx = choose_idx.groups()[0]
                    choose_idx = 'community_{}'.format(choose_idx)
                    choose_status = True
                    
                except:
                    choose_status = False
            
            if (choose_status):
                if (system.jug_community_valid(choose_idx,community_ids,self.queue_name)):
                    self.update_memory(step_type="community",
                                        selfcontent=response,
                                       receivers={self.id:self.name},
                                       )
                    return True, choose_idx.lower(), response.get("thought","")
                else:
                    tip.append(f"{choose_idx.lower()} is not available now.")

                    mem_buffer.append(response)
            else:
                self.update_memory(selfcontent=response,
                                   receivers={self.id:self.name},
                                    step_type="community")
                return False,"None", response.get("thought","")
        
        thought_fail_choose="" # 每一次的选择都是非法结果
        for mem in mem_buffer:
            thought_fail_choose+=mem.get("thought","")
            
        self.update_memory(selfcontent={"thought":thought_fail_choose,
                            "output":"I fail to choose valid community."},
                           receivers={self.id:self.name},
                           step_type="community")
        
        return False,"None", thought_fail_choose
                
        
        

        
    async def choose_house_type(self,system,rule,community_id = None) -> Tuple[bool,str]:
        mem_buffer=[]
        tip=[]
        
        house_type_description, house_type_ids = system.get_house_type(self.queue_name,community_id,rule,self)
        self.log_round_tenant.set_available_house_type(house_type_ids)
        
        choose_type = """My choice is (house type, should be one of [{house_type_indexs}])"""
        choose_type = choose_type.format(house_type_indexs = ",".join(house_type_ids))

        memory = await self.memory.memory_tenant("house_type",name=self.name)
        prompt_inputs={
            'task':'You need to choose one type of houses.',
            'thought_type':'Your views on these house types.',
            'choose_type':choose_type,
            'house_info':house_type_description,
            'memory':memory,
            'role_description':self.get_role_description()        
            }        
        
        for _ in range(self.max_jug_time):
            prompt_inputs["memory"] = memory + "\n" + "".join(tip)            
        
            
            self.reset_state(mode="choose")
            response = await self.astep(prompt_inputs)
            response = response.get("return_values")
            self.log_round_tenant.set_choose_history(prompt_inputs = prompt_inputs,
                                response = response,
                                step_type = "choose_house_type")

            # parse community choosing reponse
            choose_status = False
            choose_idx = None
            try:
                content = response.get("output","").lower()
                choose_idx= re.search("(\w+_\w+)",str(content),re.I | re.M)
                choose_idx = choose_idx.groups()[0].lower()
                choose_status = True
            
            except Exception as e:
                try:
                    content = response.get("output","")
                    if "mid"  in content:
                        choose_idx = "middle_house"
                        choose_status = True 
                    elif "large" in content:
                        choose_idx = "large_house"
                        choose_status = True
                    elif "small" in content:
                        choose_idx = "small_house"
                        choose_status = True
                    else:
                        choose_status = False
                except Exception as e:
                    choose_status = False
            
            if (choose_status):
                if community_id is None or \
                    (system.jug_community_housetype_valid(community_id,choose_idx,house_type_ids,self.queue_name)):   
                        # 如果在选小区之前选房型（community_id is None），就视作可行解
                        
                    self.update_memory(selfcontent=response,
                                       receivers={self.id:self.name},
                                       step_type="house_type")
                    return True, choose_idx.lower(), response.get("thought","")
                else:
                    tip.append(f"{choose_idx.lower()} is not available any more, keep this in mind.")
                    mem_buffer.append(response)
            else:
                self.update_memory(selfcontent=response,
                                   receivers={self.id:self.name},
                                    step_type="house_type")
                return False,"None", response.get("thought","")
        
        thought_fail_choose="" # 每一次的选择都是非法结果
        for mem in mem_buffer:
            thought_fail_choose+=mem.get("thought","")
            
        self.update_memory(selfcontent={"thought":thought_fail_choose,
                            "output":"I fail to choose valid house type."},
                           receivers={self.id:self.name},
                           step_type="house_type")
        
        return False,"None", thought_fail_choose
            
    async def choose_house_page(self, 
                          log_round_houses:List[set],
                          house_infos, 
                          house_ids:list, 
                          page_size:int = 20,
                          round_retry:int = 0,
                          tip:list=[]):
        
        houses_description_generator = self.agentrule.get_houses_generator(
                             house_data = house_infos,
                             house_ids = house_ids,
                             page_size = page_size, 
                             round_retry = round_retry
                             )
        
        choose_page_results = []
        nochoose_memory_cache = []
        choose_memory_cache = []
        
        role_description = self.get_role_description()
        
        choose_type_template = """My choice is (The index of houses, should be one of [{house_indexes}])"""
        
        
        memory = await self.memory.memory_tenant("house",name=self.name)
        for houses_description,house_available_index in houses_description_generator:
            # self.logger.info("SYSTEM:\n {}".format(houses_description))
            choose_type = choose_type_template.format(house_indexes = ",".join(house_available_index))
            prompt_inputs={
                'task':'You need to choose one house.',
                'thought_type':'Your views on these houses.',
                'choose_type':choose_type,
                'house_info':houses_description,
                'memory':memory +"\n" + "".join(tip),
                'role_description': role_description       
                }
            # self.comment(description=houses_description,
            #              step_type="house")
            
            self.reset_state(mode="choose")
            response = await self.astep(prompt_inputs)
            response = response.get("return_values") # 这里不更新记忆，仅更新最后一步
            # self.logger.debug("choose houses, tenant reponse:{}".format(response.get("output","")))
            # parse community choosing reponse
            
            log_round_houses.append((prompt_inputs,response))
            
            try:
                content = response.get("output","")
                choose_idx = re.search("(house_\w+)",str(content),re.I | re.M)
                choose_idx = choose_idx.groups()[0]
                choose_page_results.append(choose_idx.lower())
                choose_memory_cache.append(response) 
            
            except Exception as e:
                try:
                    content = response.get("output","")
                    choose_idx = re.search("([0-9]+)",str(content),re.I | re.M)
                    choose_idx = choose_idx.groups()[0]
                    choose_idx = 'house_{}'.format(choose_idx)
                    choose_page_results.append(choose_idx.lower())
                    choose_memory_cache.append(response) 
                except:
                    nochoose_memory_cache.append(response)
                    
        
        if len(choose_page_results) > 1 :
            # 这里选择和不选择的记忆没有更新，忽略掉。
            return self.choose_house_page(log_round_houses,
                                          house_infos,
                                          choose_page_results,
                                          page_size=page_size,
                                         )
        
        elif len(choose_page_results) == 1:
            choose_house=choose_page_results[0]
            return True, choose_house, choose_memory_cache

        return False,"None", nochoose_memory_cache

        
    async def choose_house(self,
                     system,
                     community_id,
                     house_filter_ids:list)->Tuple[bool,str]:
        
        # 这里的log_round 中存储一开始的所有info（未分页）
        house_ids = system.get_filtered_houses_ids(community_id=community_id,
                                                   queue_name=self.queue_name,
                                                   house_filter_ids=house_filter_ids)

        house_infos = system.house_ids_to_infos(house_ids)            
        self.log_round_tenant.set_available_house_description(house_infos)
        mem_buffer = []
        tip = []
        log_round_houses = []
        for round_retry in range(self.max_jug_time):
            if self.choose_rating:
                choose_status,choose_id,choose_mem = \
                await self.choose_house_page_rating(log_round_houses=log_round_houses,
                                   house_infos=house_infos,
                                   house_ids=house_ids,
                                   page_size=20,
                                   round_retry=round_retry,
                                   tip=tip)
            else:
                
                choose_status,choose_id,choose_mem = \
                await self.choose_house_page(log_round_houses=log_round_houses,
                                   house_infos=house_infos,
                                   house_ids=house_ids,
                                   page_size=20,
                                   round_retry=round_retry,
                                   tip=tip)
            log_round_houses_dict = {idx:{
                                       "prompt_inputs":log_round_house[0],
                                       "response":log_round_house[1]
                                       } 
                                     for idx,log_round_house in enumerate(log_round_houses)}
            if (self.choose_rating):
                rating_rounds = {idx:log_round_house[1].get("rating") for idx, log_round_house in enumerate(log_round_houses) }
                
                self.log_round_tenant.set_choose_house_rating_score(rating_rounds)
                
            self.log_round_tenant.set_choose_history(step_type = "choose_house",
                                         log_round_houses_dict = log_round_houses_dict)
            
            if (choose_status):
                if (system.jug_house_valid(choose_id)):
                    assert len(choose_mem)==1
                    # 选择了房子的情况，只更新关于选择的房子的记忆
                    self.update_memory(selfcontent=choose_mem[0],
                                       receivers={self.id:self.name},
                                    step_type="house",
                                    ) 
                    
                    # 在选择完一个房子后，记忆中添加房子相关暗信息   
                    dark_info = system.get_house_dark_info(choose_id)
                    self.update_memory(selfcontent={"output":dark_info},
                                       receivers={self.id:self.name},
                                    step_type="house")
                    
                    return True, choose_id, choose_mem[0].get("thought")
                else:
                    tip.append(f"House_{choose_id} has been chosen, keep this in mind.")
                    mem_buffer.append(choose_mem[0])
            else:
                no_choose_thought=""
                for nochoose_memory in choose_mem:
                    self.update_memory(selfcontent=nochoose_memory,
                                       receivers={self.id:self.name},
                                        step_type="house",
                                        )
                    no_choose_thought += nochoose_memory.get("thought","")   
                return False, choose_id, no_choose_thought     
        
        thought_fail_choose="" # 每一次的选择都是非法结果
        for mem in mem_buffer:
            thought_fail_choose+=mem.get("thought","")
            
        self.update_memory(selfcontent={"thought":thought_fail_choose,
                            "output":"I fail to choose valid house."},
                           receivers={self.id:self.name},
                           step_type="house")
        
        return False,"None", thought_fail_choose
        
    
    async def choose_house_page_rating(self,
                          log_round_houses:List[set],
                          house_infos, 
                          house_ids:list, 
                          page_size:int = 20,
                          round_retry:int = 0,
                          tip:list=[]):
        
        houses_description_generator = self.agentrule.get_houses_generator(
                             house_data = house_infos,
                             house_ids = house_ids,
                             page_size = page_size, 
                             round_retry = round_retry
                             )
        
        choose_page_results = []
        nochoose_memory_cache = []
        choose_memory_cache = []
        
        role_description = self.get_role_description()
       
        memory = await self.memory.memory_tenant("house",name=self.name)
        for houses_description,house_available_index in houses_description_generator:
            # self.logger.info("SYSTEM:\n {}".format(houses_description))

            prompt_inputs={
                'house_info':houses_description,
                'memory':memory +"\n" + "".join(tip),
                'role_description': role_description,
                'available_house_index' :",".join(house_available_index),
                }
            # self.comment(description=houses_description,
            #              step_type="house")
            
            self.reset_state(mode="choose_rating")
            response = await self.astep(prompt_inputs)
            response = response.get("return_values") # 这里不更新记忆，仅更新最后一步
            # self.logger.debug("choose houses, tenant reponse:{}".format(response.get("output","")))
            # parse community choosing reponse
            
            log_round_houses.append((prompt_inputs,response))
            
            try:
                rating = response.get('rating',[])
                rating.sort(key = lambda num:num[1])
                
                choose_page_results.append(rating[-1][0].lower())
                assert rating[-1][0].lower() in house_available_index
                response["choose_house"] = rating[-1][0].lower()
                choose_memory_cache.append(response) 
            
            except Exception as e:
                nochoose_memory_cache.append(response)
                    
        
        if len(choose_page_results) > 1 :
            # 这里选择和不选择的记忆没有更新，忽略掉。
            return self.choose_house_page_rating(log_round_houses,
                                          house_infos,
                                          choose_page_results,
                                          page_size=page_size,
                                         )
        
        elif len(choose_page_results) == 1:
            choose_house=choose_page_results[0]
            return True, choose_house, choose_memory_cache

        return False,"None", nochoose_memory_cache
        
    
    
    
    async def choose_orientation(self,system,rule,community_id = None) -> Tuple[bool,str]:
        mem_buffer=[]
        tip=[]
        
        available_orientation_description, available_orientations = system.get_house_orientation(queue_name=self.queue_name,
                                                                                                 community_id=community_id,
                                                                                               rule=rule,
                                                                                               tenant=self)
        if len(available_orientations) == 1:
            return True, available_orientations[0], "There's only one type of house orientation."
        choose_type = """My choice is (house orientation, should be one of [{house_type_indexs}])"""
        choose_type = choose_type.format(house_type_indexs = ",".join(available_orientations))

        memory = await self.memory.memory_tenant("house_orientation",name=self.name)
        prompt_inputs={
            'task':'You need to choose one type of house orientation.',
            'thought_type':'Your views on these house orientations.',
            'choose_type':choose_type,
            'house_info':available_orientation_description,
            'memory':memory,
            'role_description':self.get_role_description()        
            }        
        
        for _ in range(self.max_jug_time):
            prompt_inputs["memory"] = memory + "\n" + "".join(tip)            
        
            self.log_round_tenant.set_available_house_type(system.get_available_house_type(community_id,self.queue_name))
            self.reset_state(mode="choose")
            response = await self.astep(prompt_inputs)
            response = response.get("return_values")
            
            self.log_round_tenant.set_choose_history(prompt_inputs = prompt_inputs,
                                response = response,
                                step_type = "choose_house_orientation")
            # parse community choosing reponse
            choose_status = False
            chosen_orientation = None
            try:
                content = response.get("output","")
                content = re.search(".*?choice.*?is (.*)",str(content),re.I | re.M)
                content = content.groups()[0].upper()
                
                for orientation in {"north",'west','east','south'}:
                    if orientation in content.lower():
                        choose_status = True
                        chosen_orientation = orientation[0].upper()
                        break
                    
                if not choose_status:
                    for orientation in {"N",'W','E','S'}:
                        if orientation in content.upper():
                            choose_status = True
                            chosen_orientation = orientation
                            break
                        
            except Exception as e:
                choose_status = False
            
            if (choose_status):
                if chosen_orientation  in available_orientations:
                    # 如果在选小区之前选房型（community_id is None），就视作可行解    
                    self.update_memory(selfcontent=response,
                                       receivers={self.id:self.name},
                                       step_type="house_orientation")
                    return True, chosen_orientation, response.get("thought","")
                else:
                    tip.append(f"{chosen_orientation} is not available any more, keep this in mind.")
                    mem_buffer.append(response)
            else:
                self.update_memory(selfcontent=response,
                                   receivers={self.id:self.name},
                                    step_type="house_orientation")
                return False,"None", response.get("thought","")
        
        thought_fail_choose="" # 每一次的选择都是非法结果
        for mem in mem_buffer:
            thought_fail_choose+=mem.get("thought","")
            
        self.update_memory(selfcontent={"thought":thought_fail_choose},
                           receivers={self.id:self.name},
                           step_type="house_type")
        
        return False,"None", thought_fail_choose
    
    
    async def choose_floor(self,system,rule,community_id = None) -> Tuple[bool,str]:
        mem_buffer=[]
        tip=[]
        
        available_floor_description, available_floors = system.get_house_floor(community_id=community_id,
                                                                                               rule=rule,
                                                                                               tenant=self)
        
        if (len(available_floors)==1):
            return True, available_floors[0], "There's only one type of floor type."
        
        choose_type = """My choice is (house floor, should be one of [{floor_types}])"""
        choose_type = choose_type.format(floor_types = ",".join(available_floors))

        memory = await self.memory.memory_tenant("floor_type",name=self.name)
        prompt_inputs={
            'task':'You need to choose one type of house orientation.',
            'thought_type':'Your views on these house orientations.',
            'choose_type':choose_type,
            'house_info':available_floor_description,
            'memory':memory,
            'role_description':self.get_role_description()        
            }        
        
        for _ in range(self.max_jug_time):
            prompt_inputs["memory"] = memory + "\n" + "".join(tip)            
        
            self.log_round_tenant.set_available_house_type(system.get_available_house_type(community_id,self.queue_name))
            self.reset_state(mode="choose")
            response = await self.astep(prompt_inputs)
            response = response.get("return_values")
            self.log_round_tenant.set_choose_history(prompt_inputs = prompt_inputs,
                    response = response,
                    step_type = "choose_floor")
            # parse community choosing reponse
            choose_status = False
            try:
                content = response.get("output","")
                content = re.search(".*?choice.*?is (.*)",str(content),re.I | re.M)
                content = content.groups()[0].strip()
                
                for floor in {"high",'low'}:
                    if floor in content.lower():
                        choose_status = True
                        chosen_floor = floor
                        break
                    
                        
            except Exception as e:
                choose_status = False
            
            if (choose_status):
                if chosen_floor  in available_floors:
                    # 如果在选小区之前选房型（community_id is None），就视作可行解    
                    self.update_memory(selfcontent=response,
                                       receivers={self.id:self.name},
                                       step_type="house_orientation")
                    return True, chosen_floor, response.get("thought","")
                else:
                    tip.append(f"{chosen_floor} is not available any more, keep this in mind.")
                    mem_buffer.append(response)
            else:
                self.update_memory(selfcontent=response,
                                   receivers={self.id:self.name},
                                    step_type="house_orientation")
                return False,"None", response.get("thought","")
        
        thought_fail_choose="" # 每一次的选择都是非法结果
        for mem in mem_buffer:
            thought_fail_choose+=mem.get("thought","")
            
        self.update_memory(selfcontent={"thought":thought_fail_choose},
                           receivers={self.id:self.name},
                           step_type="house_type")
        
        return False,"None", thought_fail_choose
    
    
    def search_forum(self,
                     forum_manager,
                     system,
                     search_list:List=None
                    ):
        
        # 暂时从小区列表里随机选两个小区
        k_c = 2
        forum_data = forum_manager.data
        len_forum = len(forum_data)
        k_c = len_forum if k_c>len_forum else k_c
        community_infos = system.get_community_data()
        
        if search_list is None:
            search_list = system.get_available_community_ids(self.queue_name)
        if k_c < len(search_list):
            search_list = random.sample(search_list,k_c)
            
        return_infos={}
        for community_id in search_list:
            community_name = community_infos[community_id].get("community_name","")
            if community_name in forum_data.keys() :
                info = self.agentrule.read_forum(forum_data,community_name)
                return_infos[community_name] = {
                    "search_info":info,
                    "get_shortest_commute_time_str":\
                        map.baidumap.get_shortest_commute_time(self.workplace,community_infos[community_id].get("location"))
                }
                
   
        return_infos_str = self.log_round_tenant.set_forum_conclusion(return_infos)
        
        for c_name,searched in return_infos.items():
            for k,v in searched.items():
                if k == "search_info":
                    self.update_memory(selfcontent={"output":v},
                            step_type="search",
                            receivers={self.id:self.name})
                else:
                    self.update_memory(selfcontent={"output":v},
                            step_type="community",
                            receivers={self.id:self.name})
        
        # for return_info in return_infos_str:
        #     self.update_memory(
        #                     selfcontent={"output":return_info},
        #                     step_type="search",
        #                     receivers={self.id:self.name})          
        

        return return_infos
    
    
    async def publish_forum_plan(self,respond_format,system,memory=""):
        self.reset_state(mode="publish_forum_plan")
        
        role_description ="""Your task is to Publish house information or community information online.\
{concise_role_description}\
You're planning to choose one house.\
And you're willing to publish house information online. Keep this in mind!"""
        role_description = role_description.format(concise_role_description = self.get_concise_role_description())
        

        personality = self.infos.get("personality")
        
        # test: 需要llm_chain summary
        system_competiveness_description = system.get_system_competiveness_description(self.queue_name)
        
        # fixed , 需要改
        goal = system.get_goal()
        
        prompt_inputs={
                "concise_role_description":role_description,
                "memory":memory+self.infos.get("extra_info"),
                "personality":personality,
                "system_competiveness_description":system_competiveness_description,
                "goal":goal,
                "respond_format":respond_format
                }
        
        print("The forum publish plan of:{name}".format(name=self.name)) #debug
        
        response = await self.astep(prompt_inputs)
        response = response.get("return_values")
        
        self.log_round_tenant.set_choose_history(prompt_inputs = prompt_inputs,
                    response = response,
                    step_type = "publish_forum_plan")
        return response 
    
    
    # publish info only, using ReAct
    async def publish_forum(self,
                      forum_manager,
                      system):
        publish_memory = await self.memory.memory_tenant("publish",name=self.name)+self.infos.get("extra_info")
        publish_plan_respond_format = """You think (Your true opionion about these communities or houses).
For now, Whether you want to publish information honestly online: (Yes or No). 
(The reason why you want or don't want to publish information honestly online)
Your current plan is (Your plan to publish which kind of info online, be concise)"""
        
        publish_plan = await self.publish_forum_plan(publish_plan_respond_format,
                                               system=system,
                                               memory=publish_memory)
        
        
        self.reset_state(mode="publish_forum")
        mem_buffer = []
        tip=[]
        
        # 限制发布信息的小区，是否可以选择
        # available_community_ids = system.get_available_community_ids()
        # community_ids = ", ".join(available_community_ids)
        
        # 不限制发布信息的小区，是否可以选择
        community_ids = ", ".join(list(system.community_manager.total_community_datas.keys()))
        
        
        role_description = """Your task is to Publish house information or community information online.\
{role_des}"""
        role_description = role_description.format(role_des = self.get_role_description())

        prompt_inputs={
        'role_description':role_description,
        "plan":publish_plan.get("plan",""),
        'memory':publish_memory,
        "community_ids" :community_ids
        }
        
        for _ in range(self.max_jug_time):

            prompt_inputs["memory"] = publish_memory + "\n" + "".join(tip)
                        
            response = await self.astep(prompt_inputs)
            response = response.get("return_values",[])
            
            self.log_round_tenant.set_choose_history(prompt_inputs = prompt_inputs,
                    response = response,
                    step_type = "publish_forum")
            
            for publish in response:
                community_index =  publish.get("community")
                info_post = publish.get("info")
                try:
                    choose_community_idx= re.search("([0-9]+)",str(community_index),re.I | re.M)        
                    choose_community_idx = choose_community_idx.group(1)
                    
                    community_id = f"community_{choose_community_idx}".lower()
                    
                    assert community_id in system.community_manager.total_community_datas.keys(),\
                        "invalid community index"
                    
                    community_name = system.community_id_to_name(community_id)
                    
                    self.agentrule.publish_forum(
                                    forum_manager=forum_manager,
                                    tenant_id =self.id,
                                    tenant_name=self.name,
                                    community_name=community_name,
                                    community_id=community_id,
                                    info_post=info_post)
                    
                    publish["plan"] = publish_plan
                    self.update_memory(selfcontent=publish,
                                    step_type="publish",
                                    receivers={self.id:self.name})

                    self.log_round_tenant.set_comment("{c_name}:{info}".format(c_name = community_name,
                                                                   info = info_post))
                    return
                
                except:
                    tip.append(f"Remember to respond ActionInput in format.")
                    mem_buffer.append(publish)
                        
                
        

        thought_fail_publish="" # 每一次的选择都是非法结果
        for mem in mem_buffer:
            thought_fail_publish+=mem.get("thought","")
            
        self.update_memory(selfcontent={"thought":thought_fail_publish,
                            "output":"I fail to publish any information online."},
                           receivers={self.id:self.name},
                           step_type="publish")

        self.log_round_tenant.set_comment("I fail to publish any information online.")
    

    # old ver: search and publish, using ReAct
    def access_forum(self,tool):
        
        tools = tool.get_tools()
        # publish_func = tool.

        self.reset_state(mode="access_forum",
                         allowed_tools=tools)
                
        prompt_inputs={
        'task':'search for house information or community information.',
        'act_time':'TWO',
        'memory':self.memory.to_string_default(),
        'role_description':self.get_role_description()        
        }
        

        
        response = self.step(prompt_inputs,tools=tools)
        # self.logger.info("access forum, tenant response:{}".format(response.get("output","")))
        # parse community choosing reponse


        self.reset_state(mode="choose",
                         allowed_tools=[]) 
        
    # 待改，参考test\generative_model_simple.ipynb
    def rate_memory(self,
                    memory_list:List[Message],
                    task:str
                    ):
        
        def get_rating(x):
            nums = [int(i) for i in re.findall(r'\d+', x)]
            if len(nums)>0:
                return min(nums)
            else:
                return None
        prompt_meta="""You are {name}. 
    {role_description}
    Your are planning to {task}.
    You have the following memory:{memory_str}
    Give a rating, between 1 and 5, to how much you care about this."""
        
        for memory in memory_list:
            prompt = prompt_meta.format()
            res = self.llm(prompt_meta)
            memory.importance_rate = get_rating(res)
            
        
                