import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import json
import re
import random 

class App:
    def __init__(self, 
                 dir_path = None, 
                 saving_path = None):
        
        self.mode = True # True 表示save_response
        
        if dir_path ==None:
            dir_path = f"EconAgent/LLM_decision_test/data"
            assert os.path.exists(dir_path),f"The data directory :{dir_path} doesn't exist!!"
            data_files = os.listdir(dir_path)
            self.data_list = []
            
            for data_file in data_files:
                data_path = os.path.join(dir_path,data_file)
                with open(data_path,'r',encoding = 'utf-8') as f:
                    data_one = json.load(f)
                    if isinstance(data_one,dict):
                        data_one = list(data_one.values())
                        
                    self.data_list.extend(data_one)
            self.dir_path = dir_path 
        else:
            assert os.path.exists(dir_path),"no such file path: {}".format(dir_path)
            with open(dir_path,'r',encoding = 'utf-8') as f:
                self.data_list = json.load(f)
            self.dir_path=os.path.dirname(dir_path)
            
        if saving_path == None:
            import time
            self.saving_path = f"./result"
            if not os.path.exists(self.saving_path):
                os.makedirs(self.saving_path)
            
        else:
            self.saving_path = saving_path
            
        # for data in self.data_list:
        # self.data_list["reasonal"] = "human_response"/"robot_response" 
        
        self.index = 0
        self.window = tk.Tk()
        self.window.title("Check Consistency")
        
        self.create_prompt_frame()
        
        

        
        
    def create_prompt_frame(self):
        
        self.prompt_frames = []
        self.response_frames = [] # 左，右
        
        
        self.frame_top = tk.Frame(self.window)
        self.frame_top.grid(row=0, column=0,columnspan=2, sticky="nsew", padx=5, pady=5)
        
        row_counter_top = 0
        # Dynamic creation of labels and text widgets based on keys of prompt_inputs
        
        for key in self.data_list[0]['prompt_inputs'].keys():
            if key not in ["task","thought_type","choose_type","thought_hint","agent_scratchpad"]:
                # frame_top_one = tk.Frame(self.frame_top,bg="blue")
                # frame_top_one.grid(row=row_counter_top, column=0,columnspan=2, sticky="nsew", padx=5, pady=5)
                
                label = tk.Label(self.frame_top, text=key)
                #label.pack(side=tk.LEFT,expand=True)
                label.grid(row=row_counter_top,column=0,columnspan=2, sticky="nsew",padx=5, pady=5)

                text_widget = tk.Text(self.frame_top, wrap=tk.WORD,bg="yellow",height=100, width=160)
                #text_widget.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
                text_widget.grid(row=row_counter_top+1,column=0,columnspan=2, sticky="nsew",padx=5, pady=5)

                if not self.mode:
                    text_widget.configure(state=tk.DISABLED)  # Make it read-only

                self.prompt_frames.append((label, text_widget))
                row_counter_top += 2
        
        
        self.frame_bottom = tk.Frame(self.window)
        self.frame_bottom.grid(row=1, column=0, columnspan=2,sticky="nsew", padx=5, pady=5)
        
        
        
        for idx_col,data_type in enumerate(["Model 1","Model 2"]):
            frame_bottom_one = tk.Frame(self.frame_bottom)
            frame_bottom_one.grid(row=0, column = idx_col, sticky="nsew", padx=5, pady=5)
            
            label = tk.Label(frame_bottom_one, text=data_type)
            label.grid(row = 0, column = 0, sticky="nsew", padx=5, pady=5)
            
            frames_col = []
            for idx,key in enumerate(['output', 'thought']):
                frame = tk.Frame(frame_bottom_one)
                #frame.pack(side=tk.LEFT)
                frame.grid(row = idx+1, column=0, sticky="nsew", padx=5, pady=5)

                label = tk.Label(frame, text=key)
                # label.pack(side=tk.LEFT)
                label.grid(row = 0,column=0,sticky="nsew", padx=10, pady=5)

                text_widget = tk.Text(frame, wrap=tk.WORD, height=100, width=80)
                # text_widget.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
                text_widget.grid(row=1,column=0,sticky="nsew", padx=5, pady=5)
                text_widget.tag_config('red', foreground='red', font=('Arial', 12, 'bold'))
                # self.prompt_frames.append((label, text_widget))
                frames_col.append((label, text_widget))
                
            self.response_frames.append(frames_col)
            
            # buttom frame
            button_frame = tk.Frame(frame_bottom_one)
            button_frame.grid(row=3,column=0, pady=5)
            
            if idx_col ==0:
                
                button = tk.Button(button_frame, 
                               text="This One is more reasonable", 
                               command=self.approve_left)
                button_2 = tk.Button(button_frame, 
                               text="Both answar is acceptable", 
                               command=self.approve_all)
            else:
                button = tk.Button(button_frame, 
                               text="This One is more reasonable", 
                               command=self.approve_right)
                
                button_2 = tk.Button(button_frame, 
                               text="no answar is acceptable", 
                               command=self.approve_none)
                
            button.pack(side=tk.LEFT, padx=10)
            button_2.pack(side =tk.LEFT,padx=10)
            
            
            
        
        self.window.grid_rowconfigure(0, weight=50)
        self.window.grid_rowconfigure(1, weight=50)
        
        self.window.grid_columnconfigure(0, weight=1)
        # self.window.grid_columnconfigure(1, weight=1)
        self.show_data()
        self.window.protocol("WM_DELETE_WINDOW", self.save_and_exit)
        self.window.mainloop()
        

    def insert_and_resize_textbox(self,
                                  text_widget, 
                                  content,
                                  format = "default"):
        """
        Insert content into the provided text widget and resize its height based on content's lines.
        """
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        if format != "default":
            text_widget.insert(tk.END, content,format)
        else:
            text_widget.insert(tk.END, content)
        
        lines = content.split("\n")
        line_count = len(lines) + 1  # adding an additional line for padding
        text_widget.configure(height=line_count+3)
        if not self.mode:
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
        text_widget.configure(height=line_count+3)

    def show_data(self):
        if self.index < len(self.data_list):
            current_data = self.data_list[self.index]

            # Filter out keys we don't want to display
            display_keys = [key for key in current_data['prompt_inputs'].keys() if key not in ['task', 
                                                                                               'thought_type', 
                                                                                               'choose_type',
                                                                                               'thought_hint',
                                                                                               "agent_scratchpad"]]
            
            # Ensure the number of frames matches the number of display keys
            while len(self.prompt_frames) < len(display_keys):
                frame = tk.Frame(self.frame_top)
                frame.grid(row=len(self.prompt_frames), column=0, sticky="nsew", padx=5, pady=5)
                
                label = tk.Label(frame)
                label.pack(side=tk.LEFT)

                text_widget = tk.Text(frame, wrap=tk.WORD, height=80, width=50)
                text_widget.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
                if not self.mode:
                    text_widget.configure(state=tk.DISABLED)  # Make it read-only

                self.prompt_frames.append((label, text_widget))

            # Display content for the keys we want
            for (label, text_widget), key in zip(self.prompt_frames, display_keys):
                label.config(text=key)
                content = str(current_data['prompt_inputs'][key])
                self.insert_and_resize_textbox(text_widget, content)

            # Display response
            response_keys = ["human_response",
                             "robot_response"]
            random.shuffle(response_keys)
            
            for idx,(col_frames,response_key) in enumerate(zip(self.response_frames,response_keys)):
                response = current_data[response_key]
                self.data_list[self.index][response_key]["frame"] = idx
                for (label, text_widget), key in zip(col_frames, ['output','thought']):
                    label.config(text=key)
                    content = str(response[key])
                    self.insert_and_resize_textbox(text_widget, content)
                
        else:
            self.save_and_exit()

    def save_and_exit(self):
        # 保存 data_list（在这个例子中我们只是将其打印到控制台）
        
        finished_QA_result = []
        unfinished_QA_result=[]
        for data in self.data_list:
            if  "reasonal" in data.keys():
                finished_QA_result.append(data)
            else:
                unfinished_QA_result.append(data)
        
        if len(finished_QA_result) > 0 and len(unfinished_QA_result)==0 and "testflag" in finished_QA_result[0]:     
            auc = self.compute_auc(finished_QA_result)
            messagebox.showinfo("Done", "All data has been checked!The accuracy is "+str(auc)+" !!")
        elif len(unfinished_QA_result)==0:
            messagebox.showinfo("Done", "All data has been checked!")
        
        import time
        saving_path_dir = os.path.join(self.saving_path,f"{time.time()}")
        os.makedirs(saving_path_dir)
        
        finished_json_dir = os.path.join(saving_path_dir,"finished_QA_result.json")
        with open(finished_json_dir, 'w', encoding='utf-8') as file:
            json.dump(finished_QA_result, file, indent=4,separators=(',', ':'),ensure_ascii=False)
            
        if (len(unfinished_QA_result)>0):
            # 删除原来的所有data文件，合成未标注的data
            unfinished_json_dir = os.path.join(saving_path_dir,"unfinished_QA_result.json")
            with open(unfinished_json_dir, 'w', encoding='utf-8') as file:
                json.dump(unfinished_QA_result, file, indent=4,separators=(',', ':'),ensure_ascii=False)
        # 关闭窗口
        self.window.destroy()
        
    def approve_all(self):
       
        if self.index < len(self.data_list):
            self.data_list[self.index]["reasonal"] = "both"
            
            self.index += 1
            if self.index == len(self.data_list):
                self.save_and_exit()
            self.show_data()
        else:
            self.save_and_exit()
            
    def approve_none(self):
       
        if self.index < len(self.data_list):
            self.data_list[self.index]["reasonal"] = "none"
            
            self.index += 1
            if self.index == len(self.data_list):
                self.save_and_exit()
            self.show_data()
        else:
            self.save_and_exit()
            
    def approve_left(self):
        response_types =["human_response",
                         "robot_response"]
        if self.index < len(self.data_list):
            current_data = self.data_list[self.index]
            
            for response_type in response_types:
                idx = current_data[response_type]["frame"]
                if idx == 0:
                    self.data_list[self.index]["reasonal"] = response_type
                    break   
                         
            
            self.index += 1
            if self.index == len(self.data_list):
                self.save_and_exit()
            self.show_data()
        else:
            self.save_and_exit()
    
    def approve_right(self):
        response_types =["human_response",
                         "robot_response"]
        if self.index < len(self.data_list):
            current_data = self.data_list[self.index]
            
            for response_type in response_types:
                idx = current_data[response_type]["frame"]
                if idx == 1:
                    self.data_list[self.index]["reasonal"] = response_type
                    break            
            
            self.index += 1
            if self.index == len(self.data_list):
                self.save_and_exit()
            self.show_data()
        else:
            self.save_and_exit()
            
        
    def back(self):
        if self.index > 0:
            self.index  -= 1
            self.show_data()
        
    

    def compute_auc(self,data_list):
        auc_dict={
            "human_response":0,
            "robot_response":0,
            "error":0
        }
        for data_response in data_list:
            auc_dict[data_response.get("reasonal","error")] +=1
        
        auc = auc_dict["robot_response"]/(auc_dict["human_response"]+auc_dict["robot_response"])
        return auc



if __name__ == "__main__":
    
    ## 标注过程：
    
    # root_dir = "EconAgent\LLM_decision_test\qa_clear_data" 
    # saving_root_dir = "EconAgent\LLM_decision_test/result"
    # json_dirs = os.listdir(root_dir)
    # json_dirs.pop(0)
    # for json_dir in json_dirs:
    #     data_dir = os.path.join(root_dir,json_dir)
    #     saving_dir = os.path.join(saving_root_dir,json_dir)
    #     app = App(data_dir,saving_path=saving_dir)

    # 图灵测试部分：
    
    app = App()
    #app = App()