from LLM_PublicHouseAllocation.message import Message
from LLM_PublicHouseAllocation.prompt.chat_prompt import chat_prompt_default,chat_prompt_registry

from LLM_PublicHouseAllocation.prompt.chat_prompt.base_chat_prompt import BaseChatPromptTemplate
from langchain.schema import HumanMessage

# Set up a prompt template
@chat_prompt_registry.register("group_discuss_plan")
class GroupDiscussPlanPromptTemplate(BaseChatPromptTemplate):
    
    def __init__(self,**kwargs):
        template = kwargs.pop("template",
                             chat_prompt_default.get("group_discuss_plan_template",""))

        input_variables = kwargs.pop("input_variables",
                    ["concise_role_description", 
                     "acquaintance_desciption",
                     "memory",
                     "system_competiveness_description",
                     "personality",
                     "agent_scratchpad",
                     "goal",
                     "respond_format"]) # 这里的goal暂时设定为固定
        super().__init__(template=template,
                         input_variables=input_variables,
                         **kwargs)
    
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
            
        formatted = self.template.format(**kwargs)
    

        return [HumanMessage(content=formatted)]
    
    
@chat_prompt_registry.register("group_discuss")
class GroupDiscussPromptTemplate(BaseChatPromptTemplate):
    
    def __init__(self,**kwargs):
        template = kwargs.pop("template",
                             chat_prompt_default.get("group_discuss_template",""))

        input_variables = kwargs.pop("input_variables",
                    ["concise_role_description",
                     "plan",
                     "acquaintances",
                     "acquaintance_num",
                     "agent_scratchpad",
                     "memory"])
        
        super().__init__(template=template,
                         input_variables=input_variables,
                         **kwargs)
    
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
            
        formatted = self.template.format(**kwargs)
    

        return [HumanMessage(content=formatted)]
    
@chat_prompt_registry.register("group_discuss_back")
class GroupDiscussBackPromptTemplate(BaseChatPromptTemplate):
    
    def __init__(self,**kwargs):
        template = kwargs.pop("template",
                             chat_prompt_default.get("group_discuss_back_template",""))

        input_variables = kwargs.pop("input_variables",
                    ["concise_role_description", 
                     "plan",
                     "acquaintance_communication",
                     "acquaintance_name",
                     "agent_scratchpad",
                     "memory"])
        super().__init__(template=template,
                         input_variables=input_variables,
                         **kwargs)
    
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
            
        formatted = self.template.format(**kwargs)
    

        return [HumanMessage(content=formatted)]
    
    
@chat_prompt_registry.register("relation")
class RelationPromptTemplate(BaseChatPromptTemplate):
    
    def __init__(self,**kwargs):
        template = kwargs.pop("template",
                             chat_prompt_default.get("relation_template",""))

        input_variables = kwargs.pop("input_variables",
                    ["acquaintance_name", 
                     "role_description",
                     "memory",
                     "relation",
                     "communication",
                     "agent_scratchpad",])
        super().__init__(template=template,
                         input_variables=input_variables,
                         **kwargs)
    
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
            
        formatted = self.template.format(**kwargs)
    

        return [HumanMessage(content=formatted)]
    
    
    