from pydantic import BaseModel
from abc import abstractmethod
from . import writeforum_registry as WriteForumRgistry

@WriteForumRgistry.register("base")
class Base_WriteForum(BaseModel):
    @abstractmethod
    def write_forum(self,
                   forum_manager,
                   **kwargs):
        pass