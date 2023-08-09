from __future__ import annotations

import re
from typing import Union

from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish

from . import OutputParseError, output_parser_registry


@output_parser_registry.register("group_discuss")
class GroupDiscussParser(AgentOutputParser):
    
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

        regex = r"Action\s*\d*\s*:(.*?)\nFriends\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            return AgentFinish(return_values={"output":"fail to discuss",
                                            "thought":thought},log=llm_output)

        try:
            action = match.group(1).strip()
            receivers = match.group(2).strip()
            action_input = match.group(3)
            assert action.lower()=="groupdiscuss"
            return AgentFinish(return_values={"output":action_input,
                                            "thought":thought,
                                            "receivers":receivers,
                                            },log=llm_output)
        except:
            return AgentFinish(return_values={"output":"fail to discuss",
                                            "thought":thought},log=llm_output)