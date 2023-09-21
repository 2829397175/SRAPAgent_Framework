from __future__ import annotations

import re
from typing import Union

from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish

from . import OutputParseError, output_parser_registry


@output_parser_registry.register("group_discuss_plan")
class GroupDiscussPlanParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # outputs = llm_output.split("\n")
        # return_values = {}
        # try:
        #     true_opinion = outputs[0]
        #     decision_honesty = outputs[1]
        #     plan = outputs[2]
        #     return_values = {"true_opinion":true_opinion,
        #                      "decision_honesty":decision_honesty,
        #                      "plan":plan,
        #                      }
        # except Exception as e:
        #     return_values = {}
        return AgentFinish(return_values={"return_values":{"plan":llm_output}},log=llm_output)
    
    
    
@output_parser_registry.register("group_discuss")
class GroupDiscussParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        
        llm_output +="\n"
        # Parse out thought
        regexs=[r"Thought\s*\d*\s*:(.*?)\n"]
        
        for regex in regexs:
            match_thought = re.findall(regex, llm_output, re.DOTALL)
            if match_thought:
                break
        
        regex = r"Acquaintance.*?:(.*?)\nOutput.*?:(.*?)\n"
        
        
        matchs = re.findall(regex, llm_output, re.DOTALL)
        
        
        try:
            return_values={"communication":[]} # 返回一个和各个熟人的交流结果
            idx_thought = 0 
          
            for idx,match in enumerate(matchs):
                thought = match_thought[idx_thought][0] if idx_thought < len(match_thought) else ""  
                communication={
                        "thought":thought.strip(),
                        "acquaintance_names":match[0].strip(),
                        "output":match[1].strip(),
                    }
                return_values["communication"].append(communication)
                idx_thought = idx_thought+1 if (idx_thought+1)< len(match_thought) else idx_thought
                    
            return AgentFinish(return_values={"return_values":return_values},
                                    log=llm_output)
        except Exception as e:
            raise OutputParseError("Output Format Error")
    
    
    
@output_parser_registry.register("group_discuss_back")
class GroupDiscussBackParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        try:
            outputs = llm_output.strip().split("\n")
            if (len(outputs) == 1):
                output = llm_output
                output = re.sub('\\(.*?\\)','',output) # 删除括号及括号内内容
                output = re.sub('Words to say to .*?:','',output,flags=re.IGNORECASE)
                return AgentFinish(return_values={"return_values":{"continue_dialogue":True,
                                                               "output":output}},
                                   log =llm_output)
            try:
                continue_dialogue = outputs[0].split(":")[-1].strip().lower()
            except:
                continue_dialogue = outputs[0].strip().lower() # 无法parse的情况，都视为continue
                
            if continue_dialogue == "true" or "t" in continue_dialogue:
                continue_dialogue = True
            elif continue_dialogue == "false" or "f" in continue_dialogue:
                continue_dialogue = False
            else:
                continue_dialogue = True # 如果无法parse，默认继续对话
                
            output = "".join(outputs[1:]).strip()
            output = re.sub('\\(.*?\\)','',output) # 删除括号及括号内内容
            output = re.sub('Words to say to .*?:','',output,flags=re.IGNORECASE)
            
            return AgentFinish(return_values={"return_values":{"continue_dialogue":continue_dialogue,
                                                               "output":output}},
                            log=llm_output)
        except Exception as e:
             raise OutputParseError("Output Format Error")
        
        
@output_parser_registry.register("relation")
class RelationParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        
        try:
            outputs = llm_output.strip().split("\n")
            try:
                relation = outputs[0].split(":")[-1].strip()
            except:
                relation = outputs[0].strip()
                
            comment = outputs[1].strip()
            
            return AgentFinish(return_values={"return_values":{"relation":relation,
                                                            "comment":comment}},
                            log=llm_output)
        except Exception as e:
            raise OutputParseError("Output Format Error")
        
        
        