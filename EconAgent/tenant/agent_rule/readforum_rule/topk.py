
from . import readforum_registry as ReadForumRgistry
from .base import Base_ReadForum


@ReadForumRgistry.register("topk")
class Topk_ReadForum(Base_ReadForum):

    
    def read_forum(self ,
                   forumdata ,
                   community_name ,
                   k=5):
        if community_name not in forumdata or len(list(forumdata[community_name].values()) )==0 :
            return "There are currently no comments on this forum."
        if k > len(list(forumdata[community_name].values())):
            comments  =[" ".join(line) for line in list(forumdata[community_name].values())[:]]
            return  "\n".join(comments)
        else:
            comments = [" ".join(line) for line in list(forumdata[community_name].values())[-k:]]
            return  "\n".join(comments)