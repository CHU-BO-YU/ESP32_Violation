# 🚗 違停偵測系統 Parking Violation Detection System

本專案使用 ESP32-CAM 進行影像擷取，搭配車牌讀取 API 與 Telegram 推播，達成 **即時違停偵測與警告通知**。偵測結果會儲存至 SQLite 資料庫，並透過警報裝置與 Telegram 同步通知駕駛人與管理者。

---

## 📦 功能說明

* 每 10 秒拍攝一張照片
* 使用 [Plate Recognizer](https://platerecognizer.com/) API 進行車牌 OCR 讀取
* 讀取結果儲存於 SQLite 資料庫
* 偵測同一車車停留超過 `config.VIOLATION_TIME` 秒 → 標記為違規
* 初次偵測即送出警報（ESP32 顯示/蜂鳴器）
* 達違規門準後 → 發送 Telegram 推播（文字＋照片）
* 20 秒未再次偵測 → 標記為「已離開」

---

## 📁 專案結構

```
📁 project/
🔜 config.py                  # 配置檔：ESP32 IP、API KEY、違規秒數
🔜 every_10s_take_photo.py    # 主程式：攝影、讀取、資料處理、推播
🔜 photo/                     # 儲存圖片資料夾
🔜 PARKING_VIOLATION          # SQLite 資料庫
```

---

## ⚙️ 環境需求

* Python 3.8+
* 套件安裝：

  ```bash
  pip install requests opencv-python
  ```
* ESP32-CAM 可串流影像 (/stream)
* Plate Recognizer API Key (免費註冊即可)
* Telegram Bot Token 與群組 Chat ID

---

## 🔧 config.py 範例

```python
# config.py（可用環境變數方式轉接）

import os
from dotenv import load_dotenv
load_dotenv()

# Plate Recognizer API 金鑰
API_KEY = os.getenv('API_KEY') or 'Token YOUR_PLATE_RECOGNIZER_API_KEY'

# ESP32-CAM 影像串流 IP
ESP32_CAM_IP = os.getenv('ESP32_CAM_IP') or '192.168.1.100'

# ESP32 警告裝置 (e.g., 蜂鳴器/顯示) IP
ESP32_ALERT_IP = os.getenv('ESP32_ALERT_IP') or '192.168.1.101'

# 判定為違規的秒數門準
VIOLATION_TIME = int(os.getenv('VIOLATION_TIME', 30))

# Telegram Bot 設定
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or 'your_telegram_bot_token'
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID') or 'your_chat_id_or_group_id'
```

> ✅ 可選用 `.env` 檔案放置敏感資訊，例如：
>
> ```dotenv
> API_KEY=Token YOUR_PLATE_RECOGNIZER_API_KEY
> ESP32_CAM_IP=192.168.1.100
> ESP32_ALERT_IP=192.168.1.101
> VIOLATION_TIME=30
> TELEGRAM_BOT_TOKEN=your_telegram_bot_token
> TELEGRAM_CHAT_ID=your_chat_id_or_group_id
> ```

---

## 🚀 執行方式

```bash
python every_10s_take_photo.py
```

---

## 📊 資料庫欄位說明（SQLite）

| 欄位名稱            | 說明                  |
| --------------- | ------------------- |
| `id`            | 自動遞增編號              |
| `plate`         | 車牌號碼                |
| `first_seen`    | 初次偵測時間 (timestamp)  |
| `last_seen`     | 最近偵測時間              |
| `leave`         | 是否離開 (True / False) |
| `is_violation`  | 是否違規 (True / False) |
| `alert_sent`    | 是否已推播通知             |
| `snapshot_path` | 照片路徑                |

---

## 📢 推播格式（Telegram）

* 文字內容：

  ```
  🚨 偵測到違規車車：ABC123
  🕒 拍攝時間：2025/05/05 01:20:30
  ```
* 附加即時拍攝照片

---

## 🛎️ 警報流程

1. 初次偵測車牌 → 呼叫 `/plate?value=...車牌`
2. 每次推播一次，防止重複
3. 全部違停推播完畢 → 呼叫 `/plate?value=stop` 停止警示顯示
