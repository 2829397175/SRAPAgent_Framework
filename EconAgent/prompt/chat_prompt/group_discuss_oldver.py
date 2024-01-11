from EconAgent.message import Message
from EconAgent.prompt.chat_prompt import chat_prompt_default,chat_prompt_registry

from EconAgent.prompt.chat_prompt.base_chat_prompt import BaseChatPromptTemplate
from langchain.schema import HumanMessage

# Set up a prompt template
@chat_prompt_registry.register("group_discuss_oldver")
class oldver_GroupDiscussPromptTemplate(BaseChatPromptTemplate):
    
    def __init__(self,**kwargs):
        template = kwargs.pop("template",
                             chat_prompt_default.get("group_discuss_template",""))

        input_variables = kwargs.pop("input_variables",
                    ["role_description", 
                     "friends",
                     "memory",
                     "agent_scratchpad",
                     "tenant_name"])
        super().__init__(template=template,
                         input_variables=input_variables,
                         **kwargs)
    
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
            
        formatted = self.template.format(**kwargs)
    
        # return [Message(content=formatted,
        #                 message_type=message_type)]
        return [HumanMessage(content=formatted)]
    
    
@chat_prompt_registry.register("group_discuss_oldver_back")
class oldver_GroupDiscussBackPromptTemplate(BaseChatPromptTemplate):
    
    def __init__(self,**kwargs):
        template = kwargs.pop("template",
                             chat_prompt_default.get("group_discuss_back_template",""))

        input_variables = kwargs.pop("input_variables",
                    ["role_description", 
                     "memory",
                     "message_sender",
                     "context",
                     "message_content",
                     "goal",
                     "message_sender2"])
        super().__init__(template=template,
                         input_variables=input_variables,
                         **kwargs)
    
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
            
        formatted = self.template.format(**kwargs)
    
        # return [Message(content=formatted,
        #                 message_type=message_type)]
        return [HumanMessage(content=formatted)]