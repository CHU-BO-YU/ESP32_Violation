import requests
import datetime
import cv2
import config
import os
import sqlite3

#每10s拍照一次，檔案名稱 timestamp.jpg，並且送去OCR，完成後儲存至SQL資料庫

def handle_plate(plate, timestamp, image_path):
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
        print(f'[違規] {plate}')

        cursor.execute('''
            UPDATE PARKING_VIOLATION
            SET last_seen = ?, is_violation = ?
            WHERE plate = ? AND leave = 0
        ''', (last_seen, is_violation, plate))

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

def trigger_alarm(plate):
    print(f"[警告] {plate}")
    cursor.execute('''
        UPDATE PARKING_VIOLATION
        SET alert_sent = 1
        WHERE plate = ? AND leave = 0
    ''', (plate,))
    con.commit()


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

#是否拍照變數
saved = False

#自動建立資料夾
os.makedirs('./photo', exist_ok=True)

#esp32_cam url
url = f'http://{config.ESP32_CAM_IP}/stream'
cap = cv2.VideoCapture(url)

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
        
        #print OCR結果
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
                    else:
                        print(f"[分數過低] {plate} - {score:.2f}")
        except Exception as e:
            print("[OCR錯誤]", e)
        
    #重置拍照檢測
    elif int(timestamp) % 10 != 0:
        saved = False
    
    #檢查是否離開
    check_for_departures(int(timestamp))

con.commit()
con.close()
cap.release()