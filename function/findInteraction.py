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
from linebot import *
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

client = MongoClient('localhost',27017)
db = client["MeDiCine"]
collectionPI = db["Patient-Info"]
collectionMD = db["medicine-dict"]

app = Flask(__name__)

class Interaction():

    def __init__(self,line_bot_api,event):
        self.line_bot_api = line_bot_api
        self.event = event
        self.uid = event.source.user_id

    def findInteraction(self,QRresault):
        resault = collectionPI.find_one({'身分證字號':QRresault['身分證字號']})
        ingredientall = []
        if(resault != None):
            for md in QRresault['用藥']:
                for ingredient in md['成分']:
                    ingredientall.append(ingredient)
            for md in resault['用藥']:
                for ingredient in md['成分']:
                    ingredientall.append(ingredient)
            options = webdriver.FirefoxOptions()
            options.add_argument("--headless")
            driver = webdriver.Firefox(firefox_options=options)
            driver.get("https://www.webmd.com/interaction-checker/default.htm")

            time.sleep(1)

            for i in range(len(ingredientall)):
                if(i > 1):
                    driver.find_element_by_class_name("add-another").click()
                ingredientall[i] = ingredientall[i].split(' ')[0]
                time.sleep(1) 
                driver.find_element_by_id("ICDrugs-" + str(i+1)).send_keys(ingredientall[i])
                time.sleep(1)
                li= driver.find_element_by_id("ICDrugs-" + str(i+1)).get_attribute("aria-owns")
                time.sleep(1)
                driver.find_element_by_id(li + "-option-0").click()

            driver.find_element_by_id("check-interaction").click()
            time.sleep(1)
            Interaction = driver.find_element_by_css_selector(".interaction-count.ng-binding").text
            driver.close()

        if(Interaction == '0'):
            self.line_bot_api.push_message(self.uid, TextSendMessage(text='您服用的藥物沒有交互作用'))
        else:
            self.line_bot_api.push_message(self.uid, TextSendMessage(text=('您服用的藥物存在交互作用,如有疑慮,請與藥師洽詢')))
            confirm= TemplateSendMessage(
                alt_text='藥師洽詢',
                template=ConfirmTemplate(
                    title='藥師洽詢',                
                    text='是否要與藥師洽詢？',
                    actions=[
                        PostbackTemplateAction(
                            label='是',
                            text='是',
                            data='action=askpharmacy&status=yes'
                        ),
                        PostbackTemplateAction(
                            label='否',
                            text='否',
                            data='action=askpharmacy&status=no'
                        )
                    ])
            )
            self.line_bot_api.push_message(self.uid,confirm)
