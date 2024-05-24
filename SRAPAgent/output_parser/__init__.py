from SARPAgent.registry import Registry

output_parser_registry = Registry(name="OutputParserRegistry")

class OutputParseError(BaseException):
    """Exception raised when parsing output from a command fails."""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "Failed to parse output of the model:%s\n " % self.message

from .choose import ChooseParser
from .forum import ForumParser
from .publish import PublishParser
from .comment import CommentParser
from .action_plan import ActionPlanParser
from .group_discuss_oldver import Oldver_GroupDiscussParser
from .group_discuss import (GroupDiscussPlanParser,
                            GroupDiscussParser,
                            GroupDiscussBackParser,
                            RelationParser)
from .rating import ChooseRatingParser