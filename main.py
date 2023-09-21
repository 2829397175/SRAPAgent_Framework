import os
os.environ["OPENAI_API_KEY"]= "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"
# os.environ["OPENAI_API_KEY"]= "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"
from LLM_PublicHouseAllocation.executor import Executor


executor = Executor.from_task('PHA_50tenant_3community_19house')
executor.run()