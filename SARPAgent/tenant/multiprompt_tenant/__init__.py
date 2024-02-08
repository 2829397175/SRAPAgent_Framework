from SARPAgent.registry import Registry
multiprompt_tenant_registry = Registry(name="MultiPromptTenantRegistry")
from SARPAgent.tenant.multiprompt_tenant.CAHT_tenant import CAHTTenant
from SARPAgent.tenant.multiprompt_tenant.base import BaseMultiPromptTenant