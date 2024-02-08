from pydantic import BaseModel
from abc import abstractmethod
from . import readforum_registry as ReadForumRgistry

@ReadForumRgistry.register("base")
class Base_ReadForum(BaseModel):
    @abstractmethod
    def read_forum(self,forumdata:dict ,community_name:str):
        pass