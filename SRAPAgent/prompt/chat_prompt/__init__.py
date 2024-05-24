import yaml
chat_prompt_default = yaml.safe_load(open("SARPAgent/prompt/chat_prompt/chat_prompt.yaml"))
example_default = yaml.safe_load(open("SARPAgent/prompt/chat_prompt/example.yaml"))


from SARPAgent.registry import Registry
chat_prompt_registry = Registry(name="ChatPromptRegistry")

from .choose import ChoosePromptTemplate
from .forum import ForumPromptTemplate
from .publish import PublishPromptTemplate
from .comment import CommentPromptTemplate
from .action_plan import ActionPlanPromptTemplate
from .group_discuss_oldver import oldver_GroupDiscussBackPromptTemplate,oldver_GroupDiscussPromptTemplate
from .group_discuss import (GroupDiscussPlanPromptTemplate,
                            GroupDiscussPromptTemplate,
                            GroupDiscussBackPromptTemplate,
                            RelationPromptTemplate)
from .rating import ChooseRatingPromptTemplate