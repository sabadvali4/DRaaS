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

def get_interface_info(ip, user, password):
    connection = SSHConnection(ip, user, password)
    time.sleep(1)

    # Modify the command to retrieve interface information based on your device's CLI
    ssh_stdout = connection.exec_command('show interfaces')

    interface_info = []
    for line in ssh_stdout:
        # Process the output to extract relevant information
        # Modify this part based on your device's CLI output format
        match = re.match(r'Interface (.+), .*', line)
        if match:
            interface_info.append(match.group(1))

    connection.close_connection()
    return interface_info

def get_gaia_interface_info(ip, user, password):
    connection = SSHConnection(ip, user, password)
    time.sleep(1)

    # Modify the command to retrieve interface information based on Gaia CLI
    ssh_stdout = connection.exec_command('show-interfaces')

    interface_info = []
    for line in ssh_stdout:
        # Process the output to extract relevant information
        # Modify this part based on Gaia CLI output format
        match = re.match(r'Interface (.+), .*', line)
        if match:
            interface_info.append(match.group(1))

    connection.close_connection()
    return interface_info

if __name__ == "__main__":
    # Example usage
    gaia_ip = "10.169.32.178"
    gaia_username = "your_gaia_username"
    gaia_password = "your_gaia_password"

    gaia_interface_info = get_gaia_interface_info(gaia_ip, gaia_username, gaia_password)
    print(json.dumps(gaia_interface_info, indent=4))
