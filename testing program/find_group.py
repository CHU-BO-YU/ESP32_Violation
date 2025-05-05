import requests

TOKEN = 'YOUR_TELEGRAM_API'
url = f'https://api.telegram.org/bot{TOKEN}/getUpdates'
res = requests.get(url)
print(res.json())
