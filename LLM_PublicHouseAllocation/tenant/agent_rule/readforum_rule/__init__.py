from LLM_PublicHouseAllocation.registry import Registry
readforum_registry = Registry(name="ReadForumRgistry")
from .base import Base_ReadForum
from .topk import Topk_ReadForum
from .random_k import Randomk_ReadForum
