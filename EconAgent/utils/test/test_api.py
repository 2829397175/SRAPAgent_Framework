import openai
from langchain.llms import OpenAI   
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import asyncio
from langchain.chat_models import ChatOpenAI



async def test_chain(apis):
    template="""
        Transfer the following context into Simplified Chinese:
        {english_text}
        
        Here's your translation:
    """  
    
    english_text = "hello"
    for api in apis:
        # llm = OpenAI(model_name = "text-davinci-003",
        #                 verbose = False,
        #                 temperature = 0.8,
        #                 openai_api_base=api_base,
        #                 openai_api_key= api)
        
        llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k-0613",
                       verbose = False,
                       max_tokens = 500,
                       openai_api_key=api
                       )  
        input_variables=["english_text"]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        chinese_text = await chain.arun(english_text=english_text)
        print(chinese_text.strip())
    
def test_api(api):
    openai.api_key = api
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo-16k-0613",
    messages=[
        {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
        {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
    
    ]
    )

    print(completion.choices[0].message,api)
        

    

