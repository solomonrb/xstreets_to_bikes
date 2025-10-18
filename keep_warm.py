import requests
import time

url = "https://bikeshare-solomonrb.pythonanywhere.com/"

try:
    response = requests.get(url, timeout=30)
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Status: {response.status_code}")
except Exception as e:
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Error: {e}")
