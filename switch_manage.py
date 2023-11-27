import paramiko
import time, re

class ssh_con:
    shell = None
    client = None
    transport = None

    def __init__(self, address, username, password):
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

def get_vlans(ip, user, password):
    connection = ssh_con(ip, user, password)
    time.sleep(1)

    ssh_stdout = connection.exec_command('show vlan brief')
    
    switch_vlans_list = []
    for vlan in ssh_stdout:
        if re.findall("^\d+", vlan) != []:
            switch_vlans_list.append(re.findall("^\d+", vlan)[0])
    
    return switch_vlans_list

def create_vlan(ip, user, password, vlans):
    connection = ssh_con(ip, user, password)
    connection.open_shell()
    time.sleep(1)

    connection.send_shell("vlan database")
    time.sleep(1)
    for vlan in vlans:
        try:
            connection.send_shell(f"vlan {vlan[0]} name {vlan[1]}")
            time.sleep(1)
        except Exception as error:
            print(f"Failed to create vlan: {error}")

    time.sleep(1)
    connection.send_shell("exit")
    time.sleep(1)

    for vlan in vlans:
        if vlan[0] in get_vlans(ip, user, password):
            print(f"created: {vlan[1]}-{vlan[0]}")
        else:
            print(f"vlan: {vlan[0]} wasn't created")