from LLM_PublicHouseAllocation.registry import Registry

house_patch_registry = Registry(name="HousePatchPolicyRegistry")

from .base import BaseHousePatchPolicy
