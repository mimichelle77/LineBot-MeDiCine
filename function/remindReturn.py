# -*- coding: utf-8 -*-
"""
Created on Sat Oct  6 15:46:31 2018

提醒領藥--處方箋過期日
@author: 蔡念定

!pip install flask
!pip install pymongo
!pip install selenium
!pip install jieba
!pip install pygame
!pip install simplejson
!pip install pytagcloud
!pip install line-bot-sdk
!pip install apscheduler
"""

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
global user_task_list,user_list
user_task_list = {}
user_list = []

temp = []

client = MongoClient('localhost',27017)
db = client["MeDiCine"]
collectionPL = db["pharmacy-locate"]

########## 提醒領藥 ##########

# 宣告調度器
scheduler_only = BackgroundScheduler()
scheduler = BackgroundScheduler()
scheduler2 = BackgroundScheduler()

class remindReturn():

    def __init__(self,mdinfo,line_bot_api,event):
        self.line_bot_api = line_bot_api
        self.event = event
        self.uid = event.source.user_id
        self.QR_Date = mdinfo["就醫日期"]   #QR Code掃出的就醫日期
        self.QR_Date = str(int(self.QR_Date)+19110000) #民國轉西元
        self.QR_Date = datetime.datetime.strptime(self.QR_Date, '%Y%m%d')  #將就醫日期轉換成西元-月份-日期(包含時分秒)
        self.QR_days = mdinfo["給藥日份"]   #QR Code掃出的給藥日份
        self.QR_Rx=mdinfo['處方類別']  #處方箋:一般處方 1 ; 連續處方 2
        self.end_Date=self.QR_Date+datetime.timedelta(int(self.QR_days)*3-1)   #處方箋過期日

    
    #取得QR_code、詢問完領藥次數後執行
    def remind_getMed(self,end_Date):   
        today = datetime.datetime.now() #抓取系統時間
        #判斷處方箋是否過期
        if today < end_Date:
            #print(end_Date)
            #添加定時任務(調度器:scheduler_only)
            scheduler_only.add_job(remind_job, 'interval', days=int(qr_Days)-7, id=self.uid, start_date=qr_Date+datetime.timedelta(hours=8), end_date=end_Date+datetime.timedelta(int(qr_Days)), args=[end_Date])
            line_bot_api.reply_message(self.uid, TextSendMessage(text="開啟提醒領藥功能\n如欲取消領藥提醒，請輸入\"取消\""))
        else:
            #print("此連續處方箋已經過期，無法領藥")
            line_bot_api.reply_message(self.uid, TextSendMessage(text="此連續處方箋已經過期，無法領藥!"))
        #開始運行調度器:scheduler_only
        scheduler_only.start()


    #scheduler_only/scheduler調度器呼叫(給藥日份屆滿前7日呼叫一次)
    def remind_job(end_Date):
        #print("remind_job\n")
        today = datetime.datetime.now() #抓取系統時間(第1天提醒，共7天)
        endDay=date.today()+datetime.timedelta(7) #最後一天提醒領藥(共7天)
        
        #刪除scheduler_only的工作(第一次的領藥提醒天數需-7，故僅執行一次)
        if scheduler_only.get_jobs():
            scheduler_only.remove_job(self.uid)
        #判斷是否已添加scheduler
        if not(scheduler.get_jobs()):
            scheduler.add_job(remind_job, 'interval', days=int(qr_Days), id=self.uid, start_date=today, end_date=end_Date+datetime.timedelta(int(qr_Days)), args=[])
        
        #判斷是否已超過領藥次數(通常為3次)
        if today <= end_Date:
            scheduler2.add_job(remind_txt, 'interval', days=1, id=self.uid, start_date=today, end_date=endDay, args=[endDay])
            #開始運行調度器2
            scheduler2.start()
        else:
            #print("連續處方箋領藥提醒\n"+qr_Name+"先生/小姐，連續處方籤通常只可領3次，請記得回醫院看診～\n\n如欲繼續領藥提醒，需重新掃描新的處方箋，謝謝！")
            line_bot_api.push_message(self.uid, TextSendMessage(text="連續處方箋領藥提醒\n，連續處方籤通常只可領3次，請記得回醫院看診～\n\n如欲繼續提醒領藥功能，需重新掃描新的處方箋，謝謝！"))
            
            if scheduler.get_jobs():
                scheduler.remove_job(self.uid)
                if scheduler2.get_jobs():
                    scheduler2.remove_job(self.uid)

    #取得QR_code，詢問此處方箋共可領藥幾次
    def endDate_Num(self):
        #先判斷是否為連續處方箋
        if self.QR_Rx=="2":
            #print("此為連續處方籤，請問此處方箋共可領藥幾次？")
            confirm= TemplateSendMessage(
                alt_text='此為連續處方籤，請問此處方箋共可領藥幾次？',
                template=ConfirmTemplate(
                text='請問此處方箋共可領藥幾次？',
                actions=[
                    PostbackTemplateAction(
                        label='2次',
                        text='2次',
                        data='action=endDate_Num&status=2'
                    ),
                    PostbackTemplateAction(
                        label='3次',
                        text='3次',
                        data='action=endDate_Num&status=3'
                    )
                ])
            )
            self.line_bot_api.push_message(self.uid,confirm)
