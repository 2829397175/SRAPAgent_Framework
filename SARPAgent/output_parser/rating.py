from __future__ import annotations

import re
from typing import Union

from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish

from . import OutputParseError, output_parser_registry


@output_parser_registry.register("choose_rating")
class ChooseRatingParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        
        # Parse out the action and action input
        regex = r"Rating\s*\d*\s*:(.*?)Reason\s*\d*\s*:(.*)\n"
        llm_output +="\n"
        
        match = re.search(regex,llm_output,re.I|re.S)
        
        
        if not match:
            raise OutputParseError("Output Format Error")
        
        try:
            rating = match.group(1).strip()
            reason = match.group(2).strip()

            rating = rating.split("\n")
            rating =  [rating_one.split(":") for rating_one in rating]

            for rating_one in rating:
                rating_one[1] = re.search("([0-9]+)",str(rating_one[1]),re.I | re.M).groups()[0]
                rating_one[1] = int(rating_one[1])

            return AgentFinish(return_values={"return_values":
                                            {"rating":rating,
                                                "thought":reason}},
                            log=llm_output)
            
        except Exception as e:
            # Return the action and action input
            raise OutputParseError("Output Format Error")