from typing import Dict

from EconAgent.registry import Registry
visibility_registry = Registry(name="VisibilityRegistry")

from .base import BaseVisibility
from .rent import RentVisibility
