import requests, json
from urllib3.exceptions import InsecureRequestWarning
import re
import switch_manage

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def api_call(ip_addr, port, command, json_payload, sid):
    url = 'https://' + ip_addr  + ':' + port + '/gaia_api/' + command
    if sid == '':
        request_headers = {'Content-Type' : 'application/json'}
    else:
        request_headers = {'Content-Type' : 'application/json', 'X-chkp-sid' : sid}
    r = requests.post(url,data=json.dumps(json_payload), headers=request_headers, verify=False)
    return r.json()


def login(ip_addr,user,password):
    payload = {'user':user, 'password' : password}
    response = api_call(ip_addr, '443', 'login',payload, '')
    return response["sid"]


if __name__ == "__main__":
    gaia_ip = "10.169.32.178"

    try:
        sid = login(gaia_ip,'admin','iolredi8')
        # print("session id: " + sid)
    except Exception as error:
        print(error)

   # switch_vlans = switch_manage.get_vlans("192.168.88.30", "shapi", "patish")

    show_interface_data = {'name':'eth0'}
    # show_interface_result = api_call(gaia_ip, "443",'v1.7/show-interface', show_interface_data ,sid)

    show_interfaces_result = api_call(gaia_ip, "443",'v1.5/show-interfaces', "" ,sid)

    # set_interface_data = {'name':'eth1', 'ipv4-address':'192.168.1.1', 'ipv4-mask-length':'24'}
    # set_interface_result = api_call('192.168.65.2', 443,'set-physical-interface', set_interface_data ,sid)
    
    print(json.dumps(show_interfaces_result, indent=4))
    vlans_to_create = []

   # for int in show_interfaces_result["objects"]:
   #     if int["type"] == "vlan":
   #         vlan = re.findall(r'(?<=\.)\d+', int["name"])[0]
   #         if vlan in switch_vlans:
   #             print(f"vlan: {vlan} exist in switch")
   #         else:
   #             print(f"vlan: {vlan} not exist in switch, will create")
   #             vlans_to_create.append([vlan, int['name']])
   # 
    # switch_manage.create_vlan("192.168.88.30", "shapi", "patish", vlans_to_create)
    
    logout_result = api_call(gaia_ip, "443","logout", {},sid)