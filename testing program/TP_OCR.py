import requests
import datetime
import cv2
import config
import os

#每10s拍照一次，檔案名稱 timestamp.jpg，並且送去OCR

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
        print("SAFE")
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
        data = response.json()
        print(data)
        #plate = data['results'][0]['plate']
        #score = data['results'][0]['score']
        #if score >= 0.9:
        #    print(plate)
        
    #重置拍照檢測
    elif int(timestamp) % 10 != 0:
        saved = False
cap.release()