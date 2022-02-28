#!/usr/bin/env python3

import requests
import json
import configparser

config = configparser.ConfigParser()
config.sections()
config.read('./config/parameters.ini')

if 'config['DEFAULT']['Url']' in config :
  url = config['DEFAULT']['Url']    
else:
  url = "https://bynetdev.service-now.com/api/bdml/parse_switch_json/DRaaS/ParseSwitch"

if 'config['DEFAULT']['Url']' in config :
  username = config['DEFAULT']['username']    
else:
  username = "drass_admin@gmail.com"

if 'config['DEFAULT']['password']' in config :
  password = config['DEFAULT']['password']    
else:
  password = "1234"

data_json = {"hello": "world"}
payload = {'json_payload': data_json}

response = requests.post(url,headers={'Content-Type':'application/json'}, auth=(username, password), json=payload)
msg = "status is: " + str(response.status_code)
print( msg)
print(response.json())