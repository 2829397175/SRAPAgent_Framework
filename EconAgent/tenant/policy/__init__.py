from EconAgent.registry import Registry

policy_registry = Registry(name="ChoosePolicyRegistry")

from .base import BasePolicy
from .ver1policy import Ver1Policy
from .ver2policy import Ver2Policy
from .ver3policy import Ver3Policy