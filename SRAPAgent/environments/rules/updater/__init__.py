from SARPAgent.registry import Registry
updater_registry = Registry(name="UpdaterRegistry")

from .base import BaseUpdater
from .rent import RentUpdater