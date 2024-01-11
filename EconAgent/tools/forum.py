
from . import tool_registry as ToolRegistry
from .base import BaseTool

from EconAgent.manager import ForumManager
from typing import Union, Dict, Any, Tuple
from pydantic import BaseModel, Field


class PublishInput(BaseModel):
    information: str = Field()
    tenant_name: str = Field()
    
class SearchInput(BaseModel):
    search_information: str = Field()

class ForumTool(BaseTool):
    forummanager:ForumManager
    
    def _parse_input(
        self,
        tool_input: Union[str, Dict],
    ) -> Union[str, Dict[str, Any]]:
        """Convert tool input to pydantic model."""
        input_args = self.args_schema
        if isinstance(tool_input, str):
            if input_args is not None:
                key_ = next(iter(input_args.__fields__.keys()))
                input_args.validate({key_: tool_input})
            return self.forummanager, tool_input
        else:
            if input_args is not None:
                result = input_args.parse_obj(tool_input)
                return self.forummanager, {k: v for k, v in result.dict().items() if k in tool_input}
            
        return self.forummanager,tool_input
    
    def _to_args_and_kwargs(self, tool_input: Union[Tuple,str, Dict]) -> Tuple[Tuple, Dict]:
        # For backwards compatibility, if run_input is a string,
        # pass as a positional argument.
        args=[]
        kargs={}
        for input in tool_input:
            if isinstance(input,dict):
                kargs.update(input)
            else:
                args.append(input)
                
        return tuple(args),kargs