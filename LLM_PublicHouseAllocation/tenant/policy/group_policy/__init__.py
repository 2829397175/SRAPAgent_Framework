from LLM_PublicHouseAllocation.registry import Registry

group_registry = Registry(name="GroupPolicyRegistry")

from .base import BaseGroupPolicy
from .multi_list import MultiListPolicy
from .community import CommunityPolicy
from .house_type import HouseTypePolicy
from .single_list import SingleListPolicy