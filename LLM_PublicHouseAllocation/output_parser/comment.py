from __future__ import annotations

import re
from typing import Union

from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish

from . import OutputParseError, output_parser_registry


@output_parser_registry.register("comment")
class CommentParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        

        
        # Parse out the action and action input
        regex = r"Thought\s*\d*\s*:(.*?)\nAction\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        llm_output +="\n"
        
        matchs = re.findall(regex, llm_output, re.DOTALL)
        
        if not matchs:
            raise OutputParseError("Output Format Error")

        comments = []
        for match in matchs:
            thought = match[0].strip(" ").strip('"')
            action = match[1].strip()
            action_input = match[2].strip(" ").strip('"')
            comments.append({"thought":thought,
                             "action":action,
                             "action_input":action_input})
            
            if action.lower() == "comment":
                return AgentFinish(return_values={"return_values":
                                                {"comments":comments}},
                               log=llm_output)
          
        
        # Return the action and action input
        raise OutputParseError("Output Format Error")
