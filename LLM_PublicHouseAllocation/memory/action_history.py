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
                      "synthesize":"synthesize_summary"}
    reflection:bool = False # 若设置为true,则触发分类reflection  
    summary_threshold:int = 5 # 每次总结后，再多5条就触发一次总结
    
    received_messages: Dict[str,List[Message]] = {} # 接受social network 信息
    received_summarys: Dict[str,Message] = {} # 记录social network信息 的summary
    received_buffer_step: Dict[str,int] = {} # 记录某类mem，总结到哪个位置（index)
    # 想要发出的message信息，在发出后清空，加入messages中
    post_message_buffer: List = []
    
    
    def add_message(self, 
                    messages: List[Message],
                    post = False,
                    receive = False) -> None:
        if post:
            self.post_message_buffer.extend(messages)
            return

        if receive:
            messages_pt = self.received_messages
            buffer_step_pt = self.received_buffer_step
        else:
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
                                            receive=receive)
            
                
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
    
    def memory_tenant(self,mem_type:str)->str:
        TYPE_MEM={
            "community":["community",{"receive":"social_network"}],
            "house_type":["house_type",{"receive":"social_network"}],
            "house":["house",{"receive":"social_network"}],
            "search":["search"],
            "publish":["search","publish","community","house","house_type",
                       {"receive":"social_network"},],
            "social_network":["search","publish","community","house","house_type",
                       {"receive":"social_network"}],
            
        }
        type_messages = TYPE_MEM.get(mem_type,[])
        
        if not self.reflection:
            return self.to_string_default(add_sender_prefix=False,
                                        type_message=type_messages)
        else:
            messages_str = []
            for type_m in type_messages:
                if isinstance(type_m,dict):
                    receive_type_messages = type_m.get("receive",[])
                    for receive_type_m in receive_type_messages:
                        if (receive_type_m in self.received_messages.keys()):
                            messages_str.extend(self.received_messages[type_m][self.received_buffer_step[type_m]+1:])
                
                elif (type_m in self.messages.keys()):
                    messages_str.extend(self.messages[type_m][self.buffer_step[type_m]+1:])
            
            messages_str.sort(key=lambda x: x.timestamp)
            # 零散记忆限制数量为3
            messages_str = messages_str[:3] if len(messages_str)>3 else messages_str
            # 零散记忆需要summary吗?暂时没有归到summary的记忆中
            
            if mem_type == "publish" and len(messages_str)>0:
                messages_str=[self.summary_synthesize_memory(messages_str)]
            
            for type_m in type_messages:
                if isinstance(type_m,dict):
                    receive_type_messages = type_m.get("receive",[])
                    for receive_type_m in receive_type_messages:
                        if (receive_type_m in self.received_summarys.keys()):
                            messages_str.append(self.received_summarys[type_m])
                
                elif (type_m in self.summarys.keys()):
                    messages_str.append(self.summarys.get(type_m))
            
            return self.to_string(messages=messages_str)
    

    def summary_synthesize_memory(self,messages:List[Message])->str:
        yaml_key = self.summary_prompt.get("synthesize")
        prompt_template = summary_prompt_default.get(yaml_key,"")
        prompt = PromptTemplate(input_variables=["summary", "new_lines"], 
                                template=prompt_template)
        summerize_mem = self.predict_new_summary(messages=messages,
                                                existing_summary="",
                                                prompt=prompt)
        return Message(content=summerize_mem,
                       message_type = "synthesize")
        
    def summary_type_memory(self,
                            type_message:Union[str,List[str]] = "all",
                            receive = False)->str:
        if receive:
            messages_pt = self.received_messages
            message_summary_pt = self.received_summarys
            buffer_step_pt = self.received_buffer_step
        else:
            messages_pt = self.messages
            message_summary_pt = self.summarys
            buffer_step_pt = self.buffer_step
        
        type_messages = [type_message] if not isinstance(type_message,list) else type_message
        for type_m in type_messages:
            start_idx = buffer_step_pt[type_m] + 1
            new_messages = messages_pt[type_m][start_idx:]
            
            if receive:
                type_m="synthesize"

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
            if type_m!='synthesize':
                buffer_step_pt[type_m] = len(messages_pt[type_m]) -1
            

    def to_string(self, 
                  messages:List[Message],
                  add_sender_prefix: bool = False,
                  ) -> str:
        if add_sender_prefix:
            return "".join(
                [
                    f"[{message.sender}]: {message.content}"
                    if message.sender != ""
                    else message.content
                    for message in messages
                ]
            )
        else:
            return "".join([message.content for message in messages])
        
    def to_string_default(self, 
                  add_sender_prefix: bool = False,
                  type_message:Union[str,List[str]] = "all",
                  ) -> str:
        
        messages_return=[]
        if (type_message=="all") or ("all" in type_message):
            type_messages = list(self.messages.keys())

        type_messages = [type_message] if not isinstance(type_message,list) else type_message
        
        for type_m in type_messages:
            if isinstance(type_m,dict):
                receive_type_messages = type_m.get("receive",[])
                for receive_type_m in receive_type_messages:
                    if (receive_type_m in self.received_messages.keys()):
                        messages_return.extend(self.received_messages.get(receive_type_m,[]))
            
            elif (type_m in self.messages.keys()):
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
        self.received_messages = {}
        self.received_summarys = {}
        self.post_message_buffer = []
