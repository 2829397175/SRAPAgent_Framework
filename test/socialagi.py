from langchain.chat_models import ChatOpenAI
from langchain import SerpAPIWrapper, LLMChain
OPENAI_API_KEY = "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"

from langchain.llms import OpenAI

llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY)
