import datetime
import cv2
import config
import os

#每10s拍照一次，檔案名稱 timestamp.jpg

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
    
    #每10秒拍一張照片
    if int(timestamp) % 10 == 0 and saved == False :
        print("SAFE")
        filename = f'./photo/{int(timestamp)}.jpg'
        cv2.imwrite(filename, frame)
        saved = True
        
    elif int(timestamp) % 10 != 0:
        saved = False
cap.release()