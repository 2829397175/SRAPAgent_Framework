from __future__ import annotations

import re
from typing import Union

from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish

from . import OutputParseError, output_parser_registry


@output_parser_registry.register("action_plan")
class ActionPlanParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        
        # Parse out thought
        regexs=[r"Thought\s*\d*\s*:(.*?)\nAction",
                r"(.*?)\nAction\s*\d*\s*Input",
                r"(.*?)\nFinal Answer:"]
        
        for regex in regexs:
            match_thought = re.search(regex, llm_output, re.DOTALL)
            if match_thought:
                break
            
        if not match_thought:
            thought =""
        else:
            thought = match_thought.group(1).strip()
        
        regex = r"Action\s*\d*\s*:(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        
        return AgentFinish(return_values={"return_values":{"output":action,"thought":thought}},
                           log=llm_output)
        