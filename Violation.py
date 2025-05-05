import requests
import datetime
import cv2
import config   
import os
import sqlite3
import time

#每10s拍照一次，檔案名稱 timestamp.jpg，並且送去OCR，完成後儲存至SQL資料庫

#建立SQL資料庫
con = sqlite3.connect('PARKING_VIOLATION')
cursor = con.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS PARKING_VIOLATION(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate TEXT NOT NULL,
        first_seen INTEGER NOT NULL,
        last_seen INTEGER NOT NULL,
        leave BOOLEAN NOT NULL,
        is_violation BOOLEAN NOT NULL,
        alert_sent BOOLEAN NOT NULL,
        snapshot_path TEXT NOT NULL
    )
''')

#Telegram變數
send_to_TG = []

#alert變數
wait_list = []
cur = 0
last_alert_time = 0
alert_interval = 10
stoped = False

#是否拍照變數
saved = False

#自動建立資料夾
os.makedirs('./photo', exist_ok=True)

#esp32_cam url
url = f'http://{config.ESP32_CAM_IP}/stream'
cap = cv2.VideoCapture(url)

def handle_plate(plate, timestamp, image_path):
    global send_to_TG
    cursor.execute('''
        SELECT * FROM PARKING_VIOLATION
        WHERE plate = ? AND leave = 0
    ''', (plate,))
    row = cursor.fetchone()

    if row is None:
        # 第一次檢測這台車，建立資料
        cursor.execute('''
            INSERT INTO PARKING_VIOLATION(
                plate, first_seen, last_seen, leave, is_violation, alert_sent, snapshot_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (plate, timestamp, timestamp, False, False, False, image_path))
        print(f"[新增] {plate}")

        #呼叫違規
        trigger_alarm(plate)

    else:
        #第n次檢測到車輛，更新資料
        first_seen = row[2]
        last_seen = timestamp
        is_violation = (last_seen - first_seen) >= config.VIOLATION_TIME

        #發送違規通知
        snapshot_path = row[7]
        if is_violation and plate not in send_to_TG:
            print(f'[違規] {plate}')
            print(f"[推播違規] {plate}")
            send_alert_to_telegram(plate, snapshot_path)
            send_to_TG.append(plate)  # ✅ 避免重複推播

        cursor.execute('''
            UPDATE PARKING_VIOLATION
            SET last_seen = ?, is_violation = ?
            WHERE plate = ? AND leave = 0
        ''', (last_seen, is_violation, plate))

    con.commit()

def check_for_departures(current_timestamp):
    #檢測是否離開，列出所有未離開的車
    current_timestamp = int(current_timestamp)
    cursor.execute('''
        SELECT plate, last_seen FROM PARKING_VIOLATION
        WHERE leave = 0
    ''')
    rows = cursor.fetchall()

    #如果20秒內沒有檢測到，就記錄離開
    for plate, last_seen in rows:
        if current_timestamp - last_seen > 20:
            cursor.execute('''
                UPDATE PARKING_VIOLATION
                SET leave = 1
                WHERE plate = ? AND leave = 0
            ''', (plate,))
            print(f"[離開] {plate}")
    
    con.commit()

def trigger_alarm(plate):
    #將需要警報的車牌加入wait list中
    global wait_list

    if "stop" in wait_list:
        wait_list.remove("stop")

    if plate not in wait_list:
        wait_list.append(plate)
        print(f'[加入警報] {plate}')
        cursor.execute('''
            UPDATE PARKING_VIOLATION
            SET alert_sent = 1
            WHERE plate = ? AND leave = 0
        ''', (plate,))

    if "stop" not in wait_list:
        wait_list.append("stop")
    
    con.commit()

#GPT寫的telegram推播程式
def send_alert_to_telegram(plate, image_path):
    TELEGRAM_BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID = config.TELEGRAM_CHAT_ID

    message = (
        f"🚨 偵測到違規車輛：{plate}\n"
        f"🕒 拍攝時間：{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
    )

    try:
        # 發送文字
        response_msg = requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            data={'chat_id': TELEGRAM_CHAT_ID, 'text': message}
        )
        print("[✓] 傳送文字成功", response_msg.status_code)

        # 發送圖片（如果檔案存在）
        if os.path.exists(image_path):
            with open(image_path, 'rb') as photo:
                response_img = requests.post(
                    f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto',
                    data={'chat_id': TELEGRAM_CHAT_ID},
                    files={'photo': photo}
                )
            print("[✓] 傳送圖片成功", response_img.status_code)
        else:
            print("[✗] 找不到圖片檔案")

    except Exception as e:
        print("[✗] 推播失敗", e)

while cap.isOpened():
    #擷取時間
    current_datetime = datetime.datetime.now()
    timestamp = current_datetime.timestamp()

    #讀取畫面
    ret, frame = cap.read()
    if not ret:
        break
    
    #每10秒拍一張照片，並上傳到OCR服務
    if int(timestamp) % 10 == 0 and saved == False :
        #拍照儲存
        print("[儲存圖片]")
        filename = f'./photo/{int(timestamp)}.jpg'
        cv2.imwrite(filename, frame)
        saved = True
        image_path = f'./photo/{int(timestamp)}.jpg'

        #上傳至OCR服務
        with open(image_path, 'rb') as fp:
            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                headers={'Authorization': config.API_KEY},
                files={'upload': fp}
            )
        
        #print OCR結果，並加入SQL資料庫、送警告
        try:
            data = response.json()
            results = data.get('results',[])
            if not results:
                print("[未偵測到車牌]")
            else:
                for result in data['results']:
                    plate = result['plate']
                    score = result['score']
                    if score >= 0.9:
                        print(f"發現車牌：{plate}")
                        handle_plate(plate, int(timestamp), filename)
                        stoped = False
                    else:
                        print(f"[分數過低] {plate} - {score:.2f}")
        except Exception as e:
            print("[OCR錯誤]", e)
        
    #重置拍照檢測
    elif int(timestamp) % 10 != 0:
        saved = False
    
    #檢查是否離開
    check_for_departures(int(timestamp))

    current_time = time.time()
    if cur < len(wait_list):
    #如果wait list裡面有東西（指標沒指到），警報
        if current_time - last_alert_time > alert_interval:
            plate_to_alert = wait_list[cur]
            try:
                response = requests.get(f'http://{config.ESP32_ALERT_IP}/plate?value={plate_to_alert}')
                print(f'[警告] {plate_to_alert}')
                cur += 1
                last_alert_time = current_time
                stoped = False
            except:
                print(f'[警告傳送失敗] {plate_to_alert}')
    
    #如果都警報完，且尚未說過停止就停止，並且清空wait list
    if stoped == False and cur == len(wait_list) and wait_list:
        try:
            response = requests.get(f'http://{config.ESP32_ALERT_IP}/plate?value=stop')
            print(f'[停止警告]')
            stoped = True
            cur = 0
            wait_list.clear()
        except:
            print('[停止警告失敗]')
            cur = 0
            wait_list.clear()
            

con.commit()
con.close()
cap.release()