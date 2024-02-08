from SARPAgent.registry import Registry
manager_registry = Registry(name="ManagerRegistry")


from .base import BaseManager
from .community import CommunityManager
from .house import HouseManager
from .tenant import TenantManager
from .forum import ForumManager