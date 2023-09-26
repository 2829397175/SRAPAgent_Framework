import tkinter as tk
from tkinter import messagebox, simpledialog

class App:
    def __init__(self, data_list):
        self.data_list = data_list
        self.index = 0
        self.create_window()
        
    def create_window(self):
        self.window = tk.Tk()
        self.window.title("Check Consistency")
        
        # Text widget for prompt_inputs
        self.prompt_text = tk.Text(self.window, wrap=tk.WORD, width=200, height=15)
        self.prompt_text.insert(tk.END, "PROMPT INPUTS:")
        self.prompt_text.configure(state=tk.DISABLED)  # Make it read-only
        self.prompt_text.pack(padx=20, pady=10)
        
        # Text widget for response
        self.response_text = tk.Text(self.window, wrap=tk.WORD, width=200, height=15)
        self.response_text.insert(tk.END, "RESPONSE:")
        self.response_text.pack(padx=20, pady=10)
        
        # Buttons
        self.approve_button = tk.Button(self.window, text="Approve", command=self.approve)
        self.approve_button.pack(side=tk.LEFT, padx=10)
        
        self.reject_button = tk.Button(self.window, text="Reject", command=self.reject)
        self.reject_button.pack(side=tk.LEFT, padx=10)
        
        self.save_button = tk.Button(self.window, text="Save Response", command=self.save_response)
        self.save_button.pack(side=tk.LEFT, padx=10)
        
        self.show_data()
        
        self.window.mainloop()

    def show_data(self):
        if self.index < len(self.data_list):
            current_data = self.data_list[self.index]
            
            # Display prompt_inputs
            self.prompt_text.configure(state=tk.NORMAL)
            self.prompt_text.delete("2.0", tk.END)
            self.prompt_text.insert(tk.END, "\n" + str(current_data['prompt_inputs']))
            self.prompt_text.configure(state=tk.DISABLED)
            
            # Display response
            self.response_text.delete("2.0", tk.END)
            self.response_text.insert(tk.END, "\n" + str(current_data['response']))
            
            if not current_data['response']:
                self.response_text.insert(tk.END, "\n\nResponse is empty. Please input and save your response.")
        else:
            messagebox.showinfo("Done", "All data has been checked!")
            self.window.destroy()

    def approve(self):
        self.index += 1
        self.show_data()
        
    def reject(self):
        self.index += 1
        self.show_data()
        
    def save_response(self):
        # Open a dialog to input the response
        response_content = simpledialog.askstring("Input Response", "Please input your response:")
        
        if response_content:
            # Save the response to the current data
            self.data_list[self.index]['response']['output'] = response_content
            self.show_data()

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
    }]  # Replace with your JSON data

app = App(data)
