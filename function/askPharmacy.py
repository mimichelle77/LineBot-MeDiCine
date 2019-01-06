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

class askFharmacy():

    def __init__(self,line_bot_api,event):
        self.line_bot_api = line_bot_api
        self.event = event
        self.uid = event.source.user_id

    def ask(self):
        self.line_bot_api.push_message('Ued59e2c55678701d42ebafc60a3b50ea',TextSendMessage(text='病人諮詢，ID:'))
        self.line_bot_api.push_message('Ued59e2c55678701d42ebafc60a3b50ea',TextSendMessage(text=self.uid))
        self.line_bot_api.push_message('Ued59e2c55678701d42ebafc60a3b50ea',TextSendMessage(text='用藥成分:\nTHEOPHYLLINE\nATENOLOL\nFENOFIBRATE\nALPRAZOLAM'))