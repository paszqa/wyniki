import requests
import re
import json
from datetime import datetime

def download_website(url):
    response = requests.get(url)
    return response.text

def extract_json(html_content):
    # Use regular expression to find the line containing "params"
    match = re.search(r'var params = ({.*?});', html_content)
    
    if match:
        json_str = match.group(1)
        return json.loads(json_str)

    return None

def calculate_duration(start, stop):
    start_time = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    stop_time = datetime.strptime(stop, "%Y-%m-%d %H:%M:%S")
    duration = (stop_time - start_time).total_seconds()
    return duration

site_url = "https://www.sejm.gov.pl/Sejm10.nsf/transmisja.xsp?documentId=403643B2EF41AC63C1258A68003A48BC&symbol=WYPOWIEDZ_TRANSMISJA"
html_content = download_website(site_url)
params_json = extract_json(html_content)

if params_json:
    start_time = params_json["params"]["start"]
    stop_time = params_json["params"]["stop"]
    
    duration_seconds = calculate_duration(start_time, stop_time)
    print(f"Duration between start and stop: {duration_seconds} seconds")
else:
    print("Couldn't find the 'params' line with JSON data.")
