import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import json
from pydantic import BaseModel

class App:
    def __init__(self, 
                 dir_path, 
                 saving_path,
                 ):
        self.dataloader = DataLoader(root_dir = dir_path)
        self.saving_path = saving_path
        self.datas:dict = {} # 这一轮的constant data (仅仅存一轮实验的)
        self.mems:dict = {} # 这一轮的mems (仅仅存一轮实验的)
        self.mem_data_buffer:dict = {} # 按print之后，需要等待进行print的mem index
        self.context_generator = None # 这是每次生成context的generator
        self.dialogue:dict = None # 对于dataloader生成dialogue的引用
        
        self.create_window()
        
    def create_frame_window(self):
        """create_frame_window
        for window
        """
        row_counter = 0
        
        col_frame = tk.Frame(self.window)
        col_frame.grid(row=0,column=1,sticky="nesw")
        scrollbar = tk.Scrollbar(col_frame)    # 
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)       
            
        self.prompt_frames = []
        
        # Dynamic creation of labels and text widgets based on keys of self.datas
        for idx,key in enumerate(self.datas.keys()):
            frame = tk.Frame(self.window)
            frame.grid(row=row_counter, column=0, sticky="nsew", padx=20, pady=5)
            
            label = tk.Label(frame, text=key)
            label.pack(side=tk.LEFT)

            text_widget = tk.Text(frame, wrap=tk.WORD,width=160,height = self.text_heights[idx])
            text_widget.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
            text_widget.configure(state=tk.DISABLED)  # Make it read-only
            
            # 创建滚动条
            scrollbar = tk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # 将文本小部件与滚动条关联
            text_widget.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=text_widget.yview)

            self.prompt_frames.append((label, text_widget))
            row_counter += 1

        
        # Buttons Frame
        button_frame = tk.Frame(self.window)
        button_frame.grid(row=row_counter, column=0, pady=10)
        
        self.approve_button = tk.Button(button_frame, text="Approve (Human Response)", command=self.approve)
        self.approve_button.pack(side=tk.LEFT, padx=10)
        
        self.reject_button = tk.Button(button_frame, text="Reject (Robot Response)", command=self.reject)
        self.reject_button.pack(side=tk.LEFT, padx=10)
        
        # self.save_button = tk.Button(button_frame, text="Save Response", command=self.save_response)
        # self.save_button.pack(side=tk.LEFT, padx=10)

        for i in range(row_counter):
            self.window.grid_rowconfigure(i, weight=1)
        self.window.grid_columnconfigure(0, weight=9)
        self.window.grid_columnconfigure(1, weight=1)
        
        
    
    
    def show_mem_data_buffer(self):
        try:
            mem_key,mem_info = self.mem_data_buffer.popitem()
            filter_keys = ["prompt_inputs",
                            "response"]
            mem_info = {k:mem_info[k] for k in filter_keys}
            if len(mem_info) > len(self.mem_info_prompt_frames):
                self.create_mem_info_window(mem_infos = mem_info)
                
            # for mem_key,mem_info in mem_dicts.items():
            self.show_mem_info_context_info(mems=mem_info)
        except:
            return
    
    
    def show_mem_info(self):
        index = self.mem_list_box.curselection()
        self.mem_data_buffer = {}
        
        for idx in index:
            index_mem = self.mem_list_box.get(idx)
            mem_dicts = self.mems.get(index_mem,"")
            self.mem_data_buffer.update(mem_dicts)
            
            self.show_mem_data_buffer()
            
            
            
    def append_frame_mem_window(self,mem_append):
        for mem_key,mem_info in mem_append.items():
            self.mem_list_box.insert(tk.END,mem_key)
            
        
    
    def create_frame_mem_window(self):
        """create_frame_mem_window
        for mem_window
        """
        # row_counter = 0
        
        # col_frame = tk.Frame(self.mem_window)
        # col_frame.grid(row=0,column=1,sticky="nesw")
        # row_counter +=1
        scrollbar = tk.Scrollbar(self.mem_window)    # 
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)       
            
        # Buttons Frame
        # button_frame = tk.Frame(self.window)
        # button_frame.grid(row=row_counter, column=0, pady=10)
        
        self.mem_list_box = tk.Listbox(self.mem_window)
        self.mem_list_box.pack(padx=5, pady=5)
        self.mem_print_button = tk.Button(self.mem_window, text='print', command=self.show_mem_info)
        self.mem_print_button.pack()
        
        # for i in range(row_counter):
        #     self.mem_window.grid_rowconfigure(i, weight=1)
        self.mem_window.grid_columnconfigure(0, weight=9)
        self.mem_window.grid_columnconfigure(0, weight=1)
        
        
        
    def create_mem_info_window(self,mem_infos:dict):
        
        row_counter = 0
        
        col_frame = tk.Frame(self.mem_info_window)
        col_frame.grid(row=0,column=1,sticky="nesw")
        scrollbar = tk.Scrollbar(col_frame)    # 
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)       
            
            
        self.mem_info_prompt_frames = []
        text_heights = [1,1,2,2,2,2,2,2]
        # Dynamic creation of labels and text widgets based on keys of self.datas
        for idx,key in enumerate(mem_infos.keys()):
            frame = tk.Frame(self.mem_info_window)
            frame.grid(row=row_counter, column=0, sticky="nsew", padx=20, pady=5)
            
            label = tk.Label(frame, text=key)
            label.pack(side=tk.LEFT)

            text_widget = tk.Text(frame, wrap=tk.WORD,width=160,height = text_heights[idx])
            text_widget.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
            text_widget.configure(state=tk.DISABLED)  # Make it read-only
            
            # 创建滚动条
            scrollbar = tk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # 将文本小部件与滚动条关联
            text_widget.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=text_widget.yview)

            self.mem_info_prompt_frames.append((label, text_widget))
            row_counter += 1

         # Buttons Frame
        button_frame = tk.Frame(self.mem_info_window)
        button_frame.grid(row=row_counter, column=0, pady=10)
        
        self.continue_mem_button = tk.Button(button_frame, text="Continue", command=self.show_mem_data_buffer)
        self.continue_mem_button.pack(side=tk.LEFT, padx=10)
        
        
        
        for i in range(row_counter):
            self.mem_info_window.grid_rowconfigure(i, weight=1)
        self.mem_info_window.grid_columnconfigure(0, weight=9)
        self.mem_info_window.grid_columnconfigure(1, weight=1)
        
        
        
    def create_window(self):
        self.window = tk.Tk()
        self.window.title("Check Consistency")
        self.mem_window = tk.Toplevel(master=self.window)
        self.mem_window.title("Memory List")
        
        self.mem_info_window = tk.Toplevel(master=self.mem_window)
        self.mem_info_window.title("Memory Info")
        
         # 设定各个表格列的长度：[window内]
        self.text_heights=[1,1,1,10,10] 
        self.datas= {
            "general_description":"",
            "concise_role_description":"",
            "acquaintance_desciption":"",
            'context_info':"",
            "content_info":""
        }

        self.create_frame_window()

        self.create_frame_mem_window()

        self.create_mem_info_window(mem_infos={})
        
        
        
        # self.window.grid_columnconfigure(0, weight=1)
        self.show_data()
        self.window.protocol("WM_DELETE_WINDOW", self.save_and_exit)
        self.window.mainloop()
        self.mem_window.mainloop()
        self.mem_info_window.mainloop()
        


    def insert_and_resize_textbox(self,text_widget, content):
        """
        Insert content into the provided text widget and resize its height based on content's lines.
        """
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, content)
        
        # lines = content.split("\n")
        # line_count = len(lines) + 1  # adding an additional line for padding
        # text_widget.configure(height=line_count)

        text_widget.configure(state=tk.DISABLED)
        
        
    def insert_and_resize_textbox2(self,text_widget, content):
        """
        Insert content into the provided text widget and resize its height based on content's lines.
        """
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, content)
        
        lines = content.split("\n")
        line_count = len(lines) + 1  # adding an additional line for padding
        text_widget.configure(height=line_count)


    def show_context_info(self):
        for (label, text_widget), key in zip(self.prompt_frames, self.datas.keys()):
            label.config(text=key)
            content = str(self.datas[key])
            self.insert_and_resize_textbox(text_widget, content)
            
    def show_mem_info_context_info(self,mems):
        for (label, text_widget), key in zip(self.mem_info_prompt_frames, 
                                             mems.keys()):
            label.config(text=key)
            content = str(mems[key])
            self.insert_and_resize_textbox(text_widget, content)

    def show_data(self):
        continue_judge = self.dataloader.step()
        if not continue_judge:
            messagebox.showinfo("Done", "All data has been checked!")
            self.save_and_exit()
        self.context_generator = self.dataloader.get_cur_context_generator()
        general_description = self.dataloader.get_general_description()
        self.datas["general_description"] = general_description
        tenant_info, ac_info = self.dataloader.get_cur_tenant_info()
        self.datas["concise_role_description"] = tenant_info
        self.datas["acquaintance_desciption"] = ac_info        
        
        # 理论上这里应该是在approve之前的第一个dialogue。
        continue_status = self.show_one_dialogue() 
        # if not continue_status:
        #     self.show_data()

    def show_one_dialogue(self):
        try:
            self.dialogue, mem_info = next(self.context_generator)
        
            context_info = self.dialogue.get("context")
            content_info = self.dialogue.get("content")
            self.datas["context_info"] = "\n".join(context_info)
            self.datas["content_info"] = [f"{k} : {v}" for k,v in content_info.items()]
            self.datas["content_info"] = "\n".join(self.datas["content_info"])
            if (len(self.datas.keys())> len(self.prompt_frames)):
                self.create_frame_window()
                
            if list(mem_info.keys())[0] not in self.mems.keys():
                self.mems.update(mem_info)
                if len(mem_info)>0:
                    self.append_frame_mem_window(mem_info)
            # self.window.mainloop()
            
            # Display content for the keys we want
            self.show_context_info()
            return True
            
        except Exception as e:
            return False# generator内没有数据了，需要再次调用show_data()

    
    

    def save_and_exit(self):
        self.dataloader.save_data()
        # 关闭窗口
        self.window.destroy()
        # self.mem_window.destroy()
        # self.mem_info_window.destroy()
        
    # 认为是人类
    def approve(self):
        self.dialogue["testflag"] = True
        self.dialogue["turingflag"] = True
        if self.show_one_dialogue():
            return
        else:
            self.show_data()
        
    # 认为是robot
    def reject(self):
        self.dialogue["testflag"] = True
        self.dialogue["turingflag"] = False
        if self.show_one_dialogue():
            return
        else:
            self.show_data()
        
    


