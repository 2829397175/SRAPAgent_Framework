from __future__ import annotations

from pydantic import BaseModel
from EconAgent.tenant.agent_rule.readhouse_rule import Base_ReadHouse,readhouse_registry
from EconAgent.tenant.agent_rule.readforum_rule import Base_ReadForum,readforum_registry
from EconAgent.tenant.agent_rule.readcommunity_rule import Base_ReadCommunity,readcommunity_registry
from EconAgent.tenant.agent_rule.writeforum_rule import Base_WriteForum,writeforum_registry


class AgentRule(BaseModel):
    """
    Rule for the environment. It controls the speaking order of the agents
    and maintain the set of visible agents for each agent.
    """
    read_house_rule: Base_ReadHouse
    read_forum_rule: Base_ReadForum
    read_community_rule: Base_ReadCommunity
    write_forum_rule: Base_WriteForum

    def __init__(self, 
                 read_house_config,
                 read_forum_config,
                 read_community_config,
                 write_forum_config):
        read_house_list = readhouse_registry.build(read_house_config)
        read_forum_list = readforum_registry.build(read_forum_config)
        read_community_list = readcommunity_registry.build(read_community_config)
        write_forum_list = writeforum_registry.build(write_forum_config)
        
        super().__init__(read_house_rule = read_house_list,
                         read_forum_rule = read_forum_list,
                         read_community_rule = read_community_list,
                         write_forum_rule = write_forum_list)

    def read_forum(self, forumdata , community_name):
        return self.read_forum_rule.read_forum(forumdata,community_name)

    def read_house_list(self, house_data, house_ids):
        return self.read_house_rule.read_house_list(house_data, house_ids)
    
    
    def get_houses_generator(self,
                           **kwargs):
        return self.read_house_rule.get_houses_generator(**kwargs)
    
    def read_community_list(self, community_data, community_ids=None):
        return self.read_community_rule.read_community_list(community_data,community_ids)
    
    def publish_forum(self,**kwargs):
        return self.write_forum_rule.write_forum(**kwargs)