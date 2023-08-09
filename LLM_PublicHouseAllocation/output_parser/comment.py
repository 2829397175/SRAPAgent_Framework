from __future__ import annotations

import re
from typing import Union

from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish

from . import OutputParseError, output_parser_registry


@output_parser_registry.register("comment")
class CommentParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        
        # Parse out thought
        regexs=[r"Thought\s*\d*\s*:(.*?)\nAction",
                r"(.*?)\nAction"]
        
        for regex in regexs:
            match_thought = re.search(regex, llm_output, re.DOTALL)
            if match_thought:
                break
            
        if not match_thought:
            thought= ""
        else:
            thought = match_thought.group(1).strip()
        
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": "I fail to make comments.",
                               "thought":""},
                log=llm_output,
            )
        output_results=list(match.groups())
        
        for idx in range(int(len(output_results)/2)):
            action = output_results[idx*2].strip()
            action_input = output_results[idx*2+1].strip()
            if action.lower() == "comment":
                return AgentFinish(return_values={"output":action_input.strip(" ").strip('"'),
                                                "thought":thought.strip(" ").strip('"')},
                               log=llm_output)
                
        if len(output_results)>0:
            action = output_results[0].strip()
            action_input = output_results[1].strip()
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": action_input.strip(" ").strip('"'),
                               "thought":thought.strip(" ").strip('"')},
                log=llm_output,
            )
        
        # Return the action and action input
        return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": "I fail to make comments.",
                               "thought":""},
                log=llm_output,
            )
