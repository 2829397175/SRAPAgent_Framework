from pydantic import BaseModel
from EconAgent.tenant.multiprompt_tenant import multiprompt_tenant_registry as MultiPromptTenantRegistry
from EconAgent.tenant.agent_rule import AgentRule

@MultiPromptTenantRegistry.register("base")
class BaseMultiPromptTenant(BaseModel):
    agentrule:AgentRule
    # def __init__(self, rule, **kwargs):
    #     rule_config = rule
    #     readhouse_config = rule_config.get('readhouse_rule','topk')
    #     readforum_config = rule_config.get('readforum_rule','topk')
    #
    #     rule = AgentRule(readhouse_config,readforum_config)
    #     super().__init__(agentrule=rule, **kwargs)
