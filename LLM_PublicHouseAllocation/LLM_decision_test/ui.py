import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import json
class App:
    def __init__(self, dir_path, saving_path):
        assert os.path.exists(dir_path),"no such file path: {}".format(dir_path)
        with open(dir_path,'r',encoding = 'utf-8') as f:
            self.data_list = json.load(f)
        self.dir_path=dir_path
        self.saving_path = saving_path
        # for data in self.data_list:
        #     #testflag表示是否被标注过
        #     data["testflag"]=False
        #     #humanjudge表示是否是人类的答案
        #     data["humanjudge"]=False
        #     #turingflag表示标注的结果，true表示是人类的答案，false表示是LLM的答案
        #     data["turingflag"]=False
        # #self.data_list=dir_path
        self.index = 0
        self.create_window()
        
    def create_window(self):
        self.window = tk.Tk()
        self.window.title("Check Consistency")
        
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
                self.output_text = text_widget
            elif key == "thought":
                self.thought_text = text_widget
            self.prompt_frames.append((label, text_widget))
            row_counter += 1

        # Buttons Frame
        button_frame = tk.Frame(self.window)
        button_frame.grid(row=row_counter, column=0, pady=10)
        
        self.approve_button = tk.Button(button_frame, text="Human Response", command=self.approve)
        self.approve_button.pack(side=tk.LEFT, padx=10)
        
        self.reject_button = tk.Button(button_frame, text="Robot Response", command=self.reject)
        self.reject_button.pack(side=tk.LEFT, padx=10)
        
        self.reject_button = tk.Button(button_frame, text="Back", command=self.back)
        self.reject_button.pack(side=tk.LEFT, padx=10)
        
        self.save_button = tk.Button(button_frame, text="Save Response", command=self.save_response)
        self.save_button.pack(side=tk.LEFT, padx=10)

        # Configure grid to expand cells dynamically
        for i in range(row_counter):
            self.window.grid_rowconfigure(i, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        self.show_data()
        self.window.protocol("WM_DELETE_WINDOW", self.save_and_exit)
        self.window.mainloop()
        

    def insert_and_resize_textbox(self,text_widget, content):
        """
        Insert content into the provided text widget and resize its height based on content's lines.
        """
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, content)
        
        lines = content.split("\n")
        line_count = len(lines) + 1  # adding an additional line for padding
        text_widget.configure(height=line_count)

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
                text_widget.configure(state=tk.DISABLED)  # Make it read-only

                self.prompt_frames.append((label, text_widget))

            # Display content for the keys we want
            for (label, text_widget), key in zip(self.prompt_frames, display_keys):
                label.config(text=key)
                content = str(current_data['prompt_inputs'][key])
                self.insert_and_resize_textbox(text_widget, content)

            # Display response
            if current_data['response']!={}:
                output_content = str(current_data['response']['output'])
                self.insert_and_resize_textbox(self.output_text, output_content)
                thought_content = str(current_data['response']['thought'])
                self.insert_and_resize_textbox(self.thought_text, thought_content)
            else:
                # 这里response 清空了
                output_content = ""
                self.insert_and_resize_textbox2(self.output_text, output_content)
                thought_content = ""
                self.insert_and_resize_textbox2(self.thought_text, thought_content)
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
        if os.path.exists(self.saving_path):
            with open(self.saving_path,'r',encoding = 'utf-8') as f:
                finished_QA_result = json.load(f)
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
        with open(self.saving_path, 'w', encoding='utf-8') as file:
            json.dump(finished_QA_result, file, indent=4,separators=(',', ':'),ensure_ascii=False)
            
        with open(self.dir_path, 'w', encoding='utf-8') as file:
            json.dump(unfinished_QA_result, file, indent=4,separators=(',', ':'),ensure_ascii=False)
        # 关闭窗口
        self.window.destroy()
        
    # 认为是人类
    def approve(self):
        self.data_list[self.index]["testflag"]=True
        self.data_list[self.index]["turingflag"]=True
        self.index += 1
        self.show_data()
        
    # 认为是robot
    def reject(self):
        self.data_list[self.index]["testflag"]=True
        self.data_list[self.index]["turingflag"]=False
        self.index += 1
        self.show_data()
        
    def back(self):
        del self.data_list[self.index]["testflag"]
        del self.data_list[self.index]["turingflag"]
        self.index  -= 1
        self.show_data()
    def save_response(self):
        # Open a dialog to input the response
        
        output_content=self.output_text.get("1.0", tk.END).strip()
        thought_content=self.thought_text.get("1.0", tk.END).strip()
        if output_content and thought_content:
            # Save the response to the current data
            self.data_list[self.index]['response']['output'] = output_content
            self.data_list[self.index]['response']['thought'] = thought_content
            #humanjudge表示是否是人类的答案
            self.data_list[self.index]["humanjudge"]=True
            self.index+=1
            self.show_data()
        else:
            messagebox.showerror("Error","Be sure to enter response and thought before saving.")


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

