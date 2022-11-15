NULL = 0
import settings
import requests
import json
import os
# parameters from .ini file
# date support
from datetime import datetime
# SSH support
import paramiko
from dotenv import load_dotenv

load_dotenv()



def run_command_on_device_wo_close(ip_address, username, password, command, sshClient=None):
    """ Connect to a device, run a command, and return the output."""
    # Load SSH host keys.
    if sshClient == None:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        # Add SSH host key when missing.
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:
        ssh = sshClient

    if 'DEFAULT' in settings.config:
        total_attempts = int(settings.config['DEFAULT']['total_ssh_attempts'])
    else:
        total_attempts = 1

    for attempt in range(total_attempts, settings.debug_level):
        try:
            if settings.debug_level > 5:
                print("Attempt to connect: %s" % attempt)
            # Connect to router using username/password authentication.
            ssh.connect(ip_address,
                        username=username,
                        password=password,
                        look_for_keys=False)
            # Run command.
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command)
            # Read output from command.
            output = ssh_stdout.readlines()
            # Close connection.
            # W/o close =># ssh.close()
            return output

        except Exception as error_message:
            if settings.debug_level > 2:
                print("Unable to connect")
                print(error_message)


def get_switch_ios(ip):
    """
    This function ssh with <switch_user>@ip to ip and runs 'show running config'
    """
    # TODO: fix to advance setup like https://networklessons.com/python/python-ssh
    if settings.debug_level > 0:
        print("sshing to: " + settings.switches_username + "@" + ip)
    sshClient = None
    if sshClient == None:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        # Add SSH host key when missing.
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:
        ssh = sshClient
    # login and run commands to get configuration
    #output = run_command_on_device_wo_close(ip, switches_username, switches_password, "enable", ssh)
    #if settings.debug_level > 5: print(output)
    #output = run_command_on_device_wo_close(ip, switches_username, switches_password, enable_password, ssh)
    #if settings.debug_level > 5: print(output)
    output = run_command_on_device_wo_close(
        ip, settings.switches_username, settings.switches_password, "terminal length 0", ssh)
    if settings.debug_level > 5:
        print(output)
    output = run_command_on_device_wo_close(
        ip, settings.switches_username, settings.switches_password, "show run", ssh)
    if settings.debug_level > 5:
        print(output)
    # Close connection.
    ssh.close()
    # write to file
    file_name = settings.base_path+"\\temp\\"+ip.replace(".", "_")+today()+".ios"
    f = open(file_name, "w")
    if output == None:
        output = ""
    else:
        for line in output:
            f.write(line.replace("\r", ""))
    f.close()


def get_JSON_from_IOS(filename):
    """
    This function transform filename_include_path_without_ext.ios to filename_include_path_without_ext.json
    """
    if settings.debug_level > 1:
        print("translate IOS to JSON for file: " + filename + ".ios")
    dissector = confparser.Dissector.from_file('ios.yaml')
    my_filename = filename+'.ios'
    myjson = str(dissector.parse_file(my_filename))
    if settings.debug_level > 15:
        print("creating File: " + my_filename +
              ".json  with data:\n" + myjson)
    with open(filename + '.json', "w") as myfile:
        myfile.write(myjson)


def send_json_to_snow(payload):
    """
    This function sends Payload(JSON file) to SNOW API
    """
    if settings.debug_level > 1:
        print("sending JSON to snow: \n" + str(payload))
    response = requests.post(settings.url, headers={
                             'Content-Type': 'application/json'}, auth=(settings.username, settings.password), json=payload)
    msg = "status is: " + str(response.status_code)
    if settings.debug_level > 1:
        print(msg)
        print(response.json())


def get_commands_from_snow(hostname=None, ip=None):
    """
    This function gets commands from snow API
    """
    commandsUrl = settings.url + "api/bdml/parse_switch_json/GETCommands"
    if (ip != None):
        myparams = {"switch_ip": str(ip)}
    if (hostname != None):
        myparams = {"hostname": str(hostname)}
    if settings.debug_level > 1:
        print("getting commands from snow: hostname:" + str(hostname))
        print("getting commands from snow: ip:" + str(ip))
        print("getting commands from url:" + str(commandsUrl))

    response = requests.get(commandsUrl, headers={
                            'Content-Type': 'application/json'}, params=myparams, auth=(settings.username, settings.password))
    msg = "status is: " + str(response.status_code)
   
    if settings.debug_level > 1:
        print(msg)
        print(response.json())
       
    if (response.status_code == 200):
        myresponse = response.json()["result"]
        if settings.debug_level > 1:
            print(myresponse["u_commands"][0]["command"])
    else:
        myresponse = response.json()
        return "error" + msg + " response " + str(response)
    send_commands_to_switch(
        myresponse["switch_ip"], myresponse["u_commands"][0]["command"])
    return myresponse["u_commands"][0]["sysid"]


