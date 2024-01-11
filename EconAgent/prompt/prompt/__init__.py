import yaml
prompt_default = yaml.safe_load(open("EconAgent/prompt/prompt/prompt.yaml"))

from EconAgent.registry import Registry
prompt_registry = Registry(name="PromptRegistry")
from EconAgent.prompt.prompt.base_prompt import BasePromptTemplate
from EconAgent.prompt.prompt.choose_house import Choose_HousePromptTemplate
from EconAgent.prompt.prompt.choose_community import Choose_CommunityPromptTemplate
from EconAgent.prompt.prompt.comment import CommentPromptTemplate
from EconAgent.prompt.prompt.forum import Forum_PromptTemplate
from EconAgent.prompt.prompt.correct import Correct_Choose_House_PromptTemplate,Correct_Choose_Community_PromptTemplate