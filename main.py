# -*- coding: utf-8 -*-

from flask import Flask, request, abort
import tempfile, os,shutil, re
import requests
import json
from os import path
from pymongo import MongoClient
import collections
from collections import OrderedDict
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,ImageMessage,
)
from function.QRtoDB import QRtoDB
from function.remindTake import *
from function.remindReturn import *
from function.findInteraction import Interaction
from function.askPharmacy import *
from function.locationPh import *
import config

static_tmp_path = os.path.join(os.path.dirname(__file__),'temp')

app = Flask(__name__)

line_bot_api = LineBotApi(config.LineBotApi)
handler = WebhookHandler(config.WebhookHandler)

@app.route("/callback", methods=['POST'])
def index():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(PostbackEvent)
def handle_post_message(event):
    pos = parse_qs(event.postback.data)
    if(pos['action'][0]  == 'askpharmacy'):
        if(pos['status'][0] =='yes'):
            line_bot_api.push_message(event.source.user_id,TextSendMessage(text='已將您的問題傳送給藥師，請靜候回復，謝謝'))
            askFharmacy(line_bot_api,event).ask()
        elif(pos['status'] =='no'):
            line_bot_api.push_message(event.source.user_id,TextSendMessage(text='好的，請記得按時服藥'))
    if(pos['action'][0]  == 'endDate_Num'):
        line_bot_api.push_message(event.source.user_id,TextSendMessage(text='好的，我會提醒您領藥'))
        if(pos['status'][0] =='2'):
            pass
        elif(pos['status'] =='3'):
            pass

@handler.add(MessageEvent, message=(TextMessage,ImageMessage,LocationMessage))
def handle_message(event):
    
    if isinstance(event.message, TextMessage):
        if(event.message.text.find("病人你好") >= 0):
            index = event.message.text.find("病人你好")
            patID = event.message.text[0:index]
            line_bot_api.push_message(patID,TextSendMessage(text='藥師回覆:\n'+event.message.text[index:]))
        elif(event.message.text.find("次") < 0 and event.message.text.find("是") < 0 and event.message.text.find("否") < 0):
            line_bot_api.push_message('U3ec6f7e2010e39c12cdf7a5658071e29',TextSendMessage(text='您好，我是梅德森，您個人的藥事助理。\n\n請將您處方籤上的QR碼拍照並上傳，我將會定時提醒您~'))
    elif isinstance(event.message, ImageMessage):
        
        #decode QR & insert into DB
        QRresault  = QRtoDB().decode_QR(line_bot_api,event)
        
        #show md info
        if(QRresault != None):
            rT = remindTake(QRresault,line_bot_api,event)
            for md in QRresault['用藥']:
                QR_med_name = list(md.items())[1][1]     #QR Code掃出的藥品名稱
                QR_QTY = list(md.items())[3][1]  #QR Code掃出的藥品用量
                QR_freq= list(md.items())[4][1]   #QR Code掃出的用藥頻率 'Q1MN'#'Q2D2AC1M'
                QR_route = list(md.items())[5][1]    #QR Code掃出的給藥途徑
                rT.remind_med(QR_med_name,QR_QTY,QR_freq,QR_route)

                

        #check Interaction
        Interaction(line_bot_api,event).findInteraction(QRresault)

        # #remindReturn
        remindReturn(QRresault,line_bot_api,event).endDate_Num()

    elif isinstance(event.message, LocationMessage):
        geocodingapi="AIzaSyACPkahPx9DAFXqgzaUFPk8YqyJofHNBFc"
        res=requests.get('https://maps.googleapis.com/maps/api/geocode/json?latlng='+str(event.message.latitude)+','+str(event.message.longitude)+'&key='+geocodingapi+'&language=zh-TW')
        res_geo = json.loads(res.text)
        msg =res_geo["results"][0]['formatted_address']
        msg = event.message.address
        locationPH.locationapi(msg)
        addressinfo = []
        addressinfo.append(CarouselColumn(
                    title='健康人生藥局-北投石牌店',
                    text='112台北市北投區石牌路2段187號1樓，距離你共700 公尺，走路9分鐘即可抵達',
                    actions=[
                        URITemplateAction(
                            label='Google map導航',
                            uri='https://www.google.com.tw/maps/dir/25.118110,121.520447/112台北市北投區石牌路2段187號1樓'
                        )
                    ]
                ))
        carousel_template_message = TemplateSendMessage(
        alt_text='藥局選單',
        template=CarouselTemplate(
            columns=addressinfo
        )
        )
        line_bot_api.push_message(event.source.user_id,carousel_template_message)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port= 5000)