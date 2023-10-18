from pydantic import BaseModel
import os
import re

import random
from typing import List, Union
from langchain.llms import OpenAI
from LLM_PublicHouseAllocation.tools import ForumTool,PublishInput,SearchInput
from LLM_PublicHouseAllocation.manager import ForumManager

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY","")
#llm = OpenAI(openai_api_key=OPENAI_API_KEY, temperature=0)
llm = OpenAI(openai_api_key=OPENAI_API_KEY, temperature=0)
def search_forum(forummanager:ForumManager,search_infos:str):
    search_infos = search_infos.split(",")
    
    return_infos = []
    for search_info in search_infos:
        community_name= re.search("([0-9]+)",str(search_info),re.I | re.M)
        forum = forummanager.data
        if (community_name is not None ) :
            community_name = community_name.group(1)
            community_name = "community_{}".format(community_name)
        
        if community_name in forum.keys() \
            and search_info.strip().lower()==community_name:
            info = get_forum_community_info(forummanager,[community_name],num=5,num_tenant=1)
            return_infos.append(f"{info}")
            
        try:
            prompt="""
    You are searching for house information. The information
    you see is as follows:
    {community_info}

    - Now you need to focus on summarizing and describing this part of the content,
    which is the information about {search_info}

    - Give your reponse in the following format:      
    Output: (the information you get)


    - Now give your response:
    Output: 
    """
            prompt = prompt.format(community_info = get_forum_community_info(forummanager,
                                                                            [community_name],
                                                                            num=5,
                                                                            num_tenant=1),
                                search_info=search_info)
            
            response = access_llm(prompt=prompt)
            
            return_infos.append(f"{response}")
        except Exception as e:
            continue
    if (len(return_infos)==0):
        return "no useful information"
    else:
        return "".join(return_infos) 


def get_forum_community_info(forummanager:ForumManager,
                            community_names:List[str]= [],
                            num:int=5,
                            num_tenant:int=1):
    # community_names 限制返回的forum信息范围； None默认返回全部
    forum = forummanager.data
    
    # check key
    for name in community_names:
        if name not in forum.keys():
            community_names.remove(name)
    
    # 访问帖子名字不符合要求，默认返回全部
    if len(community_names)==0:
        community_names = list(forum.keys())
    
    # num: 评论条数
    community_prompt = """
{community_name}:
{comments}
"""

    
    import random
    def get_comment(comment):
        comments = []
        if num < len(comment.keys()):
            tenant_names= random.sample(list(comment.keys()), num)
        else:
            tenant_names= list(comment.keys())
            
        for tenant_name in tenant_names:
            content = comment[tenant_name]
            content_sample = random.sample(content,num_tenant)
            content_sample_str = "".join(content_sample)
            comments.append("{tenant_name}:{content_sample}".format(
            tenant_name=tenant_name,
            content_sample=content_sample_str)
            )
        return "\n".join(comments)
    
    
    community_info = [community_prompt.format(community_name=community_name,
                                                comments=get_comment(forum[community_name])
                                            ) 
                        for community_name in community_names]
    community_info = "\n\n".join(community_info)
    return community_info


class Search_forum_topk():
    def __init__(self,forummanager:ForumManager) -> None:
        self.forummanager = forummanager
        
    # 不通过agent动作访问forum，直接topk返回
    # search_infos 暂时规定为各个community的index 
    def search_forum_topk(self,
                        search_infos:List[str]=None,
                        k_c=2,
                        k_u=2):
        forum = self.forummanager.data
        len_forum = len(forum)
        k_c = len_forum if k_c>len_forum else k_c
        if search_infos is None:
            search_infos = random.sample(list(forum.keys()),
                                        k_c)
        return_infos=[]
        for community_name in search_infos:
            if community_name in forum.keys() :
                info = get_forum_community_info(self.forummanager,[community_name],k_u,1)
                return_infos.append(f"{info}")
                
        return "".join(return_infos) 

def publish_forum(forummanager:ForumManager,information,tenant_name):
    """
except input: 
    information:"index,info"
    tenant_name:"name" 
"""
    information = information.split(",")
    community_index = information[0]
    community_infos = information[1:] if len(information)>=2 else ""
    infos = ",".join(community_infos)
    forum = forummanager.data
    try:
        choose_community_idx= re.search("([0-9]+)",str(community_index),re.I | re.M)        
        choose_community_idx = choose_community_idx.group(1)
        
        if f"community_{choose_community_idx}" in forum.keys():
            if tenant_name in forum[f"community_{choose_community_idx}"].keys():
                forum[f"community_{choose_community_idx}"][tenant_name].append(infos) 
            else:
                forum[f"community_{choose_community_idx}"][tenant_name]=[infos] 
        else:
            forum[f"community_{choose_community_idx}"]={
                tenant_name: [infos]
            } 
            
        return "{tenant} successfully publish information, for blog {community}:{infos}".format(infos=infos,
                                                                                            tenant=tenant_name,
                                                                                    community=choose_community_idx)
    except:
        if (infos !="") and (infos is not None):
            forum_tag = forum.get("extra_info",{})
            if tenant_name in forum_tag.keys():
                forum_tag[tenant_name].append(infos) 
            else:
                forum_tag[tenant_name]=[infos]
            forum["extra_info"] = forum_tag
            return "{tenant} successfully publish information, for blog {community}:{infos}".format(infos=infos,
                                                                                                tenant=tenant_name,
                                                                                       community="extra_info")
        else:
            return "Fail to update message."




def access_llm(prompt,max_retry = 5):
    response = None
    for i in range(max_retry):
        try:
            response = llm.generate([prompt],stop='\n\n')
            break
        except:
            print("Retrying...")
            continue
    if response is None:
        raise ValueError(f"failed to generate valid response.")
    
    return response.generations[0][0].text



class Tool(BaseModel):
    tools:list=[]
    
    def __init__(self,forummanager:ForumManager):
        tools=[
        # ForumTool(
        # name = "Search_forum",
        # func = search_forum,
        # description="Help you get information of house community.",
        # args_schema= SearchInput,
        # forummanager=forummanager
        # ),
        Search_forum_topk(forummanager = forummanager),
        ForumTool(
        name = "Publish_forum",
        func = publish_forum,
        description = "You can publish house information online if you want to. Input format: (community index), (information you want to post online)",
        args_schema = PublishInput,
        forummanager = forummanager
        ),
        ]
        super().__init__(tools=tools)
    
    # 测试用，暂时默认search_tool放在第一个
    def get_search_tool(self) -> Search_forum_topk:
        assert isinstance(self.tools[0],Search_forum_topk),"the search_tool is mis-placed"
        return self.tools[0]
    
    def get_tools(self)->List:
        return self.tools
    
    def get_publish_func(self):
        return publish_forum
    
    # 测试用，返回所有publish相关的tool
    def get_publish_tools(self) ->List[ForumTool]:
        return_tools=[]
        for tool in self.tools:
            if isinstance(tool,ForumTool):
                return_tools.append(tool)
        return return_tools
    