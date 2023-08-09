# from LLM_PublicHouseAllocation.manager import ForumManager
# from LLM_PublicHouseAllocation.involvers import System,Tool,Search_forum_topk
from LLM_PublicHouseAllocation.memory import ActionHistoryMemory
from LLM_PublicHouseAllocation.message import Message

from LLM_PublicHouseAllocation.prompt.chat_prompt import (ForumPromptTemplate,
                                                          ChoosePromptTemplate,
                                                          PublishPromptTemplate,
                                                          CommentPromptTemplate,
                                                          GroupDiscussPromptTemplate,
                                                          ActionPlanPromptTemplate)
from LLM_PublicHouseAllocation.output_parser import (OutputParseError,
                                                     ForumParser,
                                                     ChooseParser,
                                                     PublishParser,
                                                     CommentParser,
                                                     GroupDiscussParser,
                                                     ActionPlanParser)
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
from LLM_PublicHouseAllocation.tenant.agent_rule import AgentRule


class LangchainTenant(langchainAgent):
    id :str
    name :str   
    infos : dict 
    memory : ActionHistoryMemory
    choose_times:int = 0
    max_choose:int = 3
    available:bool = True
    max_jug_time : int = 1 # 错误结果的retry次数
    max_retry:int = 5 #访问api
    workplace: str = ""  # 用来记录工作点的中文名
    friends: dict = {}
    mode : str ="choose" # 控制llm_chain 状态（reset_state中改）
    # 这个是为了更改llm_chain
    llm:BaseLanguageModel
    
    agentrule:AgentRule
    
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
        # memory = ActionHistoryMemory(llm=kwargs.get("llm",OpenAI()))
        super().__init__(agentrule=rule, 
                         **kwargs)
    
    class Config:
        arbitrary_types_allowed = True
    
    def update_times(self,chose=False):
        if chose:
            self.available = False
        else:
            self.choose_times+=1
            if(self.choose_times>=self.max_choose):
                self.available = False
    
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
    
    @property
    def return_values(self) -> List[str]:
        """Return values of the agent."""
        return ["output","thought"]
    
    @property
    def input_keys(self) -> List[str]:
        """Return the input keys.

        :meta private:
        """
        #input_keys=set(self.llm_chain.input_keys) - {"intermediate_steps"}
        return list(set(self.llm_chain.input_keys)-{"agent_scratchpad"})
    
    @root_validator()
    def validate_prompt(cls, values) :
        """Validate that prompt matches format."""
        prompt = values["llm_chain"].prompt
        if "agent_scratchpad" not in prompt.input_variables:
            prompt.input_variables.append("agent_scratchpad")
            if isinstance(prompt, ChoosePromptTemplate):
                prompt.template += "\n{agent_scratchpad}"
        return values
    
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
    
    def reset_state(self,
                     mode = "access_forum",
                     verbose :bool = False,
                     allowed_tools :Optional[List[str]] = []):
        STATES=("access_forum",
                "publish_forum",
                "choose",
                "comment",
                "group_discuss",
                "action_plan")
        
        assert mode in STATES
        if self.mode == mode : return
        
        
        if mode == "access_forum":
            prompt = ForumPromptTemplate(tools=allowed_tools)
            output_parser = ForumParser(tenant_name=self.name)
        elif mode =="group_discuss":
            prompt = GroupDiscussPromptTemplate()
            output_parser = GroupDiscussParser()
        elif mode == "action_plan":
            prompt = ActionPlanPromptTemplate()
            output_parser = ActionPlanParser()
        elif mode == "choose":
            prompt = ChoosePromptTemplate()
            output_parser = ChooseParser()
        elif mode == "publish_forum":
            prompt = PublishPromptTemplate()
            output_parser = PublishParser(tenant_name=self.name)
        elif mode == "comment":
            prompt = CommentPromptTemplate()
            output_parser = CommentParser()     
        
        self.mode = mode
        self.llm_chain = self.chain(prompt=prompt,verbose=verbose)
        self.output_parser = output_parser
        self.allowed_tools = allowed_tools
            
    def update_memory(self,
                      response,
                      step_type,
                      output_keys = ["thought","output"],
                      post = False,
                      receivers :List[str] = None # list of tenant ids
                     ):
        STEP_TYPES=(
            "community",
            "house_type",
            "house",
            "publish",
            "search",
            "social_network"
        )
        assert step_type in STEP_TYPES, "invalid type of step"
        
        content = [f"{key.capitalize()}:{response[key]}"for key in output_keys]
        content = "\n".join(content)
        
        # if receivers is None:
        #     receivers = list(self.friends.keys()) if post else [self.id] 
        
        message = Message(
            content = content,
            sender = {self.id:self.name},
            receiver = receivers,
            message_type = step_type,
            tool_response = response.get('intermediate_steps',[])
        ) # 暂时只给自己发信息
        
        self.memory.add_message(messages=[message],post = post)
        
    # 发信息给其他tenant
    def post_messages(self):
        post_messages = self.memory.post_meesages()
        return post_messages
    
    def receive_messages(self,messages:List[Message]=[]):
        for message in messages:
            self.memory.add_message(messages=[message],receive=True)
    
    def step(self, 
             prompt_inputs:dict, 
             step_type:str = "",
             tools=[],
             update_memory = False,
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
        if response is None:
            # raise ValueError(f"{self.name} failed to generate valid response.")
            return {"output":f"{self.name} failed to generate valid response.",
                    "thought":""
                    }
        
        if update_memory:
            self.update_memory(response=response,
                               step_type=step_type,
                               )
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
        allowed_tools :Optional[List[str]] = None,
        max_choose:int = 3,
        friends:dict = {}
    ) -> langchainAgent:
        """Construct an agent from an LLM and tools."""
        llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
        )
        
        memory = load_memory(memory_config=memory_config)
        return cls(
            llm_chain = llm_chain,
            output_parser = output_parser,
            allowed_tools = allowed_tools,
            llm = llm,
            id = id,
            name = name,
            rule = rule,
            infos = infos,
            memory = memory,
            max_choose = max_choose,
            workplace = work_place,
            friends = friends
        )
        
    def reset(self):
        self.memory.reset()
        
    def get_role_description(self):
        
        template="""
You are {name}. You earn {monthly_income} per month.
Your family members include: {family_members}.
You are {age} years old. Your job is {profession}. 
Your company is located in {en_work_place}. 
{special_request} 
You expect to rent a house for {monthly_rent_budget}.
You still have {chance_num} chances to choose house.
"""
        return template.format_map({"name":self.name,
                                    "chance_num":self.max_choose-self.choose_times,
                                    **self.infos}
                                   )
    
    def action_plan(self,
                    actions:dict,
                    forum_manager,
                    system,
                    log_round,
                    tool=None,
                    max_action_round=5):
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
        
        for _ in range(max_action_round):
            observation=""
            prompt_inputs={
                'actions':action_usages,
                'action_names':action_names,
                'memory':"",
                'role_description':self.get_role_description(),
                'history':action_log
                }

            self.reset_state(mode="action_plan")
            response = self.step(prompt_inputs,
                                step_type="action_plan",
                                update_memory=False)
            
            action = response.get("output","")
            thought = response.get("thought","")
            if action == "Search":
                self.search_forum(forum_manager,
                                  system,log_round)
                observation="I have searched some info on forum."
            elif action == "Publish":
                self.publish_forum(forum_manager,
                                   system,
                                   log_round)
                observation="I have published some info on forum."
            elif action == "GroupDiscuss":
                self.group_discuss()
                observation="I have discussed with my acquaintances."
            elif action == "Choose":
                choose_state,choose_house_id = self.choose_pipeline(
                        forum_manager=forum_manager,
                        system=system,
                        tool=tool,
                        log_round=log_round)
                log_round.set_choose_house_state(choose_state)
                forum_manager.save_data()
            else: 
                continue
        
            
            action_log +=\
                "Thought:{thought}\nAction:{action}\nObservation:{observation}".format_map({
                    "thought":thought,
                    "action":action,
                    "observation":observation
                })
            
    # 异步的communication过程，包括四种动作（一种放弃）
    async def async_communication(self,
                                  forum_manager,
                                  system,
                                  log_round,
                                  max_action_round=5 # 最多做几个动作
                                  ):
        actions = {
            "Search":"search house info from forum",
            "Publish":"publish house info on forum",
            "GroupDiscuss":"discuss with other people about house renting",
            "Giveup":"do nothing"
            }
        self.action_plan(actions=actions,
                         forum_manager=forum_manager,
                         system=system,
                         log_round=log_round,
                         max_action_round=max_action_round)

    
    def choose_process(self, 
               forum_manager, 
               system, 
               tool, 
               log_round):
        
        actions = {
            "Choose":"Conduct the house choosing process",
            "Giveup":"do nothing"
            }
        self.action_plan(actions=actions,
                         forum_manager=forum_manager,
                         system=system,
                         log_round=log_round,
                         tool=tool,
                         max_action_round=1) 
        # 进行1轮，先是否进行选房流程的判断，若否则直接返回
        
    def choose_pipeline(self,
                        forum_manager, 
                        system, 
                        tool, 
                        log_round):
        log_round.set_tenant_information(self.id,self.name,self.max_choose - self.choose_times)
        # log_round["tenant_id"] = self.id
        # log_round["tenant_name"] = self.name
        # log_round["available_times"] = self.max_choose - self.choose_times
            
        choose_state = False
        # search_forum test
        # search_infos = self.search_forum(tool,log_round)
        search_infos = self.search_forum(forum_manager=forum_manager,
                                         system=system,
                                         log_round=log_round)

        
        choose_state, community_id, community_choose_reason = self.choose_community(system,search_infos,log_round)
        log_round.set_choose_community(community_id,community_choose_reason)
        # log_round["choose_community_id"] = community_id
        # log_round["choose_community_reason"] = community_choose_reason
        
        if not choose_state:
            self.update_times(choose_state)
            self.publish_forum(forum_manager,system,log_round)
            return False,"None"
        
        # test
        # self.access_forum(tenant_id=tenant_id)
        
        choose_state, house_type_id, house_type_reason = self.choose_house_type(system,community_id,log_round)
        # log_round["choose_house_type"] = house_type_id
        # log_round["choose_house_type_reason"] = house_type_reason
        log_round.set_choose_house_type(house_type_id,house_type_reason)
        if not choose_state:
            self.update_times(choose_state)
            self.publish_forum(forum_manager,system,log_round)
            return False,"None"
        
        if not isinstance(house_type_id,list):
            house_filter_ids = [house_type_id] #这里存储 某个community中的，某些类型的房子
        else:
            house_filter_ids = house_type_id
            
            
       
            
        choose_state, house_id, house_choose_reason = self.choose_house(
                                                   system,
                                                   community_id,
                                                   house_filter_ids,
                                                   log_round)
        
        # log_round["choose_house_id"] = house_id
        # log_round["choose_house_reason"] = house_choose_reason
        log_round.set_choose_house(house_id,house_choose_reason)
        
        self.publish_forum(system=system,
                           forum_manager=forum_manager,
                           log_round=log_round)
        # 更改tenant 的选择状态
        self.update_times(choose_state)
             
        if not choose_state:
            return False,"None"
        
        # 更改communitymanager中的remain_num
        system.set_chosed_house(house_id,community_id,house_filter_ids)

        return True,house_id.lower()
             
        
    
        
    # 一系列房子选择的函数，理想中要整合成pipeline之类的格式(待改)
    
    def group_discuss(self):
        self.reset_state(mode="group_discuss")
        friends = ["{name}: {relation}".format(
                    name = neigh_tenant_info.get("name",neigh_tenant_id),
                    relation =neigh_tenant_info.get("relation","friend")
                    )
                     for neigh_tenant_id,neigh_tenant_info
                     in self.friends.items()] 
        friends = "\n".join(friends)
                
        prompt_inputs={
                'friends':friends,
                'memory':self.memory.memory_tenant("social_network"),
                'role_description':self.get_role_description(),
                'tenant_name':self.name
                }
        
        print("SENDER:{name}".format(name=self.name)) #debug
        
        response = self.step(prompt_inputs,
                    step_type="social_network",
                    update_memory=False)
        
        if response.get("output") =="fail to discuss":
            return
        else:
            receivers = response.get("friends",[])
            receivers = receivers.split(",") # list of tenant names
            receivers_transfered = {} # tenant id:tenant_name
            for receiver in receivers:
                receiver = receiver.strip()
                for friend_id,friend_info in self.friends.items():
                    if (receiver.lower() in friend_info["name"].lower()):
                        receivers_transfered[friend_id] = friend_info["name"]
                        

            self.update_memory(response=response,
                             step_type="social_network", 
                             receivers=receivers_transfered,  
                             output_keys=["thought","action","friends","output"] ,                       
                             post=True)
            
    
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
        
        response = self.step(prompt_inputs,
                    step_type=step_type,
                    update_memory=False)
        
        if response.get("output") =="I fail to make comments.":
            return
        else:
            receivers={}
            for tenant_id,tenant_info in self.friends:
                receivers[tenant_id] = tenant_info.get("name","")
                
            self.update_memory(response=response,
                             step_type=step_type,
                             receivers=receivers,
                             post=True)
        
    
    # 返回：（是否选择，选择编号）
    def choose_community(self,system,search_infos,log_round) ->Tuple[bool,str]:
        mem_buffer=[]
        tip=[]
        
        community_data = system.get_community_data()
        for community_index,community_info in community_data.items():
            community_info.update(search_infos.get(community_index,{}))
            
        community_description = self.agentrule.read_community_list(community_data)
        
        for _ in range(self.max_jug_time):
            # community_description = system.community_manager.get_available_community_abstract()
            prompt_inputs={
                'task':'You need to choose one type of communities.',
                'thought_type':'Your views on these communities.',
                'choose_type':'The index of community.',
                'house_info':community_description,
                'memory':"".join(tip)+self.memory.memory_tenant("community"),
                'role_description':self.get_role_description()        
                }
            # self.comment(description=community_description,
            #              step_type="community")
            
            
            #log_round["community_available_description"] = community_description
            log_round.set_available_community_description(community_description)
            self.reset_state(mode="choose")
            response = self.step(prompt_inputs,
                                step_type="community",
                                update_memory=False)
            # self.logger.info("choose community, tenant reponse:{}".format(response.get("output","")))
            # parse community choosing reponse
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
                if (system.jug_community_valid(choose_idx)):
                    self.update_memory(response=response,
                                       receivers={self.id:self.name},
                                       step_type="community")
                    return True, choose_idx.lower(), response.get("thought","")
                else:
                    tip.append(f"{choose_idx.lower()} is not available now.")

                    mem_buffer.append(response)
            else:
                self.update_memory(response=response,
                                   receivers={self.id:self.name},
                                    step_type="community")
                return False,"None", response.get("thought","")
        
        thought_fail_choose="" # 每一次的选择都是非法结果
        for mem in mem_buffer:
            thought_fail_choose+=mem.get("thought","")
            
        self.update_memory(response={"thought":thought_fail_choose,
                            "output":"I fail to choose valid community."},
                           receivers={self.id:self.name},
                           step_type="community")
        
        return False,"None", thought_fail_choose
                
        
        
    def choose_house_type(self,system,community_id,log_round) -> Tuple[bool,str]:
        mem_buffer=[]
        tip=[]
        for _ in range(self.max_jug_time):
            house_type_description = system.get_house_type(community_id)
            prompt_inputs={
                'task':'You need to choose one type of houses.',
                'thought_type':'Your views on these house types.',
                'choose_type':'house type.',
                'house_info':house_type_description,
                'memory':"".join(tip)+self.memory.memory_tenant("house_type"),
                'role_description':self.get_role_description()        
                }
            
            # self.comment(description=house_type_description,
            #              step_type="house_type")
            
            
            #log_round["available_house_type"] = system.community_manager.get_available_house_type(community_id)
            log_round.set_available_house_type(system.get_available_house_type(community_id))
            self.reset_state(mode="choose")
            response = self.step(prompt_inputs,
                                step_type="house_type",
                                update_memory=False)
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
                if (system.jug_community_housetype_valid(community_id,choose_idx)):   
                    self.update_memory(response=response,
                                       receivers={self.id:self.name},
                                       step_type="house_type")
                    return True, choose_idx.lower(), response.get("thought","")
                else:
                    tip.append(f"{choose_idx.lower()} is not available any more, keep this in mind.")
                    mem_buffer.append(response)
            else:
                self.update_memory(response=response,
                                   receivers={self.id:self.name},
                                    step_type="house_type")
                return False,"None", response.get("thought","")
        
        thought_fail_choose="" # 每一次的选择都是非法结果
        for mem in mem_buffer:
            thought_fail_choose+=mem.get("thought","")
            
        self.update_memory(response={"thought":thought_fail_choose,
                            "output":"I fail to choose valid house type."},
                           receivers={self.id:self.name},
                           step_type="house_type")
        
        return False,"None", thought_fail_choose
            
    def choose_house_page(self, 
                          house_infos, 
                          house_ids:list, 
                          page_size:int = 20,
                          log_round_houses:list=[],
                          round_retry:int = 0,
                          tip:list=[]):
        # houses_description_generator = system.get_houses_generator(house_ids=house_ids,
        #                                                             page_size=page_size,
        #                                                             log_round_houses=log_round["house_available_description"],
        #                                                             round_retry = round_retry)
        
        houses_description_generator = self.agentrule.get_houses_generator(
                             house_data = house_infos,
                             house_ids = house_ids,
                             page_size = page_size, 
                             round_retry = round_retry
                             )
        
        choose_page_results = []
        nochoose_memory_cache = []
        choose_memory_cache = []
        
        for houses_description in houses_description_generator:
            # self.logger.info("SYSTEM:\n {}".format(houses_description))
            
            prompt_inputs={
                'task':'You need to choose one house.',
                'thought_type':'Your views on these houses.',
                'choose_type':'The index of houses.',
                'house_info':houses_description,
                'memory':"".join(tip)+self.memory.memory_tenant("house"),
                'role_description':self.get_role_description()        
                }
            # self.comment(description=houses_description,
            #              step_type="house")
            
            self.reset_state(mode="choose")
            response = self.step(prompt_inputs,
                                 step_type="house",
                                 update_memory=False) # 这里不更新记忆，仅更新最后一步
            # self.logger.debug("choose houses, tenant reponse:{}".format(response.get("output","")))
            # parse community choosing reponse
        
            
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
            return self.choose_house_page(house_infos,
                                          choose_page_results,
                                          page_size=page_size,
                                          log_round_houses=log_round_houses)
        
        elif len(choose_page_results) == 1:
            choose_house=choose_page_results[0]
            return True, choose_house, choose_memory_cache

        
        # 最终一个都没选的话，将所有不选择的记忆都更新（仅末页）
        # no_choose_thought=""
        # for nochoose_memory in nochoose_memory_cache:
        #     self.update_memory(response=nochoose_memory,
        #                        step_type="house",
        #                        )
        #     no_choose_thought += nochoose_memory.get("thought","")
            
        return False,"None", nochoose_memory_cache

        
    def choose_house(self,
                     system,
                     community_id,
                     house_filter_ids:list, 
                     log_round:dict)->Tuple[bool,str]:
        house_ids = system.get_filtered_houses_ids(community_id=community_id,
                                                        house_filter_ids=house_filter_ids)
        #log_round["house_available_description"] = []
        house_infos=system.house_ids_to_infos(house_ids)            
        log_round.set_available_house_description(house_infos)
        mem_buffer = []
        tip=[]
        for round_retry in range(self.max_jug_time):
            choose_status,choose_id,choose_mem = \
            self.choose_house_page(house_infos,
                                   house_ids=house_ids,
                                   page_size=20,
                                   round_retry=round_retry,
                                   tip=tip)
            
            if (choose_status):
                if (system.jug_house_valid(choose_id)):
                    assert len(choose_mem)==1
                    # 选择了房子的情况，只更新关于选择的房子的记忆
                    self.update_memory(response=choose_mem[0],
                                       receivers={self.id:self.name},
                                    step_type="house",
                                    ) 
                    
                    # 在选择完一个房子后，记忆中添加房子相关暗信息   
                    dark_info = system.get_house_dark_info(choose_id)
                    self.update_memory(response={"output":dark_info},
                                       receivers={self.id:self.name},
                                    step_type="house",
                                    output_keys=["output"])
                    
                    return True, choose_id, choose_mem[0].get("thought")
                else:
                    tip.append(f"House_{choose_id} has been chosen, keep this in mind.")
                    mem_buffer.append(choose_mem[0])
            else:
                no_choose_thought=""
                for nochoose_memory in choose_mem:
                    self.update_memory(response=nochoose_memory,
                                       receivers={self.id:self.name},
                                        step_type="house",
                                        )
                    no_choose_thought += nochoose_memory.get("thought","")   
                return False, choose_id, no_choose_thought     
        
        thought_fail_choose="" # 每一次的选择都是非法结果
        for mem in mem_buffer:
            thought_fail_choose+=mem.get("thought","")
            
        self.update_memory(response={"thought":thought_fail_choose,
                            "output":"I fail to choose valid house."},
                           receivers={self.id:self.name},
                           step_type="house")
        
        return False,"None", thought_fail_choose
        
    
    
    
    def search_forum(self,
                     forum_manager,
                     system,
                     log_round,
                     search_list:List=None
                    ):
        
        # 暂时从小区列表里随机选两个小区
        k_c = 2
        forum_data = forum_manager.data
        len_forum = len(forum_data)
        k_c = len_forum if k_c>len_forum else k_c
        community_infos = system.get_community_data()
        
        if search_list is None:
            search_list=system.get_available_community_ids()
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
                
   
                
        # template = """{community_index}:{search_info}. This community is {get_shortest_commute_time_str} away from my workplace."""
        
        # return_infos_str = [template.format_map({"community_index":community_index,
        #                                         **search_info}) 
        #                     for community_index,search_info in return_infos.items()]
        return_infos_str=log_round.set_forum_conclusion(return_infos)
        for return_info in return_infos_str:
            self.update_memory(
                            response={"output":return_info},
                            step_type="search",
                            receivers={self.id:self.name},
                            output_keys=["output"])          
        
        # return_infos_str = "\n".join(return_infos_str) 
        # log_round["forum_conclusion"] = return_infos_str
        return return_infos
    
    # publish info only, using ReAct
    def publish_forum(self,
                      forum_manager,
                      system,
                      log_round):
        
        self.reset_state(mode="publish_forum",)
        mem_buffer = []
        tip=[]
        available_community_ids = system.get_available_community_ids()
        community_ids = ", ".join(available_community_ids)
          
        for _ in range(self.max_jug_time):
            prompt_inputs={
            'task':'Publish house information or community information online.',
            'memory':"".join(tip)+self.memory.memory_tenant("publish"),
            'role_description':self.get_role_description(),
            "community_ids" :community_ids
            }
            
            
            response = self.step(prompt_inputs,
                                step_type="publish",
                                update_memory=False)
            
            if (response.get("publish",False)):
                information = response.get("information","").split(",")
                community_index = information[0]
                community_info = information[1:] if len(information)>=2 else ""
                info_post = ",".join(community_info)
                try:
                    choose_community_idx= re.search("([0-9]+)",str(community_index),re.I | re.M)        
                    choose_community_idx = choose_community_idx.group(1)
                    
                    community_id = f"community_{choose_community_idx}".lower()
                    
                    assert system.jug_community_valid(community_id)
                    
                    community_name = system.community_id_to_name(community_id)
                    
                    self.agentrule.publish_forum(
                                    forum_manager=forum_manager,
                                    tenant_id =self.id,
                                    tenant_name=self.name,
                                    community_name=community_name,
                                    community_id=community_id,
                                    info_post=info_post)
                    
                    response["output"]="{community_name}:{info_post}".format(community_name=community_name,
                                                                             info_post=info_post)
                    
                    self.update_memory(response=response,
                                       step_type="publish",
                                       receivers={self.id:self.name})
                    #log_round["produce_comment"] = response.get("output","")
                    log_round.set_comment(response.get("output",""))
                    self.reset_state(mode="choose",
                            allowed_tools=[]) 
                    return
                
                except:
                    tip.append(f"Remember to respond ActionInput in format.")
                    mem_buffer.append(response)
                    
            else:

                tip.append(f"Remember to take action in [Publish,Giveup]")
                mem_buffer.append(response)
                
        

        thought_fail_publish="" # 每一次的选择都是非法结果
        for mem in mem_buffer:
            thought_fail_publish+=mem.get("thought","")
            
        self.update_memory(response={"thought":thought_fail_publish,
                            "output":"I fail to publish any information online."},
                           receivers={self.id:self.name},
                           step_type="publish")
    
        # self.logger.info("publish forum, tenant response:{}".format(content))
        # parse community choosing reponse
        #log_round["produce_comment"] = "I fail to publish any information online."
        log_round.set_comment("I fail to publish any information online.")
    
        self.reset_state(mode="choose",
                        allowed_tools=[]) 

    # old ver: search and publish ,using ReAct
    def access_forum(self,tool,log_round):
        
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
            
        
                