def get_ips_from_snow():
    """
    This function gets list of switchs ips from snow API
    """
    commandsUrl = settings.url + 'api/bdml/parse_switch_json/SwitchIPs'
    #

    response = requests.get(commandsUrl, headers={
                            'Content-Type': 'application/json'}, auth=(settings.username, settings.password))
    msg = "status is: " + str(response.status_code)
    if settings.debug_level > 1:
        print(msg)
        print(response.json())
    myresponse = response.json()
    ips = myresponse["result"]["ips"]
    switch_username = myresponse["result"]["username"]
    switch_password = myresponse["result"]["password"]
    print(switch_username)
    print(switch_password)


def set_status_to_sent(sysid):
    """
    This function sets status to sent
    """
    commandsUrl = settings.url + 'api/bdml/parse_switch_json/CommandSent'
    if (sysid != None):
        myparams = {"sysid": str(sysid)}
    if settings.debug_level > 1:
        print("getting commands from snow: sysid:" + str(sysid))

    response = requests.get(commandsUrl, headers={
                            'Content-Type': 'application/json'}, params=myparams, auth=(settings.username, settings.password))
    msg = "status is: " + str(response.status_code)
    if settings.debug_level > 1:
        print(msg)
        print(response.json())


def send_commands_to_switch(ip, command):
    """
    This function sends commands to the switch
    """
   # get switch username and password from snow
    commandsUrl = settings.url + 'api/bdml/parse_switch_json/SwitchIPs'
    response = requests.get(commandsUrl, headers={
                            'Content-Type': 'application/json'}, auth=(settings.username, settings.password))
    myresponse = response.json()
    ips = myresponse["result"]["ips"]
    for myip in ips:
        if myip == ip:
            switch_username = myresponse["result"]["username"]
            switch_password = myresponse["result"]["password"]
            if settings.debug_level > 0:
                print("sendig command "+command+" to: " +
                      settings.switches_username + "@" + ip)
                print(switch_username)
                print(switch_password)
    sshClient = None
    if sshClient == None:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        # Add SSH host key when missing.
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:
        ssh = sshClient
    # login and run commands to get configuration
    #output = run_command_on_device_wo_close(ip, switches_username, switches_password, "enable", ssh)
    #if settings.debug_level > 5: print(output)
    #output = run_command_on_device_wo_close(ip, switches_username, switches_password, enable_password, ssh)
    #if settings.debug_level > 5: print(output)
    output = run_command_on_device_wo_close(
        ip, settings.switches_username, settings.switches_password, "terminal length 0", ssh)
    if settings.debug_level > 5:
        print(output)
    output = run_command_on_device_wo_close(
        ip, settings.switches_username, settings.switches_password, "conf t", ssh)
    if settings.debug_level > 5:
        print(output)
    commands = command.split(",")
    for mycommand in commands:
        print("sending command: " + mycommand)
        output = run_command_on_device_wo_close(
            ip, settings.switches_username, settings.switches_password, mycommand, ssh)
        if settings.debug_level > 5:
            print(output)
    output = run_command_on_device_wo_close(
        ip, settings.switches_username, settings.switches_password, "end", ssh)
    output = run_command_on_device_wo_close(
        ip, settings.switches_username, settings.switches_password, "write", ssh)
    if settings.debug_level > 5:
        print(output)
    # Close connection.
    ssh.close()


def today():
    now = datetime.now()
    date_time = now.strftime("_%m-%d-%Y-H-%H_")
    #date_time = "fix"
    return (date_time)


# run main
"""
data_json = {"hello": "world"}
payload = {'json_payload': data_json}
get_ips_from_snow()

for i in ips:
    ip=i.strip()
    print (ip)
    get_switch_ios(ip)
    filename = base_path+"\\temp\\"+ip.replace(".","_")+today()
    get_JSON_from_IOS(filename)
    JSON_file_name = base_path+"\\temp\\"+ip.replace(".","_")+today()+".JSON"
    f = open( JSON_file_name , "r")
    data_json = f.readlines()
    f.close()
    json = ''
    for line in data_json:
        json += line #.replace("\n","").replace('\"','"')
    #data_json = {"hello": "world"}
    payload = {'json_payload': json}
    
    send_json_to_snow(payload) 
"""


def run():
   get_commands_from_snow(hostname='YanirServer')
    #send_commands_to_switch(ip="10.10.20.48", command="hostname yanir")


if __name__ == "__main__":
    run()
