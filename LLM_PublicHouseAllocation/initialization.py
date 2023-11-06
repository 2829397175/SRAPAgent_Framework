import os
from typing import Dict

import yaml

from langchain.memory.prompt import _DEFAULT_SUMMARIZER_TEMPLATE
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.memory import ChatMessageHistory
from LLM_PublicHouseAllocation.prompt.prompt import prompt_registry
from LLM_PublicHouseAllocation.manager import manager_registry
from LLM_PublicHouseAllocation.environments import env_registry
from LLM_PublicHouseAllocation.memory import SummaryMemory,ActionHistoryMemory
from LLM_PublicHouseAllocation.tenant.agent_rule import AgentRule
import copy


from LLM_PublicHouseAllocation.memory import SummaryMemory,ActionHistoryMemory

def load_memory(memory_config: Dict,
                llm):
    memory_config_temp = copy.deepcopy(memory_config)
    memory_type = memory_config_temp.pop("memory_type", "action_history")
    if memory_type == "action_history":
        return ActionHistoryMemory(llm=llm,**memory_config_temp)
    else:
        raise NotImplementedError("Memory type {} not implemented".format(memory_type))


def load_environment(env_config: Dict) :
    env_type = env_config.pop('env_type', 'rent')
    return env_registry.build(env_type, **env_config)



def load_manager(manager_config: Dict,manager_type) :
    return manager_registry.load_data(manager_type, ** manager_config)
    

    
def prepare_task_config(task):
    """Read the yaml config of the given task in `tasks` directory."""
    all_task_dir = os.path.join(os.path.dirname(__file__), 'tasks')
    task_path = os.path.join(all_task_dir, task)
    config_path = os.path.join(task_path, 'config.yaml')
    
    if not os.path.exists(task_path):
        all_tasks = []
        for task in os.listdir(all_task_dir):
            if os.path.isdir(os.path.join(all_task_dir, task)) \
                and task != "__pycache__":
                all_tasks.append(task)
        raise ValueError(f"Task {task} not found. Available tasks: {all_tasks}")
    if not os.path.exists(config_path):
        raise ValueError("You should include the config.yaml file in the task directory")
    task_config = yaml.safe_load(open(config_path))

    return task_config,task_path





def load_llm(**llm_config):
    llm_config_temp = copy.deepcopy(llm_config)
    llm_type = llm_config_temp.pop('llm_type', 'text-davinci-003')
    if llm_type == 'gpt-3.5-turbo':
        return ChatOpenAI(model_name= "gpt-3.5-turbo",
                          **llm_config_temp)
    elif llm_type == 'text-davinci-003':
        return OpenAI(model_name="text-davinci-003",
                      **llm_config_temp)
    elif llm_type == 'gpt-3.5-turbo-16k-0613':
        return ChatOpenAI(model_name="gpt-3.5-turbo-16k-0613",
                      **llm_config_temp)        
    else:
        #return OpenAI(**llm_config)
        raise NotImplementedError("LLM type {} not implemented".format(llm_type))


def load_prompt(prompt_type: str) :
    config={}
    return prompt_registry.build(prompt_type, **config)

def load_agentrule(agentrule_config):
    readhouse_rule = agentrule_config.pop("readhouse_rule", "topk")
    readforum_rule = agentrule_config.pop("readforum_rule", "topk")
    readcommunity_rule = agentrule_config.pop("readcommunity_rule", "available")
    writeforum_rule = agentrule_config.pop("writeforum_rule", "append")
    return AgentRule(readhouse_rule,readforum_rule,readcommunity_rule,writeforum_rule)

