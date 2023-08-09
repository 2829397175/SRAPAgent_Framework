from LLM_PublicHouseAllocation.registry import Registry
writeforum_registry = Registry(name="WriteForumRgistry")
from .base import Base_WriteForum
from .append import Append_WriteForum
