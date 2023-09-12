from __future__ import annotations

import re
from typing import Union

from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish

from . import OutputParseError, output_parser_registry


@output_parser_registry.register("forum")
class ForumParser(AgentOutputParser):
    tenant_name : str
    max_action_per_round :int = 5 # 无论是发布信息还是
    action_times : int = 0
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        self.action_times +=1
        
        # Parse out thought
        
        regexs=[r"\s*\d*\s*Thought\s*\d*\s*:(.*?)\nAction",
                r"(.*?)\nAction",
                r"(.*?)\nFinal Answer:"]
        
        for regex in regexs:
            match_thought = re.search(regex, llm_output, re.DOTALL)
            if match_thought:
                break
            
        if not match_thought:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
            
        thought = match_thought.group(1).strip()
        
        
        if "Final Answer:" in llm_output:
            self.action_times = 0
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"return_values":
                                {"output": llm_output.split("Final Answer:")[-1].strip(),
                               "thought": thought.strip(" ").strip('"')}},
                log=llm_output,
            )
            
        # Parse out the action and action input
        regex = r"\s*\d*\s*Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)   
            
        if self.action_times > self.max_action_per_round:
            self.action_times = 0
            output = "I exceed the limit of action time. So I fail to obtain house information."
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"return_values":{"output":output,
                             "thought":thought.strip(" ").strip('"')}},
                log=llm_output,
            )
        
        if action == "Search_forum":
            return AgentAction(tool=action, 
                               tool_input=action_input.strip(" ").strip('"'), 
                               log=llm_output)
            
        elif action == "Publish_forum":
            tool_input = {
                "information":action_input.strip(" ").strip('"'), 
                "tenant_name":self.tenant_name
            }
            return AgentAction(tool=action, 
                           tool_input=tool_input, 
                           log=llm_output)
