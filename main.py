import os
os.environ["OPENAI_API_KEY"]= "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"
from LLM_PublicHouseAllocation.executor import Executor


executor = Executor.from_task('PHA_50tenant_3community_19house')
executor.run()