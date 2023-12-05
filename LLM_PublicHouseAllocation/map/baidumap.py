import requests
import json

#from translate import Translator
from pydantic import BaseModel, Field

class Baidumap(BaseModel):
    api_key:str

    def get_lat_lng(self,location):
        # Make a request to the Baidu Maps geocoding API
        url = f"http://api.map.baidu.com/geocoding/v3/?address={location}&output=json&ak={self.api_key}"
        
        try:
            response = requests.get(url)
            # Parse the JSON response
            data = json.loads(response.text)   
            if data["status"] ==0:        
                # Extract the latitude and longitude from the response
                lat = data['result']['location']['lat']
                lng = data['result']['location']['lng']

                # Return the latitude and longitude as a string
                return f"{lat},{lng}"
            else:
                print(f"Error: {data['message']}")
                return None

        except:
            print(f"Error: fail to request url")
            return None

    def get_shortest_commute_time(self,
                                  origin, 
                                  destination,
                                  community_index:str,
                                  community_name:str):
        # Convert the origin and destination to latitude and longitude
        origin_lat_lng = self.get_lat_lng(origin)
        destination_lat_lng = self.get_lat_lng(destination)

        # Make a request to the Baidu Maps API
        url = f"http://api.map.baidu.com/direction/v2/transit?origin={origin_lat_lng}&destination={destination_lat_lng}&ak={self.api_key}"
        response = requests.get(url)
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return ""
        # Check if the request was successful
        if data['status'] == 0:
            # Find the route with the shortest duration
            shortest_route = min(data['result']['routes'], key=lambda route: route['duration'])

            # Return the duration of the shortest route
            return f"{community_index}({community_name}) is"+str(int(shortest_route['duration']/60))+" minutes away from my workplace by subway and bus"
        else:
            print(f"Error: {data['message']}")
            return ""




    def retrieve_coordinates(self,location):
        geocoding_api = f"http://api.map.baidu.com/geocoding/v3/?address={location}&output=json&ak={self.api_key}"
        response = requests.get(geocoding_api)
        data = json.loads(response.text)
        return data["result"]["location"]["lat"], data["result"]["location"]["lng"]

    def retrieve_nearby_info(self,location, radius=1000, query_list=None):
        if query_list is None:
            query_list = ["地铁", "超市", "商场", "医院", "公园", "学校", "餐厅", "银行"]

        lat, lng = self.retrieve_coordinates(location)
        info_dict = {}

        for query in query_list:
            place_search_api = f"http://api.map.baidu.com/place/v2/search?query={query}&page_size=20&page_num=0&location={lat},{lng}&radius={radius}&output=json&ak={self.api_key}&scope=2"
            response = requests.get(place_search_api)
            data = json.loads(response.text)
            if "results" in data:
                results = data["results"]
                if len(results) > 2:
                    info_dict[query] = [result["name"] for result in results[:2]]
                else:
                    info_dict[query] = [result["name"] for result in results[:]]
            else:
                print(f"No 'results' in data for query {query}. Data: {data}")
                info_dict[query] = []
        return info_dict
    
    # def translate_to_english(self,text):
    #     translator = Translator(from_lang='zh', to_lang='en')
    #     translation = translator.translate(text)
    #     return translation



    def generate_description(self,location, radius=1000, query_list=None):
        info_dict = self.retrieve_nearby_info(location, radius, query_list)

        description = f"This commnunity is surrounded by："
        for key, values in info_dict.items():
            if values !=[]:
                description += f"{key}包括{', '.join(values)}；"
        description += f".This commnunity does not have："
        for key, values in info_dict.items():
            if values == []:
                description += f"{key},"

        #description=self.translate_to_english(description)
        return description
    
if __name__ =="__main__":
    baidumap=Baidumap(api_key="weqCXjBTHdMybUxCineQ50ttzLUvd2dl")
    print(baidumap.generate_description("北京市大兴区三合北巷2、4号院"))
    # print(baidumap.generate_description("北京市大兴区永旺路1号"))
    # print(baidumap.generate_description("北京市大兴区隆平大街2号"))