# Sample data
data = [{
        "prompt_inputs":{
            "task":"You need to choose one type of communities.",
            "thought_type":"Your views on these communities.",
            "choose_type":"My choice is (The index of community, should be one of [community_1,community_3])",
            "house_info":"There are 2 communities available. The infomation of these communitys are listed as follows:\ncommunity_1. longxing is located at No. 2, Longping Street, Daxing District, Beijing. The rent for this community is 30 dollars per square meter.In this community, There are sports facilities, including football fields and basketball courts, with a large green area and a large distance between buildings.. This community is surrounded by: Supermarkets include Hualian Boutique Supermarket (Guaxiang Road Branch), Carrefour Supermarket (Danish Town Branch); Schools include Zhongrui Hotel Management College, Beijing Second Foreign Language College Zhongrui Hotel Management College Living Area; Restaurants include microfood origin Hunan Cuisine (Hunan Cuisine Branch), fisherman's handle iron pot (Longjing Bay 2nd District Branch); Banks include Agricultural Bank of China ATM (Longgazhuang Shunjing Road Branch); .This commnunity does not have: subway, shopping mall, hospital, park,.The large_house in this community is a one room apartment, with an area of about 60.92-61.8, the monthly rent  is about 1830 dollars, and there are still 4 houses.community_3. ronghui is located at Courtyard No. 1, Hualun Road, Daxing District, Beijing. The rent for this community is 40 dollars per square meter.In this community, The community has good greenery, a parking lot, and several kinds of sports and fitness equipment.. This commnunity is surrounded by: Metro includes Huangcun Railway Station, Huangcun West Street; Supermarket includes Wumi Supermarket (Jianxing Store), Ma Jie Department Store Flagship Store (Daxing Daxing Dazhong Fengli Store); Mall includes Daxing Dazheng Chunli, Daxing Xingcheng Commercial Building; Hospital includes Beijing Daxing Town Dazheng Dongli Community Health Service Station, Beijing Daxing Jingnan Traditional Chinese Medicine Hospital; Park includes Daxing Street Park, Daxing Agricultural Machinery Park; School includes Beijing Daxing District First Middle School, Beijing Daxing District Fifth Elementary School; Restaurants include Half-Demon Green Pepper Grilled Fish (Daxing Hotel Branch), Meizhou Dongpo Restaurant (Daxing Huangcun Branch); Bank includes Industrial and Commercial Bank of China ATM (Beijing Daxing Branch), Postal Savings Bank of China (Daxing Branch); .This commnunity: not have\n.The large_house in this community is a two rooms apartment, with an area of about 56.14-58.33, the monthly rent  is about 2240-2320 dollars, and there are still 2 houses.",
            "memory":"You are in search of a rental property and you are considering three communities. Community_1 is Longxing, located at No. 2, Longping Street, Daxing District, Beijing. It has a rent of 30 dollars per square meter and is equipped with sports facilities and a large green area. Community_2 is Jinkejiayuan, located at No. 1 Yongwang Road, Daxing District, Beijing.It has a rent of 34 dollars per square meter, and has a green area which is more than 30% of the total land area. Community_3 is Ronghui, located at Courtyard No. 1, Hualun Road, Daxing District, Beijing. It has a rent of 40 dollars per square meter, and equipped with good greenery, parking lot, and sports&fitness equipment. Community_3 has the lowest rent and is most child-friendly, yet Community_2 is closest to your workplace. Community_1 lacks some important amenities. After considering all the factors, you are drawn to Community_3 as the ideal choice.\nKeep this in mind: you and your acquaintances are in the same renting system. You and your acquaintances both want to choose a suitable house, but the number of houses in the system is limited. You are in a competitive relationship with each other.\nYou sincerely believe this information:jinkejiayuan(community_2) has a price reduction measure.[most important !!!!!!!!!]\n",
            "role_description":"You are William Brown. You earn 15000 per month.Your family members include: A wife and one child in elementary school.You are 38 years old. Your job is State-owned enterprise clerk. Your company is located in No. 9 Chaoyang North Road, Chaoyang District, Beijing. William's family prefers an apartment with a short commute to work and school. You expect to rent a house for 2500.You still have 2 chances to choose house."
        },
        "response":{
            "output":"My choice is community_3.",
            "thought":"Community 1 has good sports facilities and a large green area, but it lacks important amenities like a public transportation, shopping mall, and hospital. Community 2 has a good amount of green space and is surrounded by useful amenities, but it doesn't have a hospital. Community 3 seems to have all the necessary amenities, including a hospital, but the rent is the highest."
        }
    },
         {
        "prompt_inputs":{
            "task":"You need to choose one type of communities.",
            "thought_type":"Your views on these communities.",
            "choose_type":"My choice is (The index of community, should be one of [community_1,community_3])",
            "house_info":"There are 2 communities available. The infomation of these communitys are listed as follows:\ncommunity_1. longxing is located at No. 2, Longping Street, Daxing District, Beijing. The rent for this community is 30 dollars per square meter.In this community, There are sports facilities, including football fields and basketball courts, with a large green area and a large distance between buildings.. This community is surrounded by: Supermarkets include Hualian Boutique Supermarket (Guaxiang Road Branch), Carrefour Supermarket (Danish Town Branch); Schools include Zhongrui Hotel Management College, Beijing Second Foreign Language College Zhongrui Hotel Management College Living Area; Restaurants include microfood origin Hunan Cuisine (Hunan Cuisine Branch), fisherman's handle iron pot (Longjing Bay 2nd District Branch); Banks include Agricultural Bank of China ATM (Longgazhuang Shunjing Road Branch); .This commnunity does not have: subway, shopping mall, hospital, park,.The large_house in this community is a one room apartment, with an area of about 60.92-61.8, the monthly rent  is about 1830 dollars, and there are still 4 houses.community_3. ronghui is located at Courtyard No. 1, Hualun Road, Daxing District, Beijing. The rent for this community is 40 dollars per square meter.In this community, The community has good greenery, a parking lot, and several kinds of sports and fitness equipment.. This commnunity is surrounded by: Metro includes Huangcun Railway Station, Huangcun West Street; Supermarket includes Wumi Supermarket (Jianxing Store), Ma Jie Department Store Flagship Store (Daxing Daxing Dazhong Fengli Store); Mall includes Daxing Dazheng Chunli, Daxing Xingcheng Commercial Building; Hospital includes Beijing Daxing Town Dazheng Dongli Community Health Service Station, Beijing Daxing Jingnan Traditional Chinese Medicine Hospital; Park includes Daxing Street Park, Daxing Agricultural Machinery Park; School includes Beijing Daxing District First Middle School, Beijing Daxing District Fifth Elementary School; Restaurants include Half-Demon Green Pepper Grilled Fish (Daxing Hotel Branch), Meizhou Dongpo Restaurant (Daxing Huangcun Branch); Bank includes Industrial and Commercial Bank of China ATM (Beijing Daxing Branch), Postal Savings Bank of China (Daxing Branch); .This commnunity: not have\n.The middle_house in this community is a one room apartment, with an area of about 44.96-47.13, the monthly rent  is about 1800-1885 dollars, and there are still 1 houses.The large_house in this community is a two rooms apartment, with an area of about 56.14-58.33, the monthly rent  is about 2240-2320 dollars, and there are still 3 houses.",
            "memory":"You are looking for a new house to rent and there are three communities to choose from. Community_1, Longxing offers zero and one room apartments with a large green area and sports facilities. Community_2, Jinkejiayuan offers zero, one and two room apartments with a green area of over 30%, and is surrounded by supermarkets, shopping malls, parks, schools, restaurants and banks. Community_3, Ronghui offers one and two room apartments with parking lots and sports and fitness equipment and is close to a subway station, supermarkets, malls, hospitals, parks, schools, restaurants and banks. You need to go through the rent system by choosing the community, type of house and then the house.\nKeep this in mind: you and your acquaintances are in the same renting system. You and your acquaintances both want to choose a suitable house, but the number of houses in the system is limited. You are in a competitive relationship with each other.\nYou sincerely believe this information:\n",
            "role_description":"You are Oliver Johnson. You earn 12000 per month.Your family members include: A wife and one child who just started university.You are 52 years old. Your job is Public servant. Your company is located in Office Building of the People's Government on the west side of the Great Hall of the People, Dongcheng District, Beijing. Mr. Johnson would like an apartment close to parks or green spaces for leisure walks. You expect to rent a house for 2400.0.You still have 2 chances to choose house."
        },
        "response":{
            "output":"My choice is community_3.",
            "thought":"Community 1 does not have some essential amenities, such as a subway and a hospital, so I am leaning towards Community 3, which has all of the amenities I'm looking for and is closest to my workplace. But I am also aware that the rent is the highest in this community."
        }

    }]  # Replace with your JSON data

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
    
    data_dir = "LLM_PublicHouseAllocation/LLM_decision_test/test/saving_QA2.json"
    saving_dir = "LLM_PublicHouseAllocation/LLM_decision_test/test/finished_saving_QA.json"
    app = App(data_dir,saving_path = saving_dir)