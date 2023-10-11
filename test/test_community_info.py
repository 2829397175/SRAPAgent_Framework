def merge_community_info(com_a, com_b):
    # 创建一个新的空字典用于存储合并后的信息
    merged_community = {}

    # 合并sum_num和sum_remain_num
    merged_community["sum_num"] = com_a["sum_num"] + com_b["sum_num"]
    merged_community["sum_remain_num"] = com_a["sum_remain_num"] + com_b["sum_remain_num"]

    # 合并每种房型的信息
    for house_type in ["large_house","middle_house","small_house"]:
        if house_type in com_a and house_type in com_b:
            merged_community[house_type] = {}
            
            # 合并remain_number
            merged_community[house_type]["remain_number"] = com_a[house_type]["remain_number"] + com_b[house_type]["remain_number"]
            
            # 合并index
            merged_community[house_type]["index"] = com_a[house_type]["index"] + com_b[house_type]["index"]
            
            # 对于其他的字段（例如living_room、size和cost），可以选择保留其中一个或按需合并。这里仅作为示例保留community_1的内容。
            for key in ["living_room", "size", "cost"]:
                merged_community[house_type][key] = com_a[house_type][key]
        elif house_type in com_a:
            merged_community[house_type]=com_a[house_type]
        elif house_type in com_b:
            merged_community[house_type]=com_b[house_type]
                    
    # 对于其他的字段（例如location、community_name等），可以选择保留其中一个或按需合并。这里仅作为示例保留community_1的内容。
    for key in ["community_id", "community_name", "location", "en_location", "value_inch", "description", "nearby_info","available"]:
        merged_community[key] = com_a[key]
        
    return merged_community
def add_community_pool(cur_pool,add_com):
    if cur_pool=={}:
        for _,c_info in add_com.items():     
            c_info["available"]=True
        return add_com
    elif add_com=={}:
        return cur_pool
    for community_id,community_info in add_com.items():
        if community_id in cur_pool:
            cur_pool[community_id]=merge_community_info(cur_pool[community_id],community_info)
            cur_pool[community_id]["available"]=True
        else:
            cur_pool[community_id]=community_info
            cur_pool[community_id]["available"]=True
    return cur_pool
