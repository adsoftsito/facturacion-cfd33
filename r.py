# encoding: utf-8
from flask import Flask
from facturacion_moderna import facturacion_moderna
from datetime import datetime, timedelta
import base64
from M2Crypto import RSA
from lxml import etree as ET
import hashlib
import os

app = Flask(__name__)

@app.route('/')
def hello_world():
  return 'cfdi 33 OK'
