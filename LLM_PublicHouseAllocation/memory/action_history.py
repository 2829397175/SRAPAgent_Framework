from typing import List,Union,Dict

from pydantic import Field

from LLM_PublicHouseAllocation.message import Message

from . import memory_registry,summary_prompt_default
from .base import BaseMemory

from langchain.chains.llm import LLMChain
from langchain.base_language import BaseLanguageModel
from langchain.memory.prompt import SUMMARY_PROMPT
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts.base import BasePromptTemplate
from pydantic import BaseModel, root_validator


class SummarizerMixin(BaseModel):
    llm: BaseLanguageModel

    def predict_new_summary(
        self, 
        messages: List[Message], 
        existing_summary: str,
        prompt: BasePromptTemplate = SUMMARY_PROMPT
    ) -> str:
        new_lines = "\n".join([message.content for message in messages])

        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.predict(summary=existing_summary, new_lines=new_lines)


@memory_registry.register("action_history")
class ActionHistoryMemory(BaseMemory,SummarizerMixin):
    messages: Dict[str,List[Message]] = {} # 包括自己做的行为+自己想发的信息
    summarys: Dict[str,Message] = {} # 记录某类记忆的summary
    buffer_step: Dict[str,int] = {} # 记录某类mem，总结到哪个位置（index)
    summary_prompt = {"community":"community_summary",
                      "house_type":"house_type_summary",
                      "house":"house_summary",
                      "search":"forum_search_summary",
                      "publish":"forum_publish_summary",
                      "synthesize":"synthesize_summary",
                      "social_network":"synthesize_summary"}
    reflection:bool = False # 若设置为true,则触发分类reflection  
    summary_threshold:int = 5 # 每次总结后，再多5条就触发一次总结
    
    # 想要发出的message信息，在发出后清空，加入messages中
    post_message_buffer: List = []
    
    
    def add_message(self, 
                    messages: List[Message],
                    post = False,
                    receive = False) -> None:
        if post:
            self.post_message_buffer.extend(messages)
            return

        messages_pt = self.messages
        buffer_step_pt = self.buffer_step
            
        for message in messages:
            if message.message_type in messages_pt.keys():
                messages_pt[message.message_type].append(message)
                
            else:
                messages_pt[message.message_type]=[message]
                buffer_step_pt[message.message_type]=-1
                
        for type_m in messages_pt.keys():
            if len(messages_pt[type_m]) - \
                buffer_step_pt[type_m] > self.summary_threshold:
                    self.summary_type_memory(type_message = type_m,
                                            receive = receive)
            
                
    def post_meesages(self):
        for message in self.post_message_buffer:
            self.add_message([message])
        post_messages = self.post_message_buffer.copy()
        self.post_message_buffer = []
        return post_messages
        
    def topk_message_default(self,
                             messages:List[Message],
                             k=10)->List[Message]:
        messages.sort(key=lambda x: x.sort_rate())
        return messages[:k] if k<len(messages) else messages
    
    # choose类别的记忆选择："community","house_type","house"
    # 例：community的memory选择
        # 种类选择search_forum，publish_forum，choose_community 类记忆
        # 先按照时间排序所有没被总结summary的记忆，选其中前三条
        # 再添加search_forum，publish_forum，choose_community的summary记忆
    
        
    
    
    

    def summary_synthesize_memory(self,messages:List[Message])->str:
        yaml_key = self.summary_prompt.get("synthesize")
        prompt_template = summary_prompt_default.get(yaml_key,"")
        prompt = PromptTemplate(input_variables=["summary", "new_lines"], 
                                template=prompt_template)
        summerize_mem = self.predict_new_summary(messages=messages,
                                                existing_summary="",
                                                prompt=prompt)
        return Message(content = summerize_mem,
                       message_type = "synthesize",
                       sender = {"system":"system"}
                       )
        
    def summary_type_memory(self,
                            type_message:Union[str,List[str]] = "all",
                            receive = False)->str:

        messages_pt = self.messages
        message_summary_pt = self.summarys
        buffer_step_pt = self.buffer_step
        
        type_messages = [type_message] if not isinstance(type_message,list) else type_message
        for type_m in type_messages:
            start_idx = buffer_step_pt[type_m] + 1
            new_messages = messages_pt[type_m][start_idx:]
            
            if receive:
                # receive的memory暂时都用这个进行summary
                prompt_template = summary_prompt_default.get("synthesize_summary","") 
            else:
                yaml_key = self.summary_prompt.get(type_m)
                prompt_template = summary_prompt_default.get(yaml_key,"")
                
            prompt = PromptTemplate(input_variables=["summary", "new_lines"], 
                                    template=prompt_template)
            summerize_mem = self.predict_new_summary(messages=new_messages,
                                                     existing_summary=message_summary_pt.get(type_m,""),
                                                     prompt=prompt)
            message_summary_pt[type_m] = Message(message_type = type_m,
                                            content = summerize_mem.strip())
            
             # 总结了所有最新信息，更新总结位置
            buffer_step_pt[type_m] = len(messages_pt[type_m]) -1
            

    def to_string(self, 
                  messages:List[Message],
                  add_sender_prefix: bool = False,
                  ) -> str:
        if add_sender_prefix:
            return "\n".join(
                [
                    f"[{list(message.sender.values())[0]}]: {message.content}"
                    if list(message.sender.values())[0] != ""
                    else message.content
                    for message in messages
                ]
            )
        else:
            return "\n".join([message.content for message in messages])
        
    def to_string_default(self, 
                  add_sender_prefix: bool = False,
                  type_message:Union[str,List[str]] = "all",
                  ) -> str:
        
        messages_return=[]
        if (type_message=="all") or ("all" in type_message):
            type_messages = list(self.messages.keys())

        type_messages = [type_message] if not isinstance(type_message,list) else type_message
        
        for type_m in type_messages:
            if (type_m in self.messages.keys()):
                messages_return.extend(self.messages.get(type_m,[]))
        

        messages_return = self.topk_message_default(messages_return)
        
        if add_sender_prefix:
            return "".join(
                [
                    f"[{message.sender}]: {message.content}"
                    if message.sender != ""
                    else message.content
                    for message in messages_return
                ]
            )
        else:
            return "".join([message.content for message in messages_return])

    def reset(self) -> None:
        self.messages = {}
        self.summarys = {}
        self.post_message_buffer = []


    ###############         一系列的 retrive memory rule       ##############
    
    #  调用各类 retrive 方法
    def memory_tenant(self,mem_type:str)->str:
        TYPE_MEM={
            "community":["community","social_network"],
            "house_type":["house_type","social_network"],
            "house":["house","social_network"],
            "search":["search"],
            "publish":["search","publish","community","house","house_type",
                       "social_network",],
            
            
        }
        
        if mem_type in TYPE_MEM.keys():# 默认retrive方法
            type_messages = TYPE_MEM.get(mem_type,[]) 
            return self.retrive_basic(type_messages=type_messages,
                                      mem_type=mem_type)
        elif mem_type == "social_network":# social_network retrive方法
            return self.retrive_group_discuss_memory()
        else: 
            return ""
        
        
    
    # 默认retrive方法
    def retrive_basic(self,
                      type_messages:List[str],
                      mem_type:str):
        
        if not self.reflection:
            return self.to_string_default(add_sender_prefix=False,
                                        type_message=type_messages)
        else:
            messages_str = []
            for type_m in type_messages:
                if (type_m in self.messages.keys()):
                    messages_str.extend(self.messages[type_m][self.buffer_step[type_m]+1:])
            
            messages_str.sort(key=lambda x: x.timestamp,reverse=True)
            # 零散记忆限制数量为3
            messages_str = messages_str[:3] if len(messages_str)>3 else messages_str
            # 零散记忆需要summary吗?暂时没有归到summary的记忆中
            
            if mem_type == "publish" and len(messages_str)>0:
                messages_str=[self.summary_synthesize_memory(messages_str)]
            
            for type_m in type_messages:
                if (type_m in self.summarys.keys()):
                    messages_str.append(self.summarys.get(type_m))
            
            return self.to_string(messages=messages_str,
                                  add_sender_prefix=True)
    
    # social_network retrive方法
    def retrive_group_discuss_memory(self):
        
        type_messages=["search","publish","community","house","house_type"]
        
        if not self.reflection:
            return self.to_string_default(add_sender_prefix=False,
                                        type_message=type_messages)
            
            
        template_memory="""\
{memory_house_info}\n\n\
Here's your discussion with your acquaintances:\n\n\
{discussion}"""

        # memory_house_info 部分
        messages_str = []
        for type_m in type_messages:
            if (type_m in self.messages.keys()):
                messages_str.extend(self.messages[type_m][self.buffer_step[type_m]+1:])
                
        messages_str.sort(key=lambda x: x.timestamp,reverse=True)
        messages_str = messages_str[:3] if len(messages_str)>3 else messages_str
        
        for type_m in type_messages:
            if (type_m in self.summarys.keys()):
                messages_str.append(self.summarys.get(type_m))
        
        memory_house_info = self.to_string(messages=messages_str,
                                add_sender_prefix=True)
        
        # discussion 部分
        messages_social_net = self.messages.get('social_network',[])
        messages_social_net.sort(key=lambda x: x.timestamp,reverse=True)
        messages_social_net = messages_social_net[:3] if len(messages_social_net)>3 else messages_social_net
        
        if ('social_network' in self.summarys.keys()):
            messages_social_net.append(self.summarys.get('social_network'))
            
        discussion = self.to_string(messages = messages_social_net,
                                add_sender_prefix=True)
        
        return template_memory.format(memory_house_info=memory_house_info,
                                      discussion=discussion)

            