cur_pool={}
add2={
      "community_1":{
         "community_id":"community_1",
         "community_name":"longxing",
         "location":"北京市大兴区隆平大街2号",
         "en_location":"No. 2, Longping Street, Daxing District, Beijing",
         "value_inch":30,
         "sum_num":3,
         "sum_remain_num":3,
         "description": "There are sports facilities, including football fields and basketball courts, with a large green area and a large distance between buildings.",
         "nearby_info": "This community is surrounded by: Supermarkets include Hualian Boutique Supermarket (Guaxiang Road Branch), Carrefour Supermarket (Danish Town Branch); Schools include Zhongrui Hotel Management College, Beijing Second Foreign Language College Zhongrui Hotel Management College Living Area; Restaurants include microfood origin Hunan Cuisine (Hunan Cuisine Branch), fisherman's handle iron pot (Longjing Bay 2nd District Branch); Banks include Agricultural Bank of China ATM (Longgazhuang Shunjing Road Branch); .This commnunity does not have: subway, shopping mall, hospital, park,",
         "large_house":{
            "remain_number":1,
            "living_room":"one room",
            "index":["house_4"],
            "size":"60.92-61.8",
            "cost":"1830"
         },
         "small_house":{
            "remain_number":2,
            "living_room":"zero room",
            "index":["house_6","house_7"],
            "size":"37.96-38.09",
            "cost":"1140"
         }
      },
      "community_2":{
         "community_id":"community_2",
         "community_name":"jinkejiayuan",
         "location":"北京市大兴区永旺路1号",
         "en_location":"No. 1 Yongwang Road, Daxing District, Beijing",
         "value_inch":34,
         "sum_num":2,
         "sum_remain_num":2,
         "description":"The green area of the community should account for more than 30% of the total land area, and the central urban area should not be less than 25%.",
         "nearby_info": "This commnunity is surrounded by: Metro includes biomedical base; supermarkets include Sure Beauty Fresh Life Supermarket (Jinke Tianwei Store), Tiangong Courtyard Convenience Store; shopping malls include Yuejie Times Square, Longhu Beijing Daxing Tianjie; parks include Yongxing River Wetland Park; schools include Daxing Experimental Primary School affiliated to Beijing Education College (Merging Campus), Tsinghua University School Primary School; restaurants include Fan Laoman (Tiangong Courtyard Store), Xinlong Sijiu Meat (Tiangong Courtyard Store); banks include Beijing Rural Commercial Bank 24-hour Self-help Bank (Beibei Village Branch), Beijing Daxing Jiuiyin Village Bank (Tiangong Courtyard Branch); .This commnunity does not have: Hospital,",
         "small_house":{
            "remain_number":2,
            "living_room":"zero room",
            "index":["house_12","house_14"],
            "size":"27.76-44.62",
            "cost":"952-1517"
         }
      },
      "community_3":{
         "community_id":"community_3",
         "community_name":"ronghui",
         "location":"北京市大兴区华伦路1号院",
         "en_location":"Courtyard No. 1, Hualun Road, Daxing District, Beijing",
         "value_inch":40,
         "sum_num":3,
         "sum_remain_num":3,
         "description": "The community has good greenery, a parking lot, and several kinds of sports and fitness equipment.",
         "nearby_info": "This commnunity is surrounded by: Metro includes Huangcun Railway Station, Huangcun West Street; Supermarket includes Wumi Supermarket (Jianxing Store), Ma Jie Department Store Flagship Store (Daxing Daxing Dazhong Fengli Store); Mall includes Daxing Dazheng Chunli, Daxing Xingcheng Commercial Building; Hospital includes Beijing Daxing Town Dazheng Dongli Community Health Service Station, Beijing Daxing Jingnan Traditional Chinese Medicine Hospital; Park includes Daxing Street Park, Daxing Agricultural Machinery Park; School includes Beijing Daxing District First Middle School, Beijing Daxing District Fifth Elementary School; Restaurants include Half-Demon Green Pepper Grilled Fish (Daxing Hotel Branch), Meizhou Dongpo Restaurant (Daxing Huangcun Branch); Bank includes Industrial and Commercial Bank of China ATM (Beijing Daxing Branch), Postal Savings Bank of China (Daxing Branch); .This commnunity: not have\n",
         "large_house":{
            "remain_number":3,
            "living_room":"two rooms",
            "index":["house_15","house_16","house_17"],
            "size":"56.14-58.33",
            "cost":"2240-2320"
         }
      }
   }

add1={
         "community_1":{
            "community_id":"community_1",
            "community_name":"longxing",
            "location":"北京市大兴区隆平大街2号",
            "en_location":"No. 2, Longping Street, Daxing District, Beijing",
            "value_inch":30,
            "sum_num":5,
            "sum_remain_num":5,
            "description": "There are sports facilities, including football fields and basketball courts, with a large green area and a large distance between buildings.",
            "nearby_info": "This community is surrounded by: Supermarkets include Hualian Boutique Supermarket (Guaxiang Road Branch), Carrefour Supermarket (Danish Town Branch); Schools include Zhongrui Hotel Management College, Beijing Second Foreign Language College Zhongrui Hotel Management College Living Area; Restaurants include microfood origin Hunan Cuisine (Hunan Cuisine Branch), fisherman's handle iron pot (Longjing Bay 2nd District Branch); Banks include Agricultural Bank of China ATM (Longgazhuang Shunjing Road Branch); .This commnunity does not have: subway, shopping mall, hospital, park,",
            "large_house":{
               "remain_number":4,
               "living_room":"one room",
               "index":["house_1","house_2","house_3","house_5"],
               "size":"60.92-61.8",
               "cost":"1830"
            },
            "small_house":{
               "remain_number":1,
               "living_room":"zero room",
               "index":["house_8"],
               "size":"37.96-38.09",
               "cost":"1140"
            }
         },
         "community_2":{
            "community_id":"community_2",
            "community_name":"jinkejiayuan",
            "location":"北京市大兴区永旺路1号",
            "en_location":"No. 1 Yongwang Road, Daxing District, Beijing",
            "value_inch":34,
            "sum_num":3,
            "sum_remain_num":3,
            "description":"The green area of the community should account for more than 30% of the total land area, and the central urban area should not be less than 25%.",
            "nearby_info": "This commnunity is surrounded by: Metro includes biomedical base; supermarkets include Sure Beauty Fresh Life Supermarket (Jinke Tianwei Store), Tiangong Courtyard Convenience Store; shopping malls include Yuejie Times Square, Longhu Beijing Daxing Tianjie; parks include Yongxing River Wetland Park; schools include Daxing Experimental Primary School affiliated to Beijing Education College (Merging Campus), Tsinghua University School Primary School; restaurants include Fan Laoman (Tiangong Courtyard Store), Xinlong Sijiu Meat (Tiangong Courtyard Store); banks include Beijing Rural Commercial Bank 24-hour Self-help Bank (Beibei Village Branch), Beijing Daxing Jiuiyin Village Bank (Tiangong Courtyard Branch); .This commnunity does not have: Hospital,",
            "small_house":{
               "remain_number":3,
               "living_room":"zero room",
               "index":["house_9","house_10","house_11"],
               "size":"27.76-44.62",
               "cost":"952-1517"
            }
         }
   }
