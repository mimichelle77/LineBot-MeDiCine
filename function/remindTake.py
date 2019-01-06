# -*- coding: utf-8 -*-
'''
Created on Fri Apr 20 04:01:46 2018
@author: user
'''

#!/usr/bin/python
#-*-coding:utf-8 -*
#!pip install flask
#!pip install line-bot-sdk
#!pip install apscheduler
from flask import Flask,url_for,request
from operator import itemgetter
from urllib.parse import parse_qs
import json,re,requests,jieba,os,datetime,time,threading
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime,timedelta
from linebot.models import *
                
user_task = {'user_id':'',
             'status': 1,
             'ask_count': 0,
             }

app = Flask(__name__)
global user_task_list,user_list
user_task_list = {}
user_list = []
temp = []

#政府編碼資料 {'id'='','code':'','freq_unit': '','time': ''}
#freq_unit->day:每日；week:每周；month:每月
#time->am:早上；noon:中午；pm:晚上；bed:睡前；星期幾
data_freq = [{'id':1,'code':'QW()','freq_unit': 'week','time': ['noon']},
             {'id':4,'code':'QOD','freq_unit': 'day','time': ['noon'],'use':'隔日使用一次'},
             {'id':5,'code':'QD','freq_unit': 'day','time': ['noon'],'use':''},
             {'id':6,'code':'QW','freq_unit': 'week','time': ['noon1'],'use':''},
             {'id':7,'code':'QM','freq_unit': 'month','time': ['noon1'],'use':''},
             {'id':8,'code':'QW','freq_unit': 'week','week': ['wed'],'time': ['noon'],'use':'每星期一次'},
             {'id':9,'code':'BIW','freq_unit': 'week','week': ['mon','thu'],'time': ['noon'],'use':'每星期兩次'},
             {'id':10,'code':'TIW','freq_unit': 'week','week': ['mon','wed','fri'],'time': ['noon'],'use':'每星期三次'},
             {'id':13,'code':'QH','freq_unit': 'day','use':''},
             {'id':14,'code':'QMN','freq_unit': 'day','use':''},
             {'id':15,'code':'QD','freq_unit': 'day','time': ['noon'],'use':'每日一次'},
             {'id':16,'code':'QDAM','freq_unit': 'day','time': ['am'],'use':'每日一次上午使用'},
             {'id':17,'code':'QDPM','freq_unit': 'day','time': ['noon'],'use':'每日一次下午使用'},
             {'id':18,'code':'QDHS','freq_unit': 'day','time': ['bed'],'use':'每日一次睡前使用'},
             {'id':19,'code':'QN','freq_unit': 'day','time': ['pm'],'use':'每晚使用一次'},
             {'id':20,'code':'BID','freq_unit': 'day','time': ['am','pm'],'use':'每日兩次'},             
             {'id':21,'code':'QAM&HS','freq_unit': 'day','time': ['am','bed'],'use':'上午使用一次且睡前一次'},
             {'id':22,'code':'QPM&HS','freq_unit': 'day','time': ['noon','bed'],'use':'下午使用一次且睡前'},
             {'id':23,'code':'QAM&PM','freq_unit': 'day','time': ['am','noon'],'use':'每日上下午各使用一次'},
             {'id':24,'code':'TID','freq_unit': 'day','time': ['am','noon','pm'],'use':'每日三次'},
             {'id':25,'code':'BID&HS','freq_unit': 'day','time': ['am','noon','bed'],'use':'每日兩次且睡前一次'},
             {'id':26,'code':'QID','freq_unit': 'day','time': ['am','noon','pm','bed'],'use':'每日四次'},
             {'id':27,'code':'HS','freq_unit': 'day','time': ['bed'],'use':'睡前一次'},
             {'id':28,'code':'TID&HS','freq_unit': 'day','time': ['am','noon','pm','bed'],'use':'每日三次且睡前一次'},
             {'id':'test','code':'QQ','freq_unit': 'week','week': ['mon','thu','fri'],'time': ['noon1'],'use':'每日三次且睡前一次'}]
