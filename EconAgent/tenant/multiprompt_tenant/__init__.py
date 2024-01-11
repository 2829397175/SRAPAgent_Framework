from EconAgent.registry import Registry
multiprompt_tenant_registry = Registry(name="MultiPromptTenantRegistry")
from EconAgent.tenant.multiprompt_tenant.CAHT_tenant import CAHTTenant
from EconAgent.tenant.multiprompt_tenant.base import BaseMultiPromptTenant