from typing import Dict

from LLM_PublicHouseAllocation.registry import Registry
visibility_registry = Registry(name="VisibilityRegistry")

from .base import BaseVisibility
from .rent import RentVisibility