class DataLoader(BaseModel):
    root_dir :str 
    tenant_data :dict = {}
    
    
    
    
    # {tenants:{sn}} 存dict 一个邻接表
    sn_rounds_data:list = []
    # mem_id:{prompts,response} 存dict
    sn_mems_data: list = []
    
    id_tenants:list  =[] # 本轮所有judge的tenant A
    id_listened_tenants:list =[]# A的所有acquantance
    
    index_experiment:int = 0 # 实验的index（对应一次运行）
    index_tenant:str = "-1" # 正在judge的tenant A
    index_listened_tenant:str = "-1" # tenant A正在对话的tenant B
    
          
                
    
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        tenental_system_datas = []
        json_dirs = os.listdir(self.root_dir)
        for json_dir in json_dirs:
            data_path = os.path.join(self.root_dir,json_dir)
            assert os.path.exists(data_path),"no such file path: {}".format(data_path)
            with open(data_path,'r',encoding = 'utf-8') as f:
                tenental_system_datas.append(json.load(f))

        tenant_dir = "LLM_PublicHouseAllocation/tasks/backup_data/tenant_5.json"
        with open(tenant_dir,'r',encoding = 'utf-8') as f:
            self.tenant_data = json.load(f)

                
        def update_dialogue(sn_target:dict,sn_mem_update:dict):
            """输入是序列化后的memory结构"""
            for key,value in sn_mem_update.items():
                if key == "dialogues":
                    sn_target["dialogues"].extend(value)
                else:
                    sn_target.update(**{key:value})
            return sn_target
                

        
        for tenental_system_data in tenental_system_datas:
            
            # change store structure
            transfered_sn_rounds = {}
            transfered_sn_mems = {}
            for key, log in tenental_system_data.items():
                if (key=="group"):
                    continue
                for idx,step_type_info in log.get("log_social_network",{}).items():
                    if (idx == "social_network_mem"):
                        for tenant_id, tenant_sn in step_type_info.items():
                            transfered_sn_rounds[tenant_id]= \
                                update_dialogue(transfered_sn_rounds.get(tenant_id,{}),
                                                tenant_sn)
                    else:
                        for step_type, step_type_pr in step_type_info.items():
                            if isinstance(step_type_pr,list):
                                for step_type_pr_one in step_type_pr:
                                    transfered_sn_mems[step_type_pr_one.get("key_social_network")] = \
                                        {
                                            step_type:step_type_pr_one
                                        }
                            elif isinstance(step_type_pr,dict):
                                transfered_sn_mems[step_type_pr.get("key_social_network")] = \
                                step_type_info
                            else:
                                assert False, "unsupported type"
            self.sn_mems_data.append(transfered_sn_mems)
            self.sn_rounds_data.append(transfered_sn_rounds)
                
        
        self.initialize_tenant_loop()        
            
                
    def get_experiment_data(self):
        return self.sn_rounds_data[self.index_experiment]
    
    def initialize_tenant_loop(self):
        self.id_tenants = list(self.sn_rounds_data[self.index_experiment].keys())
        self.id_listened_tenants = []
        self.index_listened_tenant = "-1"
        self.index_tenant = "-1" 

    def get_general_description(self):
        tenant_info = self.tenant_data.get(str(self.index_tenant))
        template ="""communication loop start for tenant [{t_name}] in experiment [{ex_id}]"""   
        return template.format(t_name = tenant_info.get("name"),
                               ex_id = self.index_experiment)
        
    def step_tenant_id(self):
        if len(self.id_tenants) > 0:
            self.index_tenant = self.id_tenants.pop(0)
            return True
        return False
    
    
    # 在每次generator里面的信息用完后，进行step
    def step(self): # 更新index
        if self.index_tenant == '-1' and \
            len(self.id_tenants) > 0:
            self.index_tenant = self.id_tenants.pop(0)
        
        # 实验开始前的initialize
        if self.index_listened_tenant == "-1":
            self.id_listened_tenants = list(self.sn_rounds_data[self.index_experiment][self.index_tenant]["social_network"].keys())
            
            
        if len(self.id_listened_tenants) > 0 :
            self.index_listened_tenant = self.id_listened_tenants.pop(0)
            return True
        elif len(self.id_tenants) > 0 or self.index_tenant == -1:
            self.index_tenant = self.id_tenants.pop(0)
            # 为新的tenant分配listener
            self.id_listened_tenants = list(self.sn_rounds_data[self.index_experiment][self.index_tenant]["social_network"].keys())
            return True
        elif self.index_experiment < len(self.sn_rounds_data):
            self.index_experiment +=1
            return True
        else:
            return False
        
        
    def get_cur_context_generator(self):
        ### return context, response_content, mem(related: prompt))
        
        # 生成index_tenant和index_listened_tenant的对话记录（rounds_data）
        # 并通过key 获取相应的memory信息    
        tenant_sn_memory = self.sn_rounds_data[self.index_experiment][self.index_tenant]
        tenant_sn_memory = tenant_sn_memory["social_network"][self.index_listened_tenant]
        
        dialogues = tenant_sn_memory.get("dialogues",[])
        dialogues.sort(key=lambda x: x.get("timestamp"))
        for dialogue in dialogues:
            dialogue_mem_key = dialogue.get("key_social_network")
            mem = self.sn_mems_data[self.index_experiment].get(dialogue_mem_key)
            yield dialogue,{dialogue_mem_key:mem}
            # 每次yield最早的那句dialogue,以及产生这句dialogue对应的memory
        
    def get_cur_tenant_info(self):
       
        tenant_infos = self.tenant_data[self.index_tenant]
        role_description_template="""\
You are {name}. You earn {monthly_income} per month.\
Your family members include: {family_members}."""
        concise_role_description = role_description_template.format_map({"name":tenant_infos["name"],
                                    **tenant_infos}
                                   )
        if self.tenant_data[self.index_tenant].get("personal_preference",False):
            concise_role_description += "Up to now, your personal preference for house is :{}".format(
                tenant_infos.get("personal_preference")
            )
            
        social_network = ["{name}: {relation}".format(
                    name = neigh_tenant_info.get("name",neigh_tenant_id),
                    relation = neigh_tenant_info.get("relation","friend")
                    )
                     for neigh_tenant_id,neigh_tenant_info
                     in tenant_infos.get("social_network",{}).items()] 
        
        social_network_str = "\n".join(social_network)
            
        return concise_role_description,social_network_str
    
    
    def save_data(self):
        with open("LLM_PublicHouseAllocation\LLM_decision_test\social_network\data_label\sn_rounds_data.json",
                  "w", encoding='utf-8') as file:
            json.dump(self.sn_rounds_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)
        with open("LLM_PublicHouseAllocation\LLM_decision_test\social_network\data_label\sn_mems_data.json",
                  "w", encoding='utf-8') as file:
            json.dump(self.sn_mems_data, file, indent=4,separators=(',', ':'),ensure_ascii=False)




if __name__ == "__main__":
    
    # load data
    # data_dir: directory of jsons
    data_dir ="LLM_PublicHouseAllocation\LLM_decision_test\social_network\\tenental_system"
    saving_dir = "LLM_PublicHouseAllocation\LLM_decision_test\social_network\data_label/QA_test.json"
    app = App(data_dir,saving_dir)
    
    ## 标注过程：
    
    # root_dir = "LLM_PublicHouseAllocation\LLM_decision_test\qa_clear_data" 
    # saving_root_dir = "LLM_PublicHouseAllocation\LLM_decision_test/result"
    # json_dirs = os.listdir(root_dir)
    # json_dirs.pop(0)
    # for json_dir in json_dirs:
    #     data_dir = os.path.join(root_dir,json_dir)
    #     saving_dir = os.path.join(saving_root_dir,json_dir)
    #     app = App(data_dir,saving_path=saving_dir)

    # 图灵测试部分：
    
    # data_dir = "LLM_PublicHouseAllocation\LLM_decision_test/test\saving_QA.json"
    # app = App(data_dir,saving_path = data_dir)