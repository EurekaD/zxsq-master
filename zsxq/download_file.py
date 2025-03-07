import json

import requests
import config

url = "https://api.zsxq.com/v2/files/818288858114182/download_url"

response = requests.get(url, headers=config.get_headers())

fileDic = json.loads(response.text)
fileLink = fileDic['resp_data']['download_url']


