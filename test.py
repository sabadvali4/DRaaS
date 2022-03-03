#Need to install requests package for python
import requests

# Set the request parameters
url = 'https://bynetdev.service-now.com/api/now/table/x_bdml_draas_switch_info/'

# Eg. User name="username", Password="password" for this code sample.
user = ''
pwd = ''

# Set proper headers
headers = {"Accept":"application/json",'Content-type':'application/json'}

# Do the HTTP request
response = requests.delete(url, auth=(user, pwd), headers=headers)

# Check for HTTP codes other than 204
if response.status_code != 204: 
    print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:', response.json())
    exit()

# Decode the JSON response into a dictionary and use the data
data = response
print(data)