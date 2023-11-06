
from . import readforum_registry as ReadForumRgistry
from .base import Base_ReadForum
import random

@ReadForumRgistry.register("randomk")
class Randomk_ReadForum(Base_ReadForum):
    def get_tenant_comment(self,
                           comments_tenant:list[str],
                           tenant_name:str,
                           k_tenant = 2,
                           ):
        comments = []
        if (k_tenant)<len(comments):
            content_sample = random.sample(comments_tenant,k_tenant)
        else:
            content_sample = comments_tenant
        content_sample_str = "".join(content_sample)
        comments.append("{tenant_name} said :{content_sample}.".format(
        tenant_name=tenant_name,
        content_sample=content_sample_str)
        )
        return "\n".join(comments)
    
    def get_community_comment(self,
                              comments_community,
                              k_community = 3,
                              k_tenant = 2):
        comments = []
        if k_community < len(comments_community.keys()):
            tenant_names= random.sample(list(comments_community.keys()), k_community)
        else:
            tenant_names= list(comments_community.keys())
            
        
        for tenant_name in tenant_names:
            comments_tenant = comments_community[tenant_name]
            comments.append(self.get_tenant_comment(comments_tenant=comments_tenant,
                                                    tenant_name=tenant_name,
                                                    k_tenant=k_tenant))
        return "\n".join(comments)
        
    def read_forum(self ,
                   forumdata ,
                   community_name ,
                   k_c=3,
                   k_t=2):
        if community_name not in forumdata or len(list(forumdata[community_name].values()) )==0 :
            return "There are currently no comments on this forum."
        
        comments_one_cm = self.get_community_comment(forumdata[community_name],
                                          k_community=k_c,
                                          k_tenant=k_t)
        template_one_cm ="The following are the information posted by different tenants on the forum:{comments}"
        
        return template_one_cm.format(comments = comments_one_cm)