#途徑/作用部位
data_route = [{'code':'AD','route':'左耳','use':'部位','code':'AS','route':'右耳','use':'部位'},
            {'code':'AU','route':'雙耳','use':'部位','code':'ET','route':'氣切內','use':'部位'},
            {'code':'GAR','route':'漱口','use':'用法1','code':'HD','route':'皮下灌注','use':'注射'},
            {'code':'ID','route':'皮內注射','use':'注射','code':'IA','route':'動脈注射','use':'注射'},
            {'code':'IE','route':'脊髓硬膜內注射','use':'注射','code':'IM','route':'肌肉注射','use':'注射'},            
            {'code':'IV','route':'靜脈注射','use':'注射','code':'IP','route':'腹腔注射','use':'注射'},
            {'code':'IPLE','route':'胸膜內注射','use':'注射','code':'ICV','route':'腦室注射','use':'注射'},
            {'code':'IMP','route':'植入','use':'用法2','code':'INHL','route':'吸入','use':'用法2'},
            {'code':'IS','route':'滑膜內注射','use':'注射','code':'IT','route':'椎骨內注射','use':'注射'},
            {'code':'IVA','route':'靜脈添加','use':'注射','code':'IVD','route':'靜脈點滴滴入','use':'注射'},
            {'code':'IVI','route':'玻璃體內注射','use':'注射','code':'IVP','route':'靜脈注入','use':'注射'},
            {'code':'LA','route':'局部麻醉','use':'注射','code':'LI','route':'局部注射','use':'注射'},
            {'code':'NA','route':'鼻子','use':'部位','code':'OD','route':'右眼','use':'部位'},
            {'code':'ORO','route':'口咽直接','use':'部位','code':'OS','route':'左眼','use':'部位'},
            {'code':'OU','route':'雙眼','use':'部位','code':'PO','route':'口服','use':'用法2'},
            {'code':'SC','route':'皮下注射','use':'注射','code':'SCI','route':'結膜下注射','use':'注射'},
            {'code':'SKIN','route':'皮膚','use':'部位','code':'SL','route':'舌下','use':'部位'},
            {'code':'SPI','route':'脊髓','use':'部位','code':'RECT','route':'肛門','use':'部位'},
            {'code':'TPI','route':'局部塗擦','use':'用法1','code':'TPN','route':'全靜脈營養劑','use':'注射'},
            {'code':'VAG','route':'陰道','use':'部位','code':'IRRI','route':'沖洗','use':'用法1'},
            {'code':'EXT','route':'外用','use':'用法2','code':'XX','route':'其他','use':'exp'}]

data_QR_freq = [{'id':0,'meal':'PC','meal_number':'','code_number':""}]

# remind_date = {} #QR Code提醒時間
sched = BackgroundScheduler()
sched.start()
sched1 = BackgroundScheduler()
# sched1.start()
sched2 = BackgroundScheduler()
sched2.start()
setalert={}#當前提醒記錄(手動設定)

