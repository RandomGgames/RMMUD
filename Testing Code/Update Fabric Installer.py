import requests
import urllib
import os

## Get latest installer
url = "https://meta.fabricmc.net/v2/versions/installer?limit=1"
response = requests.get(url).json()[0]
print(f'{response = }')
installer_version = response['version']
installer_download_url = response['url']
installer_file_name = response['url'].split('/')[-1]
if not os.path.exists(installer_file_name):
    with open(installer_file_name, 'wb') as f: f.write(requests.get(installer_download_url).content)
