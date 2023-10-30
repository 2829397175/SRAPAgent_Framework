import os
import json
import numpy as np
from langchain.llms import OpenAI   
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
from pydantic import BaseModel
os.environ["OPENAI_API_KEY"]= "sk-YZyToq4keshPgAw8vUqtT3BlbkFJ1Zwdp6NdxzbtcksjMBw"

class Translate(BaseModel):
    data_path:str="LLM_PublicHouseAllocation/LLM_decision_test/data/unfinished_QA_result.json"
    save_path:str="LLM_PublicHouseAllocation/LLM_decision_test/data/Chinese_unfinished_QA_result.json"
    datas:list=[]
    
    def read_data(self):
        assert os.path.exists(self.data_path),"no such file path: {}".format(self.data_path)
        with open(self.data_path,'r',encoding = 'utf-8') as f:
            self.datas = json.load(f)
    


    def translate_to_chinese(self):
        llm = OpenAI(temperature=1)
        template="""
            {english_text}
            
            中文：
        """  
        input_variables=["english_text"]
        prompt = PromptTemplate(  
            input_variables=input_variables,  
            template=template,  
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        for data in self.datas:
            for value in data.values():
                if isinstance(value,dict):
                    for content in value.values():
                        input={"english_text":content}
                        response=chain.run(input)
                        content=response
                        print(content)


    def save_data(self):
        with open(self.save_path, 'w', encoding='utf-8') as file:
            json.dump(self.datas, file, indent=4,separators=(',', ':'),ensure_ascii=False)

    
    def run(self):
        self.read_data()
        self.translate_to_chinese()
        self.save_data()
        
    

if __name__ == "__main__":
    translator=Translate()
    translator.run()