from LLM_PublicHouseAllocation.memory import SummaryMemory,ActionHistoryMemory
from typing import Dict
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI

def load_memory(memory_config: Dict):
    memory_config_temp = memory_config.copy()
    memory_type = memory_config_temp.pop("memory_type", "action_history")
    if memory_type == "action_history":
        llm = load_llm(memory_config_temp.pop('llm',{'llm_type': 'text-davinci-003'}))
        return ActionHistoryMemory(llm=llm,**memory_config_temp)
    else:
        raise NotImplementedError("Memory type {} not implemented".format(memory_type))


def load_llm(llm_config: Dict):
    llm_type = llm_config.pop('llm_type', 'text-davinci-003')
    if llm_type == 'gpt-3.5-turbo':
        return ChatOpenAI(**llm_config)
    elif llm_type == 'text-davinci-003':
        return OpenAI(**llm_config)
    else:
        raise NotImplementedError("LLM type {} not implemented".format(llm_type))