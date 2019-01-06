# -*- coding: utf-8 -*-


#!/usr/bin/python
#-*-coding:utf-8 -*
from flask import Flask,url_for,request
from operator import itemgetter
from urllib.parse import parse_qs
from linebot import LineBotApi
from linebot.models import *
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime,timedelta,date
from pymongo import MongoClient
import json,re,requests,jieba,os,datetime,time,threading

user_task = {'user_id':'',
             'status': 1,
             'ask_count': 0,
             }

app = Flask(__name__)

client = MongoClient('localhost',27017)
db = client["MeDiCine"]
collectionPL = db["pharmacy-locate"]

class locationPH():
    #google map
    def locationapi(msg):        
        #Distance Matrix API 金鑰
        mapapi="AIzaSyACPkahPx9DAFXqgzaUFPk8YqyJofHNBFc"
        #正規化地址,取得區域鄉鎮
        district=r'(\D+?(區|鎮區|[鄉鎮區]))'
        match=re.search(district,msg)
        loc=match.group().split('台灣')[1]
        loc=loc.replace('台','臺') 
        mapurl='https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins='+msg+'&destinations='
        pharmacy=collectionPL.find({'地址鄉鎮市區':loc[3:6]}).limit(60) #max=66
        newlist=[]
        for i in pharmacy:
            mapurl=mapurl+i['地址街道巷弄號']+'|'
            newlist.append(i)
        mapurl=mapurl+'&units=metric&key='+mapapi
        res=requests.get(mapurl)
        res_json =json.loads(res.text)
        num=0
        for i in res_json['rows'][0]['elements']:
            if(i['status']!="NOT_FOUND"):
                newlist[num]["distance"]=i["distance"]['value']
                newlist[num]["time"]=i["duration"]['text']
            else:
                newlist[num]["distance"]=99999
                newlist[num]["time"]=99999
            num=num+1	
        newlist=sorted(newlist,key=itemgetter('distance'))
        addressinfo=[]
        for i in range(0,len(newlist)):
            if(i==5):
                break
            addressinfo.append(CarouselColumn(
                    title=newlist[i]['name'],
                    text=newlist[i]['address']+'，距離你共'+str(newlist[i]['distance'])+'公尺，走路'+newlist[i]['time'].replace("mins","分")+'鐘即可抵達',
                    actions=[
                        PostbackTemplateAction(
                            label='店家資訊',
                            data='action=pharmacy&address='+newlist[i]['address']
                        ),
                        URITemplateAction(
                            label='Google map導航',
                            uri='https://www.google.com.tw/maps/dir/'+msg+'/'+newlist[i]['address']
                        )
                    ]
                ))
        carousel_template_message = TemplateSendMessage(
        alt_text='藥局選單',
        template=CarouselTemplate(
            columns=addressinfo
        )
        )
        self.line_bot_api.reply_message(self.uid,carousel_template_message)


