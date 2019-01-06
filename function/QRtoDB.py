# -*- coding: utf-8 -*-

from flask import Flask, request, abort
import tempfile, os,shutil, time
import requests
from bs4 import BeautifulSoup
import json
from os import path
from pymongo import MongoClient
import collections
from collections import OrderedDict
from selenium import webdriver


client = MongoClient('localhost',27017)
db = client["MeDiCine"]
collectionPI = db["Patient-Info"]
collectionMD = db["medicine-dict"]
static_tmp_path = os.path.dirname(__file__)

app = Flask(__name__)

class QRtoDB():

    def __init__(self):
        pass

    def decode_QR(self,line_bot_api,event):
            userId=event.source.user_id
            ext = 'jpg'
            message_content = line_bot_api.get_message_content(event.message.id)
            with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
                for chunk in message_content.iter_content():
                    tf.write(chunk)
                tempfile_path = tf.name
            fo = open(tempfile_path,'rb')
            file={'qrcode':fo}
            compile_url="https://zxing.org/w/decode"
            response = requests.post(compile_url,files=file)
            response.encoding='utf-8'
            head=response.text.find("<pre>")
            last=response.text.find("</pre>")
            rawBytes=response.text[head+5:last]
            fo.close()
            if(rawBytes[0:5]=="CTYPE"):
                rawBytes="Error"
                return u"無法辨識這張處方籤上的QRCODE哦，請再拍得更清晰些。"

            if(rawBytes!="CTYPE"):
                In_data=OrderedDict()
                In_data['userId']=userId

                arr_data = rawBytes.split(';')
        

                In_data['處方類別']=arr_data[1]
                In_data['病患姓名']=arr_data[3]
                In_data['出生日期']=arr_data[5]
                In_data['身分證字號']=arr_data[4]
                In_data['就醫日期']=arr_data[7]
                In_data['給藥日份']=arr_data[9]
                In_data['用藥']=[]

                for i in range(14,len(arr_data)-1,5):
                    options = webdriver.FirefoxOptions()
                    options.add_argument("--headless")
                    driver = webdriver.Firefox(firefox_options=options)
                    driver.get("https://www.nhi.gov.tw/QueryN/Query1.aspx")
                    driver.find_element_by_id("ctl00_ContentPlaceHolder1_tbxQ1ID").send_keys(arr_data[i])
                    time.sleep(0.5)
                    driver.find_element_by_id("ctl00_ContentPlaceHolder1_btnSubmit").click()
                    time.sleep(0.5)
                    MDname = driver.find_element_by_id("ctl00_ContentPlaceHolder1_gvQuery1Data_ctl02_lblNameChinese").text
                    driver.close()


                    compile_url="https://www.nhi.gov.tw/QueryN/Query1.aspx"
                    form_data = {"__VIEWSTATE": "/9+WDrlyaJCi1s6Crmc+q0SyGNpFpzizClB2iGPjcQQxuCXwFCDkROtZ1k88ldmTG12jUKzHGfIPhgUvPpC/GSpUg6SsWVY504jxLZc9FubKqKyGsJuXMgTiCQC3PWv2QDb8Et2Sl9HFmCkPd0B49kAp85hLZ08Vd8cdWMe0c6SdQVKo/k85xJv9SnfZm3bvcXituCpQaWWU10H/J+oQB2mAlOTMc+6sUH8w8ByIX7loJUOalQEpt7Mj0/SiF+jMr4AbLnBSRQui7298gavS6tsvx7LnK0XJq0yzBmbYyBjf6gpZrNQA7ffZyYkjt9xcV8w0Sesv7fVVyN14RBEFWGBtMVJa571dmM4yk1qraRk68vtGCh2Sq+hFUgVeW6yiueaNw/KdBFQ667g8KldFyVn/C/B6pZJu+5tq2EQSWodheTCaBagH0DrGjvh5/GVOZEBAUtTEMKyQOi3K+0e2cJLiVW/s8DoE/lI6hn+1J49XyEKR7Yx/dBNQfFyxpF9SM31NPImNyGf+hNaqHTpEmrxd3NAsLUKAU2fixaxuSq8FNIVCc+H5Gc9WfL/2C8iX2WR1j5H4hex4/c23kinSMdYeVUKflUHJPNBELwAF5D8+ceAyi9gMHcXE4RwOGiZRn+Wy49Fbm8WjyP5QqU9nIO56F1h4tZ9OjWyOc5n9Ow5jnqrrp9exd/B1+pEUG4qTFmurW5cT4DJDWTQm+Z6Y8vj400PTAQGCix6OSuEWyPPRfKIqnGPjszwwRxDfCcUyEbpFxLrTS1NzPh6P+EMp4JZWK3NokZX5z8mNQDUrL6Y3ysI6MS9ablSsVhZVDbD2TDF+sqfcEagIUvtuQQKKPmBgrqbiig9huNS1OCOz5ugr+/Lvw7MIBffWU9XU7KhLCb9uuyYhJ212NqoiDjoxaKi8KNGBXEE2znoohNvqlIvgzi3U50B0060148bRQUM9D9Z1lE0dXTa/G6aCfqwZQBfX9t14tQvDC5OvMP7K3djtPAn58gmJsfPKWUXjIU6Ja+v8BNfFhKJQS9ef31HUe0t771yy/3qIMqePUQWNFe42YdXrNeLMl7q6AeotdGUXoc44xenfIC21lofoNfZTqi8QC9V8D3+hPCC5EzIUTIQb/WdW7CSRm0OXBeEr17PNsjkDwSP3MKlkgQ85M3rZNA1/i53Yu8Za+duSz53JHcKYLbx7lYedxvUIRomdrbi5LmADigodUZUXcDyxyXKI2V28e+opq22oAU0yxW/Yy4bo+vrgWBx4Kgrc/aFPNL7Fr7BG/7SLv3ecCo3rMX1tzQKSyuysunbzkUSt+w+k9eA2VcdKvRwiiuJpw7wnNt5aCqAT1bytFUnCF7NOKWq0qqW9LWoyPAS2d4Ha5Mmi5cGuWLlOtlJ/J72faOfS5lhC7urdpNsly+wngPTuIq0oQgfsyCoEhFE2NV7AVDa0fUJ/BfopbDGAiI6Ws3d/1GRZ",
                                "__VIEWSTATEGENERATOR": "D47A3E17",
                                "__SCROLLPOSITIONX": "0",
                                "__SCROLLPOSITIONY": "0",
                                "__EVENTTARGET": "",
                                "__EVENTARGUMENT": "",
                                "__VIEWSTATEENCRYPTED": "",
                                "ctl00$ContentPlaceHolder1$tbxQ1ID": arr_data[i],
                                "ctl00$ContentPlaceHolder1$rblType": "迄今",
                                "ctl00$ContentPlaceHolder1$tbxPageNum": "10",
                                "ctl00$ContentPlaceHolder1$btnSubmit": "開始查詢"}
                    response = requests.post(compile_url,data=form_data)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    MDname = soup.find(id='ctl00_ContentPlaceHolder1_gvQuery1Data_ctl02_lblNameChinese')

                    ingredient =[]
                    if(arr_data[i][0] == 'A'):
                        MDlicense = u"衛署藥製字第0" + arr_data[i][2:7] + u"號"
                    elif(arr_data[i][0] == 'B'):
                        MDlicense = u"衛署藥輸字第0" + arr_data[i][2:7] + u"號"
                    elif(arr_data[i][0] == 'N'):
                        MDlicense = u"內衛藥製字第0" + arr_data[i][2:7] + u"號"
                    elif(arr_data[i][0] == 'P'):
                        MDlicense = u"內衛藥輸字第0" + arr_data[i][2:7] + u"號"
                    for ing in collectionMD.find({"許可證字號":MDlicense}):
                        ingredient.append(ing['成分名稱'])

                    In_data['用藥'].append(OrderedDict([('藥品代號', arr_data[i]),('藥品名稱',MDname),('成分',ingredient),('藥品用量', arr_data[i+1]), ('用藥頻率', arr_data[i+2]),
                                                ('途徑', arr_data[i+3]),('總數量', arr_data[i+4])]) )
                os.remove(tempfile_path)
                resault = collectionPI.find_one(In_data)
                if(resault == None):
                    collectionPI.insert_one(In_data)
                    return In_data
                else:
                    return None