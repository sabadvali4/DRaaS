import paramiko
import time, re
import json
class SSHConnection:
    shell = None
    client = None
    transport = None

    def __init__(self, address, username, password):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        self.client.connect(address, username=username, password=password, look_for_keys=False)

    def close_connection(self):
        if self.client is not None:
            self.client.close()

    def open_shell(self):
        self.shell = self.client.invoke_shell()

    def exec_command(self, command):
        _, ssh_stdout, ssh_stderr = self.client.exec_command(command)
        err = ssh_stderr.readlines()
        return err if err else ssh_stdout.readlines()

    def send_shell(self, command):
        if self.shell:
            return self.shell.send(command + "\n")
        else:
            print("Shell not opened.")

    def create_vlan(self, vlan_id, vlan_name):
        commands = [
            "vlan database",
            f"vlan {vlan_id} name {vlan_name}",
            "exit"
        ]
        for cmd in commands:
            self.send_shell(cmd)
            time.sleep(1)
    
    def get_vlans(self):
        ssh_stdout = self.exec_command('show vlan brief')
        switch_vlans_list = []
        for vlan in ssh_stdout:
            match = re.findall("^\d+", vlan)
            if match:
                switch_vlans_list.append(match[0])
        return switch_vlans_list

def get_gaia_interface_info(ip, user, password):
    #Login by ssh
    connection = SSHConnection(ip, user, password)
    time.sleep(1)
    #Send command and get output
    output = connection.exec_command('show interfaces all')
    #Join it to one str
    output_str = '\n'.join(output)

    #Sent to another function and parse it to Json format
    parsed_data = parse_gaia_output(output_str)
    json_data = json.dumps(parsed_data, indent=4)
    
    connection.close_connection()
    return json_data

def parse_gaia_output(output):
    interfaces = {}
    current_interface = None
    # Split the output by interface sections
    sections = output.split("\n\n\n\n\n\n")

    for section in sections:
        lines = section.strip().split("\n")
        if not lines:
            continue
        current_interface = lines[0].split()[-1]
        interfaces[current_interface] = {}

        for line in lines[1:]:
            key_value = line.strip().split(maxsplit=1)
            if len(key_value) == 2:
                key, value = key_value
                interfaces[current_interface][key] = value
    return interfaces

def get_gaia_route_info(ip, user, password):
    connection = SSHConnection(ip, user, password)
    time.sleep(1)
    # Send command to get route information
    output = connection.exec_command('show route')
    # Join the output to form a string
    output_str = '\n'.join(output)

    # Parse the output to JSON format
    parsed_data = parse_gaia_route_output(output_str)
    json_data = json.dumps(parsed_data, indent=4)
    
    connection.close_connection()
    return json_data

def parse_gaia_route_output(output):
    routes = []
    lines = output.split("\n")
    for line in lines:
        # Check if the line starts with "C" indicating a connected route
        if line.startswith("C"):
            fields = line.split()
            if len(fields) >= 6:
                route_entry = {
                    "protocol": fields[0],      # Protocol type (C for connected)
                    "destination": fields[1],   # Destination network
                    "via": fields[3],           # Next hop or directly connected
                    "interface": fields[5]      # Interface
                }
                routes.append(route_entry)
    return routes

def add_gaia_vlan(ip, user, password, vlan_id, vlan_name):
    connection = SSHConnection(ip, user, password)
    connection.open_shell()
    time.sleep(1)
    
    connection.create_vlan(vlan_id, vlan_name)
    
    vlans = [(vlan_id, vlan_name)]
    for vlan in vlans:
        if vlan[0] in connection.get_vlans():
            print(f"Created: {vlan[1]}-{vlan[0]}")
        else:
            print(f"VLAN: {vlan[0]} wasn't created")

def add_gaia_route(ip, user, password, destination, next_hop):
    connection = SSHConnection(ip, user, password)
    time.sleep(1)
    output = connection.add_route(destination, next_hop)
    connection.close_connection()
    return '\n'.join(output)

if __name__ == "__main__":
    gaia_ip = "172.16.18.113"
    gaia_username = "user"
    gaia_password = "password"

    gaia_interface_info = get_gaia_interface_info(gaia_ip, gaia_username, gaia_password)
    #print("interfaces" + gaia_interface_info)
    gaia_route_info = get_gaia_route_info(gaia_ip, gaia_username, gaia_password)
    #print("routes" + gaia_route_info)

    interface_dict = json.loads(gaia_interface_info)
    route_dict = json.loads(gaia_route_info)
    combined_data = {"interfaces": interface_dict, "routes": route_dict}
    json_data = json.dumps(combined_data, indent=4)
    print(json_data)
