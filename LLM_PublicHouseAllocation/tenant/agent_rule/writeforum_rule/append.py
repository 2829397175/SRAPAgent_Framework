
from . import writeforum_registry as WriteForumRgistry
from .base import Base_WriteForum


# 在原论坛的内容上，直接添加信息
@WriteForumRgistry.register("append")
class Append_WriteForum(Base_WriteForum):
    
    
    def write_forum(self,
                   forum_manager,
                   tenant_id,
                   tenant_name,
                   community_name:str=None,
                   community_id:str=None,
                   info_post=""):
        
        forum = forum_manager.data
        
        if community_name in forum.keys():
            if tenant_name in forum[community_name].keys():
                forum[community_name][tenant_id].append(info_post) 
            else:
                forum[community_name][tenant_id]=[info_post] 
        else:
            forum[community_name]={
                tenant_id: [info_post]
            } 
            
        return "tenant {tenant_id} {tenant_name} successfully publish information, for blog {community}:{info_post}".format(info_post=info_post,
                                                                                                         tenant_name=tenant_name,
                                                                                                         tenant_id=tenant_id,
                                                                                                         community=community_name)
