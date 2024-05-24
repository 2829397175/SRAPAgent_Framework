import yaml
prompt_default = yaml.safe_load(open("SARPAgent/prompt/prompt/prompt.yaml"))

from SARPAgent.registry import Registry
prompt_registry = Registry(name="PromptRegistry")
from SARPAgent.prompt.prompt.base_prompt import BasePromptTemplate
from SARPAgent.prompt.prompt.choose_house import Choose_HousePromptTemplate
from SARPAgent.prompt.prompt.choose_community import Choose_CommunityPromptTemplate
from SARPAgent.prompt.prompt.comment import CommentPromptTemplate
from SARPAgent.prompt.prompt.forum import Forum_PromptTemplate
from SARPAgent.prompt.prompt.correct import Correct_Choose_House_PromptTemplate,Correct_Choose_Community_PromptTemplate