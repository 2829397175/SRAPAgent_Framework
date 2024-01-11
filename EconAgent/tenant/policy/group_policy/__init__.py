from EconAgent.registry import Registry

group_registry = Registry(name="TenantGroupPolicyRegistry")

from .base import BaseGroupPolicy
from .multi_list import MultiListPolicy
from .community import CommunityPolicy
from .house_type import HouseTypePolicy
from .single_list import SingleListPolicy
from .portion import PortionPolicy