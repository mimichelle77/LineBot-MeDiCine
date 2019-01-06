#-*- coding: utf-8 -*-
import requests,json
from pymongo import MongoClient
#print ("FUXK!")

url="mongodb://localhost:27017/"
client = MongoClient(url)

db = client['Medicine']
collect = db['pharmacy']


res=requests.get('http://data.fda.gov.tw/cacheData/35_3.json')
res_json = json.loads(res.text)
#  {{"Name[0][1]["機構名稱"]" : "", "Number[7]["電話"]" : "", "City[2]["地址縣市別"]" : "",
# "Area[3]["地址鄉鎮市區"]" : "", "Address[2][3][4]["地址街道巷弄號"]" : "",}


for i in range(0,len(res_json)) : 
	NNCAA_json = {}

	for n in range(0,9) : 
		NNCAA_json["name"] = res_json[i][1]["機構名稱"]
		NNCAA_json["boss"] = res_json[i][5]["負責人姓名"]
		NNCAA_json["sex"] = res_json[i][6]["負責人性別"]
		NNCAA_json["number"] = res_json[i][7]["電話"]
		NNCAA_json["official"] = res_json[i][8]["是否為健保特約藥局"]
		NNCAA_json["city"] = res_json[i][2]["地址縣市別"]+res_json[i][3]["地址鄉鎮市區"]
		NNCAA_json["address"] = res_json[i][2]["地址縣市別"] + res_json[i][3]["地址鄉鎮市區"] + res_json[i][4]["地址街道巷弄號"]
	p=collect.insert_one(NNCAA_json).inserted_id
	print ('Done' + str(i+1) + '!')
	print(p)





`






