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

    def create_vlan(self, physical_interface, vlan_ids):
        try:
            for vlan_id in vlan_ids:
                command = f"add interface {physical_interface} vlan {vlan_id}"
                self.send_shell(command)
                time.sleep(1)
                self.send_shell('save config')
                time.sleep(2)
                print(f"VLAN {vlan_id} added successfully to interface {physical_interface}.")
        except Exception as e:
            print(f"Error occurred while creating VLAN: {e}")

    def create_route(self, destination_network, via=None, gateway=None):
        try:
            if via and gateway:
                # Both via and gateway are present
                command = f"set static-route {destination_network} nexthop gateway logical {via} on"
            elif via:
                # Only via is present
                command = f"set static-route {destination_network} nexthop gateway logical {via} on"
            elif gateway:
                # Only gateway is present
                command = f"set static-route {destination_network} nexthop gateway address {gateway} on"
            else:
                #Neither via nor gateway is present
                print("Neither via nor gateway provided.")
                return
        
            self.send_shell(command)
            time.sleep(1)
            self.send_shell('save config')
            print(f"Route to {destination_network} configured successfully.")
        except Exception as e:
            print(f"Error occurred while configuring route: {e}")

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
        if line.startswith("C") or line.startswith("S"):
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

def parse_gaia_route_output(output):
    routes = []
    lines = output.split("\n")
    for line in lines:
        if line.startswith("C") or line.startswith("S"):
            fields = line.split(",")
            protocol = fields[0].strip()  # Protocol type (C or S)
            destination = fields[1].split()[1].strip() if "via" in fields[1] else fields[1].strip()
            via = fields[1].split()[2].rstrip(',') if "via" in fields[1] else "directly"

            interface = next((part.strip() for part in fields if part.startswith("eth")), None)
            if not interface:  # If no part starts with "eth", then check the last part (just in case).
                interface = fields[-1].strip() if fields[-1].startswith("eth") else None

            if interface:
                route_entry = {
                    "protocol": protocol,
                    "destination": destination,
                    "via": via,
                    "interface": interface
                }
                routes.append(route_entry)
            else:
                print(f"Could not determine interface for line: {line}")
                
    return routes


def expand_vlan_ranges(vlan_list):
    expanded = []
    for item in vlan_list:
        if '-' in item:
            start, end = item.split('-')
            expanded.extend(range(int(start), int(end) + 1))
        else:
            expanded.append(int(item))
    return expanded

def add_gaia_vlan(ip, user, password, physical_interface, vlan_list):
    connection = SSHConnection(ip, user, password)
    connection.open_shell()
    time.sleep(1)
    
    expanded_vlans = expand_vlan_ranges(vlan_list)
    connection.create_vlan(physical_interface, expanded_vlans)
    connection.close_connection()

def remove_gaia_vlan(ip, user, password , physical_interface, vlan_id):
    connection = SSHConnection(ip, user, password)
    connection.open_shell()
    time.sleep(1)
    connection.send_shell(f'delete interface {physical_interface} vlan {vlan_id}')
    connection.send_shell('save config')
    connection.close_connection()

def add_gaia_route(ip, user, password, destination_network, via=None, gateway=None):
    connection = SSHConnection(ip, user, password)
    connection.open_shell()
    time.sleep(1)
    
    # Call the create_route method with appropriate parameters
    if via and gateway:
        connection.create_route(destination_network, via=via, gateway=gateway)
    elif via:
        connection.create_route(destination_network, via=via)
    elif gateway:
        connection.create_route(destination_network, gateway=gateway)
    else:
        print("Neither via nor gateway provided. Route configuration failed.")
    
    connection.close_connection()

def remove_gaia_route(ip,user,password,destination_network):
    connection = SSHConnection(ip,user, password)
    connection.open_shell()
    time.sleep(1)
    connection.send_shell(f'set static-route {destination_network} off')
    connection.send_shell('save config')
    connection.close_connection()

if __name__ == "__main__":
    gaia_ip = "10.169.32.178"
    gaia_username = "admin"
    gaia_password = "iolredi8"

    #adding vlan+route to test
    #add_gaia_vlan(gaia_ip, gaia_username, gaia_password, "eth0", 18)
    #add_gaia_route(gaia_ip, gaia_username, gaia_password, "192.168.2.0/24", "10.169.32.2")
    
    #remove vlan+route to test
    remove_gaia_route(gaia_ip,gaia_username,gaia_password,"192.168.2.0/24")
    remove_gaia_vlan(gaia_ip, gaia_username, gaia_password, "eth0", 18)

    gaia_interface_info = get_gaia_interface_info(gaia_ip, gaia_username, gaia_password)
    gaia_route_info = get_gaia_route_info(gaia_ip, gaia_username, gaia_password)

    interface_dict = json.loads(gaia_interface_info)
    route_dict = json.loads(gaia_route_info)
    combined_data = {"interfaces": interface_dict, "routes": route_dict}
    json_data = json.dumps(combined_data, indent=4)
    print(json_data)