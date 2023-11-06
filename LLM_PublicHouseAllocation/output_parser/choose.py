from __future__ import annotations

import re
from typing import Union

from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish

from . import OutputParseError, output_parser_registry


@output_parser_registry.register("choose")
class ChooseParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        
        # # Parse out thought
        # regexs=[r"Thought\s*\d*\s*:(.*?)\nAction",
        #         r"(.*?)\nAction\s*\d*\s*Input",
        #         r"(.*?)\nFinal Answer:"]
        
        # for regex in regexs:
        #     match_thought = re.search(regex, llm_output, re.DOTALL)
        #     if match_thought:
        #         break
            
        # if not match_thought:
        #     thought =""
        # else:
        #     thought = match_thought.group(1).strip()
        
        
        
        # Parse out the action and action input
        regex = r"Thought\s*\d*\s*:(.*?)Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*?)\n"
        llm_output +="\n"
        
        match = re.search(regex, llm_output, re.DOTALL|re.IGNORECASE)
        
        
        if not match:
            raise OutputParseError("Output Format Error(choose)")
        
        # chooses = []
        # for match in matchs:
        #     thought = match[0].strip().strip(" ").strip('"')
        #     action = match[1].strip()
        #     action_input = match[2].strip().strip(" ").strip('"')
        #     chooses.append({"output":action_input,
        #                     "thought":thought})
            
        #     if action.lower() == "choose":
        #         return AgentFinish(return_values={"return_values":
        #                                         {"chooses":chooses}},
        #                        log=llm_output)
        
        
        thought = match.group(1).strip().strip(" ").strip('"')
        action = match.group(2).strip()
        action_input = match.group(3).strip().strip(" ").strip('"')

        
        if action.lower() == "choose":
            return AgentFinish(return_values={"return_values":
                                            {"output":action_input,
                                                "thought":thought}},
                            log=llm_output)
        
        # Return the action and action input
        raise OutputParseError("Output Format Error(choose)")