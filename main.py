#!/usr/bin/env python3

from curses.ascii import NUL
from zipfile import ZIP_BZIP2
import requests
import json
# parameters from ENV
from dotenv import load_dotenv   #for python-dotenv method
load_dotenv()                    #for python-dotenv method
import os 
# parameters from .ini file
import configparser
#date support
from datetime import datetime
#SSH support
import paramiko

debug_level = 0
config = configparser.ConfigParser()
config.sections()
config.read('./config/parameters.ini')






if 'DEFAULT' in config :
  debug_level = int(config['DEFAULT']['debug_level']  )  
else:
  debug_level = 0

if "DEFAULT" in config :
  url = config["DEFAULT"]['Url']    
else:
  url = "https://bynetdev.service-now.com/api/bdml/parse_switch_json/DRaaS/ParseSwitch"

if "DEFAULT" in config :
  username = config['DEFAULT']['username']    
else:
  username = os.environ.get('USER')

if "DEFAULT" in config :
  password = config['DEFAULT']['password']    
else:
  password = os.environ.get('password')

if "DEFAULT" in config :
    base_path = config['DEFAULT']['basepath']    
else:
    base_path = "."

if "DEFAULT" in config :
  enable_password = config['DEFAULT']['enable_password']    
else:
  enable_password = os.environ.get('enable_password')  

if "SWITCHES" in config :
  ips = config['SWITCHES']['ips'].split(",") 
  switches_username = config['SWITCHES']['username']  
  switches_password = config['SWITCHES']['password'] 
else:
  ips = os.environ.get('ips').split(",")
  switches_username = os.environ.get('switches_username')
  switches_password = os.environ.get('switches_password')



#define functions


def run_command_on_device_wo_close(ip_address, username, password, command, sshClient = NUL):
    """ Connect to a device, run a command, and return the output."""
    # Load SSH host keys.
    if sshClient == NUL:
      ssh = paramiko.SSHClient() 
      ssh.load_system_host_keys()
      # Add SSH host key when missing.
      ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:
      ssh = sshClient    

    if 'DEFAULT' in config :
       total_attempts = int( config['DEFAULT']['total_ssh_attempts'])    
    else:
       total_attempts = 1

    for attempt in range(total_attempts):
        try:
            if debug_level > 5:
              print("Attempt to connect: %s" % attempt)
            # Connect to router using username/password authentication.
            ssh.connect(ip_address, 
                        username=username, 
                        password=password,
                        look_for_keys=False )
            # Run command.
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command)
            # Read output from command.
            output = ssh_stdout.readlines()
            # Close connection.
            #W/o close =># ssh.close()
            return output

        except Exception as error_message:
            if debug_level > 2:
              print("Unable to connect")
              print(error_message)


def get_switch_ios(ip):
    """
    This function ssh with <switch_user>@ip to ip and runs 'show running config'
    """
    #TODO: fix to advance setup like https://networklessons.com/python/python-ssh
    if debug_level > 0:
      print("sshing to: " + switches_username + "@"+ ip)
    sshClient = None
    if sshClient == None:
      ssh = paramiko.SSHClient() 
      ssh.load_system_host_keys()
      # Add SSH host key when missing.
      ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:
      ssh = sshClient
    #login and run commands to get configuration      
    output = run_command_on_device_wo_close(ip, switches_username, switches_password, "enable", ssh)
    output = run_command_on_device_wo_close(ip, switches_username, switches_password, enable_password, ssh)
    output = run_command_on_device_wo_close(ip, switches_username, switches_password,"terminal length 0",ssh)
    output = run_command_on_device_wo_close(ip, switches_username, switches_password,"show run",ssh)
    # Close connection.
    ssh.close()
    #write to file
    file_name = base_path+"\\temp\\"+ip.replace(".","_")+today()+".ios"
    f = open( file_name , "w")
    if output == None:
        output = ""
    f.write(output)
    f.close()

def get_JSON_from_IOS(filename):
    """
    This function transform filename.ios to filename.json
    """
    if debug_level > 0:
      print("translate IOS to JSON for file: " + filename)
  
def send_json_to_snow(payload):
    """
    This function sends Payload(JSON file) to SNOW API
    """
    if debug_level > 1:
      print("sending JSON to snow: \n" + payload)
    response = requests.post(url,headers={'Content-Type':'application/json'}, auth=(username, password), json=payload)
    msg = "status is: " + str(response.status_code)
    if debug_level > 1:
      print( msg)
      print(response.json())

def today():
    now = datetime.now()
    date_time = now.strftime("_%m-%d-%Y-H-%H_")
    if int(debug_level) > 8:
      print("date and time:",date_time)
    return(date_time)  

#show params if debug >8

if int(debug_level) > 8:
  print("Today:", today(),"\n")  
  print("url: ", url ,"\n")
  print("username: ",username,"\n")
  print("password: ",password,"\n")
  print("Switches IP", ips,"\n")

# run main

data_json = {"hello": "world"}
payload = {'json_payload': data_json}

for i in ips:
    ip=i.strip()
    get_switch_ios(ip)
    filename = base_path+"\\temp\\"+ip.replace(".","_")+today()+".ios"
    get_JSON_from_IOS(filename)
    payload = base_path+"\\temp\\"+ip.replace(".","_")+today()+".JSON"
    #send_json_to_snow(payload)