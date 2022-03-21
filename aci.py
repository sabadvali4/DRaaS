""" get Token """
import requests
import json

def get_token(APIC):  
  url = f"https://{APIC}/api/aaaLogin.json"

  payload = {
    "aaaUser": {
       "attributes": {
          "name":"admin",
          "pwd":"C1sco12345"
        }
    }
   }

  headers = {
    "Content-Type" : "application/json"
   }
      
  requests.packages.urllib3.disable_warnings()
  response = requests.post(url,data=json.dumps(payload), headers=headers, verify=False).json()

  token = response['imdata'][0]['aaaLogin']['attributes']['token']
  return token

def my_post(URL,payload,token = None):
  url = URL
  data = payload
  if (token == None):
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
  else:
    headers = {'Content-type': 'application/json', 'Accept': 'application/json', "Cookie" : f"APIC-Cookie={token}"}  
  requests.packages.urllib3.disable_warnings()
  return requests.post(url, data=json.dumps(data), headers=headers, verify=False)

def my_get(URL,token = None):
  url = URL
  if (token == None):
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
  else:
    headers = {'Content-type': 'application/json', 'Accept': 'application/json', "Cookie" : f"APIC-Cookie={token}"}  
  requests.packages.urllib3.disable_warnings()
  return requests.get(url, headers=headers, verify=False)
  
  
def main():
  APIC = "10.10.20.14" 
  
  token = get_token(APIC)
  print("The token is: " + token)

  """create tenant"""
  NAME = "Leumit"
  DN = f"tn-{NAME}"
  URL = f"https://{APIC}/api/node/mo/uni/{DN}.json"
  payload = {"fvTenant":{"attributes":{"dn":f"uni/{DN}","name":NAME,"nameAlias":NAME,"rn":DN,"status":"created"},"children":[]}}
  response=my_post(URL,payload,token)
  print("Response code ["+str(response)+"] Create tenant : \n")
  data = response.content
  print(data)
  """ list all Tenants """
  url = f"https://{APIC}/api/node/class/fvTenant.json"
  payload={}
  response=my_get(URL,token)
  print("Response code ["+str(response)+"] tenant list: \n")
  data = response.content
  print(data)

  
  
  
if __name__ == "__main__":
   main()