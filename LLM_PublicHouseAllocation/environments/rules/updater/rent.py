from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple, Dict

from langchain.schema import AgentAction
from pydantic import BaseModel


from LLM_PublicHouseAllocation.message import Message

from . import updater_registry as UpdaterRegistry

from .base import BaseUpdater


@UpdaterRegistry.register("rent")
class RentUpdater(BaseUpdater):
    """
    The basic version of updater.
    The messages will be seen by all the receiver specified in the message.
    """
    def post_messages(self, 
                      post_messages:List[Message],
                      tenant_manager):
        
        for message in post_messages:
            for r_id in message.receiver:
                if r_id in tenant_manager.data.keys():
                    tenant_manager.data[r_id].receive_messages(messages=[message])
            
                    
    def reset(self):
        pass