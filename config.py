from dotenv import load_dotenv
import os

# 載入 .env 檔案
load_dotenv()

# 讀取設定
API_KEY = os.getenv('API_KEY')
ESP32_CAM_IP = os.getenv('ESP32_CAM_IP')
ESP32_ALERT_IP = os.getenv('ESP32_ALERT_IP')
VIOLATION_TIME = int(os.getenv('VIOLATION_TIME', 30))
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')