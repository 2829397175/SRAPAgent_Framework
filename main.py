import os
os.environ["OPENAI_API_KEY"]= "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"
from LLM_PublicHouseAllocation.executor import Executor


executor = Executor.from_task('PHA_50tenant_3community_19house')
executor.run()