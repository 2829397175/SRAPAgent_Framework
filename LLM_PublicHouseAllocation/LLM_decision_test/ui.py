import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import json
import re
class App:
    def __init__(self, 
                 dir_path = None, 
                 saving_path = None):
        
        self.mode = True # True 表示save_response
        
        if dir_path ==None:
            dir_path = f"./data"
            assert os.path.exists(dir_path),f"The data directory :{dir_path} doesn't exist!!"
            data_files = os.listdir(dir_path)
            self.data_list = []
            for data_file in data_files:
                data_path = os.path.join(dir_path,data_file)
                with open(data_path,'r',encoding = 'utf-8') as f:
                    data_list = json.load(f)
                    if isinstance(data_list,dict):
                        data_list = list(data_list.values())
                    self.data_list.extend(data_list)
            self.dir_path = dir_path 
        else:
            assert os.path.exists(dir_path),"no such file path: {}".format(dir_path)
            with open(dir_path,'r',encoding = 'utf-8') as f:
                data_list = json.load(f)
                if isinstance(data_list,dict):
                    data_list = list(data_list.values())
                self.data_list = data_list
            self.dir_path = os.path.dirname(dir_path)
            
        if saving_path == None:
            import time
            self.saving_path = f"./result"
            if not os.path.exists(self.saving_path):
                os.makedirs(self.saving_path)
            
        else:
            self.saving_path = saving_path
     
        self.index = 0
        self.window = tk.Tk()
        self.window.title("Save Response")
        
        self.create_prompt_frame()
        
        

        
        
    def create_prompt_frame(self):
        
        self.prompt_frames = []
        row_counter = 0

        # Dynamic creation of labels and text widgets based on keys of prompt_inputs
        for key in self.data_list[0]['prompt_inputs'].keys():
            if key not in ["task","thought_type","choose_type"]:
                frame = tk.Frame(self.window)
                frame.grid(row=row_counter, column=0, sticky="nsew", padx=20, pady=5)
                
                label = tk.Label(frame, text=key)
                label.pack(side=tk.LEFT)

                text_widget = tk.Text(frame, wrap=tk.WORD, height=5, width=50)
                text_widget.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
                if not self.mode:
                    text_widget.configure(state=tk.DISABLED)  # Make it read-only

                self.prompt_frames.append((label, text_widget))
                row_counter += 1
        
        for key in ['output', 'thought']:
            frame = tk.Frame(self.window)
            frame.grid(row=row_counter, column=0, sticky="nsew", padx=20, pady=5)

            label = tk.Label(frame, text=key)
            label.pack(side=tk.LEFT)

            text_widget = tk.Text(frame, wrap=tk.WORD, height=5, width=50)
            text_widget.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

            if key == "output":
                text_widget.tag_config('red', foreground='red', font=('Arial', 12, 'bold'))
                self.output_text = text_widget

            elif key == "thought":
                text_widget.tag_config('red', foreground='red', font=('Arial', 12, 'bold'))
                self.thought_text = text_widget
            self.prompt_frames.append((label, text_widget))
            row_counter += 1

        # Buttons Frame
        button_frame = tk.Frame(self.window)
        button_frame.grid(row=row_counter, column=0, pady=10)
        
        # self.approve_button = tk.Button(button_frame, text="Human Response", command=self.approve)
        # self.approve_button.pack(side=tk.LEFT, padx=10)
        
        # self.reject_button = tk.Button(button_frame, text="Robot Response", command=self.reject)
        # self.reject_button.pack(side=tk.LEFT, padx=10)
        
        self.back_button = tk.Button(button_frame, text="Back", command=self.back)
        self.back_button.pack(side=tk.LEFT, padx=10)
        
        self.save_button = tk.Button(button_frame, text="Save Response", command=self.save_response)
        self.save_button.pack(side=tk.LEFT, padx=10)

        # Configure grid to expand cells dynamically
        for i in range(row_counter):
            self.window.grid_rowconfigure(i, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
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
        text_widget.configure(height=line_count)
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
        text_widget.configure(height=line_count)

    def show_data(self):
        if self.index < len(self.data_list):
            current_data = self.data_list[self.index]

            # Filter out keys we don't want to display
            display_keys = [key for key in current_data['prompt_inputs'].keys() if key not in ['task', 'thought_type', 'choose_type']]
            
            # Ensure the number of frames matches the number of display keys
            while len(self.prompt_frames) < len(display_keys):
                frame = tk.Frame(self.window)
                frame.grid(row=len(self.prompt_frames), column=0, sticky="nsew", padx=20, pady=5)
                
                label = tk.Label(frame)
                label.pack(side=tk.LEFT)

                text_widget = tk.Text(frame, wrap=tk.WORD, height=5, width=50)
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
            if current_data['response']=={} or "response" not in current_data.keys():
                output_content = ""
                self.insert_and_resize_textbox2(self.output_text, output_content)
                thought_content = ""
                self.insert_and_resize_textbox2(self.thought_text, thought_content)
            
            else:
                # 这里response 清空了
                output_content = str(current_data['response']['output'])
                self.insert_and_resize_textbox(self.output_text, output_content,"red")
                thought_content = str(current_data['response']['thought'])
                self.insert_and_resize_textbox(self.thought_text, thought_content,"red")
                
        else:
            finished_QA_result = []
            unfinished_QA_result=[]
            for data in self.data_list:
                if data["testflag"]!=None and data["turingflag"]!=None:
                    finished_QA_result.append(data)
                elif data["testflag"]!=None:
                    del data["testflag"]
                    unfinished_QA_result.append(data)
                elif data["turingflag"]!=None:
                    del data["turingflag"]
                    unfinished_QA_result.append(data)
                else:
                    unfinished_QA_result.append(data)
            if "testflag" in finished_QA_result[0]:     
                auc=self.compute_auc(finished_QA_result)
                messagebox.showinfo("Done", "All data has been checked!The accuracy is "+str(auc)+" !!")
            else:
                messagebox.showinfo("Done", "All data has been checked!")
            self.save_and_exit()

    def save_and_exit(self):
        # 保存 data_list（在这个例子中我们只是将其打印到控制台）
        
        finished_QA_result = []
        # if os.path.exists(self.saving_path):
        #     with open(self.saving_path,'r',encoding = 'utf-8') as f:
        #         finished_QA_result = json.load(f)
        unfinished_QA_result=[]
        for data in self.data_list:
            if data.get("testflag",None)!=None and data.get("turingflag",None)!=None:
                finished_QA_result.append(data)
            elif data.get("testflag",None)!=None:
                unfinished_QA_result.append(data)
            elif data.get("turingflag",None)!=None:
                unfinished_QA_result.append(data)
            else:
                unfinished_QA_result.append(data)
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
        
    # 认为是人类
    def approve(self):
        output_content=self.output_text.get("1.0", tk.END).strip()
        thought_content=self.thought_text.get("1.0", tk.END).strip()
        if output_content and thought_content:
            try:
                assert output_content.strip() != "" and thought_content.strip() != ""
            except Exception as e:
                messagebox.showerror("Error","You should label the data first before Turing test!! Enter the content and press saving button.")
                return
            self.data_list[self.index]["testflag"]=True
            self.data_list[self.index]["turingflag"]=True
            self.index += 1
            if self.index == len(self.data_list):
                self.save_and_exit()
            self.show_data()
        else:
            messagebox.showerror("Error","You should label the data first before Turing test!! Enter the content and press saving button.")
        
    # 认为是robot
    def reject(self):
        output_content=self.output_text.get("1.0", tk.END).strip()
        thought_content=self.thought_text.get("1.0", tk.END).strip()
        if output_content and thought_content:
            try:
                assert output_content.strip() != "" and thought_content.strip() != ""
            except Exception as e:
                messagebox.showerror("Error","You should label the data first before Turing test!! Enter the content and press saving button.")
                return
            self.data_list[self.index]["testflag"]=True
            self.data_list[self.index]["turingflag"]=False
            self.index += 1
            if self.index == len(self.data_list):
                self.save_and_exit()
            self.show_data()
        else:
            messagebox.showerror("Error","You should label the data first before Turing test!! Enter the content and press saving button.")
            
        
    def back(self):
        # del self.data_list[self.index]["testflag"]
        # del self.data_list[self.index]["turingflag"]
        self.index  -= 1
        self.show_data()
        
    def save_response(self):
        # Open a dialog to input the response
        
        output_content=self.output_text.get("1.0", tk.END).strip()
        thought_content=self.thought_text.get("1.0", tk.END).strip()
        if output_content and thought_content:
            # check output format
            
            try:
                assert output_content.strip() != "" and thought_content.strip() != ""
            except Exception as e:
                messagebox.showerror("Error","You should label the data first !!")
                return
            
            try:
                assert len(thought_content)> 30
            except Exception as e:
               
                messagebox.showerror("Error","喂，不要摸鱼!好好标注QAQ,多写点thought")
                return
            # Save the response to the current data
            if "response" not in self.data_list[self.index].keys():
                self.data_list[self.index]['response'] = {}
                
            self.data_list[self.index]['response']['output'] = output_content
            self.data_list[self.index]['response']['thought'] = thought_content
            #humanjudge表示是否是人类的答案
            self.data_list[self.index]["humanjudge"]=True
            self.index += 1
            if self.index == len(self.data_list):
                self.save_and_exit()
            self.show_data()
        else:
            messagebox.showerror("Error","Be sure to enter response and thought before saving!")


    def compute_auc(self,data_list):
        sum,correct_num=0,0
        for data in data_list:
            if data.get("testflag")==True:
                humanjudge=data.get("humanjudge")
                turingresult=data.get("turingflag")
                if humanjudge!=None and turingresult!=None:
                    if humanjudge==turingresult:
                        correct_num+=1
                    sum+=1
        return correct_num/sum



if __name__ == "__main__":
    
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
    
    app = App()
    #app = App()