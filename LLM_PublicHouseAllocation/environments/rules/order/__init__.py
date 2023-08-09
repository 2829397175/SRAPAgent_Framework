from LLM_PublicHouseAllocation.registry import Registry
order_registry = Registry(name="OrderRegistry")

from .base import BaseOrder
from .rent import RentOrder