import os
os.environ["OPENAI_API_KEY"]= "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"
from LLM_PublicHouseAllocation.executor import Executor


executor = Executor.from_task('PHA_50tenant_3community_19house')
executor.run()