import requests

url = "https://www.telekino.com.ar/telekino/"
headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(url, headers=headers)
print(r.text[:4000])
