###########################
#
# Random User Generator
#
# This program calls https://randomuser.me to get random users for testing
#
#####################
import json
import requests






api_endpoint = "https://randomuser.me/api/"

r = requests.get(api_endpoint)
if ( r.status_code == 200):
    print("Request Status OK!")
    #traffic_data_dict_list = r.json()    #this will return a list of dictionaries.  Each dictionary represents once segment traffic data
    #write_json_file("traffic_data1.json",traffic_data_dict_list)   
else:
    print ("Error Code "+str(r.status_code))
