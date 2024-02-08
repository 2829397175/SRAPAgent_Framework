from typing import Dict
from SARPAgent.registry import Registry
env_registry = Registry(name="EnvironmentRegistry")
from .base import BaseEnvironment
from .rent import RentEnvironment