add3={
      "community_2":{
         "community_id":"community_2",
         "community_name":"jinkejiayuan",
         "location":"北京市大兴区永旺路1号",
         "en_location":"No. 1 Yongwang Road, Daxing District, Beijing",
         "value_inch":34,
         "sum_num":1,
         "sum_remain_num":1,
         "description":"The green area of the community should account for more than 30% of the total land area, and the central urban area should not be less than 25%.",
         "nearby_info": "This commnunity is surrounded by: Metro includes biomedical base; supermarkets include Sure Beauty Fresh Life Supermarket (Jinke Tianwei Store), Tiangong Courtyard Convenience Store; shopping malls include Yuejie Times Square, Longhu Beijing Daxing Tianjie; parks include Yongxing River Wetland Park; schools include Daxing Experimental Primary School affiliated to Beijing Education College (Merging Campus), Tsinghua University School Primary School; restaurants include Fan Laoman (Tiangong Courtyard Store), Xinlong Sijiu Meat (Tiangong Courtyard Store); banks include Beijing Rural Commercial Bank 24-hour Self-help Bank (Beibei Village Branch), Beijing Daxing Jiuiyin Village Bank (Tiangong Courtyard Branch); .This commnunity does not have: Hospital,",
         "small_house":{
            "remain_number":1,
            "living_room":"zero room",
            "index":["house_13"],
            "size":"27.76-44.62",
            "cost":"952-1517"
         }
      },
      "community_3":{
         "community_id":"community_3",
         "community_name":"ronghui",
         "location":"北京市大兴区华伦路1号院",
         "en_location":"Courtyard No. 1, Hualun Road, Daxing District, Beijing",
         "value_inch":40,
         "sum_num":2,
         "sum_remain_num":2,
         "description": "The community has good greenery, a parking lot, and several kinds of sports and fitness equipment.",
         "nearby_info": "This commnunity is surrounded by: Metro includes Huangcun Railway Station, Huangcun West Street; Supermarket includes Wumi Supermarket (Jianxing Store), Ma Jie Department Store Flagship Store (Daxing Daxing Dazhong Fengli Store); Mall includes Daxing Dazheng Chunli, Daxing Xingcheng Commercial Building; Hospital includes Beijing Daxing Town Dazheng Dongli Community Health Service Station, Beijing Daxing Jingnan Traditional Chinese Medicine Hospital; Park includes Daxing Street Park, Daxing Agricultural Machinery Park; School includes Beijing Daxing District First Middle School, Beijing Daxing District Fifth Elementary School; Restaurants include Half-Demon Green Pepper Grilled Fish (Daxing Hotel Branch), Meizhou Dongpo Restaurant (Daxing Huangcun Branch); Bank includes Industrial and Commercial Bank of China ATM (Beijing Daxing Branch), Postal Savings Bank of China (Daxing Branch); .This commnunity: not have\n",
         "middle_house":{
            "remain_number":2,
            "living_room":"one room",
            "index":["house_18","house_19"],
            "size":"44.96-47.13",
            "cost":"1800-1885"
         }
      }
   }

cur_pool=add_community_pool(cur_pool,add1)
cur_pool=add_community_pool(cur_pool,add2)
cur_pool=add_community_pool(cur_pool,add3)
print(len(cur_pool))