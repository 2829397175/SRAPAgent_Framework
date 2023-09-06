from pydantic import BaseModel, Field
from typing import List, Tuple, Set

from langchain.schema import AgentAction,BaseMessage
from datetime import datetime
from pydantic import BaseModel

# 这里导致prompt template返回类型有问题
class Message(BaseModel):
    timestamp: float
    message_type: str
    content: str
    importance_rate: float = 0
    relation_rate :float = 0
    sender: dict[str,str] = {"system":"system"} # tenant_id:tenant_name
    receiver: List[str] = []  # tenant_id:tenant_name
    tool_response: List[Tuple[AgentAction, str]] = Field(default=[])
    conver_num:int =0 #记录对话次数
    context: List[str] = [] #记录的上下文
    
    def __init__(self,**kwargs):
        now = datetime.now()
        timestamp = datetime.timestamp(now)
        super().__init__(timestamp = timestamp,
                         **kwargs)
        
    def sort_rate(self):
        return self.timestamp+self.importance_rate+self.relation_rate

    def type(self) -> str:
        """Type of the message, used for serialization."""
        return "chat"
    
    def __str__(self):
        return self.content
    


# class TenantMassage(Message):
#     make_choice:bool = False
#     chosed_housing_idx:int = -1