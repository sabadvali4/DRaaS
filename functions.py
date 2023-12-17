import time, sys, threading; from unittest import result; import requests, json, re, os
from datetime import datetime; import paramiko, configparser, confparser; from ntc_templates.parse import parse_output
from netmiko import ConnectHandler; import json
from dotenv import load_dotenv; from socket import *
#import glv; from glv import added_vlan  # Import the added_vlan list
global added_vlan
added_vlan=[]
load_dotenv()

config = configparser.ConfigParser()
config.sections()
config.read('./config/parameters.ini')

#SSH connection function
class SSHClient:
    def __init__(self, address, username, password):
        print("Connecting to server on IP", str(address) + ".")
        self.connection_params = {
            'device_type': 'cisco_ios',
            'ip': address,
            'username': username,
            'password': password,
        }
        self.connection = None

    def connect(self):
        self.connection = ConnectHandler(**self.connection_params)
        self.connection.enable()

    def close_connection(self):
        if self.connection:
            self.connection.disconnect()

    def exec_command(self, command, use_textfsm=False, expect_string=None):
        if self.connection:
            if use_textfsm:
                output = self.connection.send_command(command, use_textfsm=True, expect_string=expect_string)
            else:
                output = self.connection.send_command(command, expect_string=expect_string)
            return output
        else:
            raise ValueError("SSH connection is not established.")
#SSH connection function
class ssh_new:
    shell = None
    client = None
    transport = None

    def __init__(self, address, username, password):
        print("Connecting to server on ip", str(address) + ".")
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        self.client.connect(address, username=username, password=password, look_for_keys=False)

    def close_connection(self):
        if(self.client != None):
            self.client.close()

    def open_shell(self):
        self.shell = self.client.invoke_shell()


    def exec_command(self, command):
        _, ssh_stdout, ssh_stderr = self.client.exec_command(command)
        err = ssh_stderr.readlines()
        return err if err else ssh_stdout.readlines()

    def send_shell(self, command):
        if(self.shell):
            return self.shell.send(command + "\n")
        else:
            print("Shell not opened.")

def run_command_and_get_json(ip_address, username, password, command):
    # Create an instance of the SSHClient class
    ssh_client = SSHClient(ip_address, username, password)
    try:
        # Establish the SSH connection
        ssh_client.connect()
        if 'show run' in command:
            output = ssh_client.exec_command(command)
            parsed_data = confparser.Dissector.from_file('ios.yaml').parse_str(output)
            json_data = json.dumps(parsed_data, indent=4)
        else:
            output = ssh_client.exec_command(command, use_textfsm=True)
            json_data = json.dumps(output, indent=2)

        return json_data

    except (paramiko.AuthenticationException, paramiko.SSHException) as error:
        # Raise an exception if there is an error during the connection
        raise error

    finally:
        # Close the SSH connection when done
        ssh_client.close_connection()

def is_json(myjson):
  try:
    json.loads(str(myjson))
  except ValueError as e:
    return False
  return True

def get_interfaces_mode(ip_address, username, password, interfaces, sshClient=None):
    interfaces_mode = []
    for interface in interfaces:
        command = "show int " + interface + " switchport | include Administrative Mode:"
        response = run_command_and_get_json(ip_address, username, password,command, sshClient)[0]
        interface_mode = str(response.replace("\n", "").replace("\r", "").replace("Administrative Mode: ", ""))
        interface_mode = {
            'interface': interface,
            'mode': interface_mode
        }
        interfaces_mode.append(interface_mode)
    return interfaces_mode

def check_privileged_connection(connection):
    """
    Check if the SSH connection is privileged.
    """
    buffer_size = 4096
    def flush(connection):
        while connection.shell.recv_ready():
            connection.shell.recv(buffer_size)
    def get_prompt(connection):
        flush(connection)  # flush everything from before
        connection.shell.sendall('\n')

        time.sleep(.3)
        data = str(connection.shell.recv(buffer_size), encoding='utf-8').strip()
        flush(connection)  # flush everything after (just in case)

        return data
    prompt = get_prompt(connection)
    return True if prompt[-1] == '#' else False

def check_vlan_exists(ip_address, username, password, vlan_id):
    response = run_command_and_get_json(ip_address, username, password, f'show vlan id {vlan_id}')
    if "not found in current VLAN database" in response:
        print(f"VLAN {vlan_id} not found. Creating the VLAN...")
        create_vlan_command = f'vlan {vlan_id}'
        run_command_and_get_json(ip_address, username, password, create_vlan_command)
        print(f"VLAN {vlan_id} created.")
        added_vlan.append(vlan_id)  # Append the VLAN ID to the list of added VLANs in glv
        return True
    else:
        print(f"VLAN {vlan_id} already exists.")
        return True  # The VLAN exists

def change_interface_mode(ip_address, username, password, interface, mode, vlan_range, enable_pass=None):
    """
    Change the mode of a network interface on a switch.
    """
    connection = ssh_new(ip_address, username, password)
    try:
        connection.open_shell()
        time.sleep(1)

        if not check_privileged_connection(connection):
            if enable_pass is not None:
                connection.send_shell('enable')
                time.sleep(1)
                connection.send_shell(enable_pass)
                time.sleep(1)
            else:
                raise ValueError('enable_pass is missing, and SSH connection is not privileged')

        connection.send_shell('conf terminal')
        time.sleep(1)
        connection.send_shell(f'interface {interface}')
        time.sleep(1)

        # Remove any existing configuration related to the opposite mode
        if mode == 'trunk':
            connection.send_shell('no switchport access vlan')
            connection.send_shell('no switchport mode access')
            connection.send_shell('switchport trunk encapsulation dot1q')
            connection.send_shell('switchport mode trunk')
            
            vlan_ids = []

            for vlan_group in vlan_range.split(','):
                if "-" in vlan_group:
                    start_vlan, end_vlan = map(int, vlan_group.split('-'))
                    vlan_ids.extend(range(start_vlan, end_vlan + 1))
                else:
                    vlan_ids.append(int(vlan_group))

            for vlan_id in vlan_ids:
                if check_vlan_exists(ip_address, username, password, vlan_id) == False:
                    raise ValueError(f'VLAN {vlan_id} is missing in device configuration')
                connection.send_shell(f'switchport trunk allowed vlan add {vlan_id}')
            
            print(f'Interface {interface} mode changed to trunk, allowed VLANs: {vlan_range}')
        elif mode == 'access':
            connection.send_shell('no switchport trunk encapsulation dot1q')
            connection.send_shell('no switchport mode trunk')
            
            if "-" in vlan_range:
                raise ValueError("VLAN range is not supported in access mode")
            elif vlan_range:
                vlan_id = int(vlan_range)
                if check_vlan_exists(ip_address, username, password, vlan_id) == False:
                    raise ValueError(f'VLAN {vlan_id} is missing in device configuration')
                connection.send_shell(f'switchport access vlan {vlan_id}')
            
            print(f'Interface {interface} mode changed to access, VLAN: {vlan_range}')
            connection.send_shell('no switchport trunk allowed vlan')  # Remove trunk allowed VLANs
        
        connection.send_shell('exit')
        connection.send_shell('exit')
        connection.send_shell('write memory')  # Save the configuration to memory
        time.sleep(10)  # Give it some time to save the configuration
        connection.close_connection()

    except (paramiko.AuthenticationException, paramiko.SSHException) as error:
        # Raise an exception if there is an error during the connection
        raise error