class remindTake():

    def __init__(self,mdinfo,line_bot_api,event):
        self.line_bot_api = line_bot_api
        self.event = event
        self.uid = event.source.user_id
        self.QR_Date = mdinfo["就醫日期"]   #QR Code掃出的就醫日期
        self.QR_Date = str(int(self.QR_Date)+19110000) #民國轉西元
        self.QR_days = int(mdinfo["給藥日份"])   #QR Code掃出的給藥日份
        self.remind_date = {}


    #代碼判斷
    def remind_med(self,QR_med_name,QR_QTY,QR_freq,QR_route):
        take_hour = 0#飯前/後N小時
        take_min = 0#飯前/後N分鐘
        QR_freq_meal = ''
        data_QR_freq[0]['meal'] = QR_freq
        QR_date = datetime.strptime(self.QR_Date, '%Y%m%d')
        #給藥途徑
        data_QR_freq[0]['take_msg'] = ''
        for k in range(len(data_route)): 
            if QR_route == data_route[k]['code']:
                data_QR_freq[0]['route'] = data_route[k]['route']
                if data_route[k]['use'] =='部位':
                    data_QR_freq[0]['take_msg'] = '請於「'+ data_QR_freq[0]['route'] + '」使用' +QR_med_name
                elif data_route[k]['use'] =='注射':
                    data_QR_freq[0]['take_msg'] = '請於'+ data_QR_freq[0]['route'] + QR_med_name
                elif data_route[k]['use'] =='用法1':
                    data_QR_freq[0]['take_msg'] = '請使用'+ QR_med_name + data_QR_freq[0]['route']
                elif data_route[k]['use'] =='用法2':
                    data_QR_freq[0]['take_msg'] = '請使用'+ data_QR_freq[0]['route'] + QR_med_name 
        
        if re.search('STAT',QR_freq):
            self.line_bot_api.push_message(self.uid, TextSendMessage(text='您的藥品名稱為' + QR_med_name + '」，\n\n'+' 此藥需「立刻使用」。\n\n作用部位/用法：\n'+ data_QR_freq[0]['take_msg']))
        elif re.search('ASORDER',QR_freq):
            self.line_bot_api.push_message(self.uid, TextSendMessage(text='您的藥品名稱為「' + QR_med_name + '」，\n\n'+'此藥「請依照醫師指示使用」。\n\n作用部位/用法：\n'+ data_QR_freq[0]['take_msg']))
        elif re.search('PRN|HPRN',QR_freq):
            if re.search('HPRN',QR_freq):
                data_QR_freq[0]['code_number'] = list(map(int,re.findall('\d',QR_freq)))
                self.line_bot_api.push_message(self.uid, TextSendMessage(text='您的藥品名稱為「' + QR_med_name + '」，\n\n'+'在需要時，\n'+ data_QR_freq[0]['take_msg'] +'\n(每'+data_QR_freq[0]['code_number']+'小時使用一次)'))
            else:self.line_bot_api.push_message(self.uid, TextSendMessage(text='您的藥品名稱為「' + QR_med_name + '」，\n\n'+'在需要時，\n' + data_QR_freq[0]['take_msg']))            
        else:
            #QW(x,y,z)
            if re.search('\(',QR_freq):
                QW_weeks = [{'id':1,'week':'mon','id':2,'week':'tue','id':3,'week':'wed'},
                            {'id':4,'week':'thu','id':5,'week':'fri','id':6,'week':'sat','id':7,'week':'sun'}]
                data_QR_freq[0]['code']='QW()'
                data_QR_freq[0]['code_number'] = list(map(int,re.findall('\d',QR_freq)))
                for j in range(len(QW_weeks)):
                    for k in range(len(data_QR_freq[0]['code_number'])):
                        if data_QR_freq[0]['code_number'][k] == QW_weeks[j]['id']:
                            data_QR_freq[0]['week'].append(QW_weeks[j]['week'])
            #找相符代碼
            for i in range(len(data_freq)):
                QR_freq_code1 = QR_freq_code2 = ''
                if re.search('AC|PC',QR_freq):
                    match_index = re.search('AC|PC',QR_freq).span()#AC或PC的索引位置
                    QR_freq_code,QR_freq_meal = QR_freq.split(QR_freq[match_index[0]:match_index[1]])#代碼切割(用藥頻率、服用時間)
                    QR_freq_code1 = re.findall('\D',QR_freq_code)#用藥頻率取字元
                    data_QR_freq[0]['meal'] = re.search('AC|PC',QR_freq).group()#服用時間為飯前或飯後
                    data_QR_freq[0]['meal_number'] = list(map(int,re.findall('\d',QR_freq_meal)))#服用時間的數字
                    if any(data_QR_freq[0]['meal_number']):
                        take_hour = data_QR_freq[0]['meal_number'][0]
                    else:
                        take_hour = 1
                else:
                    QR_freq_code = QR_freq
                    QR_freq_code1 = re.findall('\D',QR_freq)#用藥頻率取字元
                for k in range(len(QR_freq_code1)):
                    QR_freq_code2 = QR_freq_code2 + QR_freq_code1[k]
                #找到相符代碼
                if data_freq[i]['code'] == QR_freq_code2: 
                    data_QR_freq[0]['code'] = data_freq[i]['code']
                    data_QR_freq[0]['code_number'] = list(map(int,re.findall('\d',QR_freq_code)))#用藥頻率的數字
                    if data_freq[i]['code']=='QOD':
                        data_QR_freq[0]['code_number'] = 2
                    if data_freq[i]['code']=='QD' and len(data_QR_freq[0]['code_number'])<1 and data_freq[i]['id']==5:
                        continue
                    
                    #飯前/後
                    data_QR_freq[0]['meal_msg'] = '飯後'
                    if QR_freq_meal != '':            
                        if data_QR_freq[0]['meal']=='AC':
                            data_QR_freq[0]['meal_msg'] = '飯前'
                            if QR_freq_meal[-1]=='H':
                                take_hour = data_QR_freq[0]['meal_number'][0]*(-1)
                                data_QR_freq[0]['meal_msg'] = '飯前' + str(abs(take_hour)) + '小時'
                            elif QR_freq_meal[-1]=='M':
                                take_min = data_QR_freq[0]['meal_number'][0]*(-1)
                                data_QR_freq[0]['meal_msg'] = '飯前' + str(abs(take_min)) + '分鐘'
                        elif data_QR_freq[0]['meal']=='PC':
                            if QR_freq_meal[-1]=='H':
                                take_hour = data_QR_freq[0]['meal_number'][0]
                                data_QR_freq[0]['meal_msg'] = '飯後' + str(take_hour) + '小時'
                            elif QR_freq_meal[-1]=='M':
                                take_min = data_QR_freq[0]['meal_number'][0] 
                                data_QR_freq[0]['meal_msg'] = '飯後' + str(take_min) + '分鐘'
                    #告知用藥資訊
                    freq_msg = ''
                    if data_freq[i]['id'] == 13 or data_freq[i]['id'] == 14:
                        if data_freq[i]['id'] == 13:
                            freq_msg = '每'+ data_QR_freq[0]['code_number'] +'小時使用一次'
                        elif data_freq[i]['id'] == 14:
                            freq_msg = '每'+ data_QR_freq[0]['code_number'] +'分鐘使用一次'
                        self.line_bot_api.push_message(self.uid, TextSendMessage(text='您的藥品名稱為「' + QR_med_name + '」，\n\n'+'請「' + freq_msg +'」。\n\n作用部位/用法：\n'+ data_QR_freq[0]['take_msg']))
                    else:                    
                        if data_freq[i]['id'] == 5:
                            freq_msg = '每' + str(data_QR_freq[0]['code_number'][0]) +'日一次'
                        elif data_freq[i]['id'] == 15:
                            freq_msg = '每日一次'
                        elif data_freq[i]['id'] == 6:
                            freq_msg = '每'+ str(data_QR_freq[0]['code_number'][0]) +'星期一次'
                        elif data_freq[i]['id'] == 7:
                            freq_msg = '每'+ str(data_QR_freq[0]['code_number'][0]) +'月一次'
                        else:freq_msg = data_freq[i]['use']
                        self.line_bot_api.push_message(self.uid, TextSendMessage(text='您的藥品名稱為「' + QR_med_name + '」，\n\n'+'使用方式為「' + freq_msg +'」，\n\n'+'請於'+ data_QR_freq[0]['meal_msg'] + '使用。\n\n作用部位/用法：\n'+ data_QR_freq[0]['take_msg']))
                    
                    self.remind_date['i'] = i
                    self.remind_date['take_hour'] = take_hour
                    self.remind_date['take_min'] = take_min
                    self.remind_date['QR_date'] = QR_date
                    # self.remind_med_freq(QR_med_name)
                    break
                                     
                if ('code' not in data_QR_freq[0]) and (i==len(data_freq)-1):
                    print('未在標準碼中找到相符的代碼!\n請聯絡醫生或藥師!')
                    self.line_bot_api.push_message(self.uid, TextSendMessage(text='未在標準碼中找到相符的代碼!\n請聯絡醫生或藥師!'))

     #啟動提醒(頻率-日/週/月)
    def remind_med_freq(self,QR_med_name):
        i = self.remind_date['i']
        take_hour = self.remind_date['take_hour']
        take_min = self.remind_date['take_min']
        QR_date = self.remind_date['QR_date']
        if(data_freq[i]['freq_unit']=='day'): 
            self.remind_med_day(i,take_hour,take_min,QR_date,QR_med_name)
        # elif(data_freq[i]['freq_unit']=='week'): 
        #     time_week = ''
        #     for k in range(len(data_freq[i]['week'])):
        #         time_week = time_week + ',' + data_freq[i]['week'][k]
        #     print('week function')
        #     remind_med_week(i,take_hour,take_min,uid,time_week[1:],QR_date)
        # elif(data_freq[i]['freq_unit']=='month'): 
        #     remind_med_month(i,take_hour,take_min,uid,QR_date)
                
    #提醒頻率-每日
    def remind_med_day(self,i,take_hour,take_min,QR_date,QR_med_name):
        if 'am' in data_freq[i]['time']:
            if (take_min<0):
                take_hour = 6
                take_min = 60 + take_min
            elif (take_hour<0):
                take_hour = 7 + take_hour
                take_min = 1
            elif (take_min>0):
                take_hour = 7
            elif (take_hour>0):
                take_hour = 7 + take_hour
                take_min = 1
            sched.add_job(self.remind_med_text, 'cron', day='*', hour=take_hour, minute=take_min,id=self.uid+QR_med_name,#second='*',
                        start_date=QR_date, end_date=QR_date+timedelta(days=self.QR_days),
                        args=[QR_med_name])
        if 'noon' in data_freq[i]['time']:
            if (take_min<0):
                take_hour = 11
                take_min = 60 + take_min
            elif (take_hour<0):
                take_hour = 12 + take_hour
                take_min = 1
            elif (take_min>0):
                take_hour = 12
            elif (take_hour>0):
                take_hour = 12 + take_hour
                take_min = 1
            sched.add_job(self.remind_med_text, 'cron', day='*', hour=take_hour, minute=take_min,id=self.uid+QR_med_name,
                        start_date=QR_date, end_date=QR_date+timedelta(days=self.QR_days),
                        args=[QR_med_name])
        if 'pm' in data_freq[i]['time']:
            if (take_min<0):
                take_hour = 16
                take_min = 60 + take_min
            elif (take_hour<0):
                take_hour = 17 + take_hour
                take_min = 1
            elif (take_min>0):
                take_hour = 17
            elif (take_hour>0):
                take_hour = 17 + take_hour
                take_min = 1
            sched.add_job(self.remind_med_text, 'cron', day='*', hour=take_hour, minute=take_min,id=self.uid+QR_med_name,
                        start_date=QR_date, end_date=QR_date+timedelta(days=self.QR_days),
                        args=[QR_med_name])
        if 'bed' in data_freq[i]['time']:
            sched.add_job(self.remind_med_text, 'cron', day='*', hour=22,id=self.uid+QR_med_name,
                        start_date=QR_date, end_date=QR_date+timedelta(days=self.QR_days),
                        args=[QR_med_name])
        if 'noon1' in data_freq[i]['time']:
            dt = datetime.now()
            if (take_min<0):
                take_hour = 11
                take_min = 60 + take_min
            elif (take_hour<0):
                take_hour = 12 + take_hour
                take_min = 1
            elif (take_min>0):
                take_hour = 12
            elif (take_hour>0):
                take_hour = 12 + take_hour
                take_min = 1
            take_hour = 23
            take_min = 41
            sched.add_job(self.remind_med_text,'date', id=self.uid,
                        run_date=datetime(dt.year, dt.month, dt.day,take_hour,take_min,0),
                        args=[QR_med_name])
        if data_freq[i]['id']==4 or data_freq[i]['id']==5: #每X日一次
            sched.add_job(self.remind_med_text, 'interval', days=data_QR_freq[0]['code_number'][0],id=self.uid+QR_med_name,
                        start_date=QR_date, end_date=QR_date+timedelta(days=self.QR_days),
                        args=[QR_med_name])
        if data_freq[i]['id']==13: #每X小時使用一次
            sched.add_job(self.remind_med_text, 'interval', hours=data_QR_freq[0]['code_number'][0],id=self.uid+QR_med_name,
                        start_date=QR_date, end_date=QR_date+timedelta(days=self.QR_days),
                        args=[QR_med_name])
        if data_freq[i]['id']==14: #每X分鐘使用一次
            sched.add_job(self.remind_med_text, 'interval', minutes=data_QR_freq[0]['code_number'][0],id=self.uid+QR_med_name,#id='day_noon',
                        start_date=QR_date, end_date=QR_date+timedelta(days=self.QR_days),
                        args=[QR_med_name])
            
        if 'nn' in data_freq[i]['time']:
            sched.add_job(self.remind_med_text, 'cron', day='*',hour='*',minute='*',second=10,id=self.uid+QR_med_name,
                    start_date='2018-07-16', end_date=QR_date+timedelta(days=self.QR_days),
                    args=[QR_med_name])

    #提醒頻率-每星期
    def remind_med_week(self,i,ttt,take_hour,take_min,uid,time_week,QR_date):
        if data_freq[i]['id']==6:
            sched1.add_job(remind_med_day, 'interval', weeks=data_QR_freq[0]['code_number'][0],minutes=2,id=uid,
                    start_date=QR_date, end_date=QR_date+timedelta(days=QR_days),
                    args=[i,ttt,take_hour,take_min,uid,QR_date])
        if data_freq[i]['id']=='test':
            sched1.add_job(remind_med_day, 'interval', minutes=1,id=uid,
                    start_date='2018-07-16', end_date=QR_date+timedelta(days=QR_days),
                    args=[i,ttt,take_hour,take_min,uid,QR_date])
        else:
            if (take_min<0):
                take_hour = 11
                take_min = 60 + take_min
            elif (take_hour<0):
                take_hour = 12 + take_hour
                take_min = 1
            elif (take_min>0):
                take_hour = 12
            elif (take_hour>0):
                take_hour = 12 + take_hour
                take_min = 1
            sched1.add_job(remind_med_text, 'cron', day_of_week=time_week, hour=12+take_hour,id=uid,
                        start_date=QR_date, end_date=QR_date+timedelta(days=QR_days),
                        args=[ttt,uid])
        sched1.start()

    # #提醒頻率-每月
    def remind_med_month(self,i,ttt,take_hour,take_min,uid,QR_date):
        sched1.add_job(remind_med_day, 'interval', months=data_QR_freq[0]['code_number'][0],id=uid,
                    start_date=QR_date, end_date=QR_date+timedelta(days=QR_days),
                    args=[i,ttt,take_hour,take_min,uid])
        sched1.start()


    #傳送提醒用藥訊息
    def remind_med_text(self,QR_med_name):
        print('現在是'+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'請服用'+ QR_med_name + data_QR_freq[0]['take_msg'])
        self.line_bot_api.push_message(self.uid, TextSendMessage(text='現在是'+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'\n'+ data_QR_freq[0]['take_msg']))
        print(sched.get_jobs())