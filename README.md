# ESP32\_Violation

一套基於 ESP32-CAM 的違規停車偵測與提醒系統

## 專案簡介

本專案設計一套低成本、模組化的違停偵測系統，透過 ESP32-CAM 擷取影像，自動辨識違停車輛並發送警告訊息至第二塊 ESP32 顯示端。系統支援多車牌排程、斷線自動重連與資料庫儲存，並可自動尋找伺服器 IP，適合部署於校園、社區或工廠內網環境。

## 系統架構

* **ESP32-CAM 偵測端**：

  * 每 10 秒拍照
  * 上傳至 Flask Server
  * 呼叫 Plate Recognizer API 辨識車牌
  * 將結果儲存至資料庫

* **Flask Server（本地端）**：

  * 接收圖片並儲存
  * 整合車牌辨識 API
  * 記錄資料至 SQLite
  * 每 10 秒發送未通知車牌至顯示端

* **ESP32 顯示端**：

  * 接收 `/plate?value=ABC123` 指令
  * 顯示車牌與警告 10 秒

## 專案目錄

```
ESP32_Violation/
├── IP_Finder.py               # UDP / MAC 查詢伺服器 IP 工具
├── Violation.py               # 主伺服器程式（Flask）
├── config.py                  # API 金鑰與伺服器設定（應避免上傳）
├── violation_database.db      # SQLite 資料庫
├── ESP32 code/
│   ├── CAM端/video_stream/    # ESP32-CAM 偵測端程式
│   └── 1602端/get_plate/      # ESP32 顯示端程式（1602 LCD）
├── testing program/           # 測試模組（OCR、影像擷取、資料儲存）
│   ├── TP_OCR.py
│   ├── every_10s_take_photo.py
│   ├── get_video_from_esp32.py
│   ├── save_plate_to_sql.py
│   └── ocr.py
└── README.md
```

## IP Finder 工具

`IP_Finder.py` 提供手動查詢伺服器 IP 的功能，使用者可依據 ESP32 的 MAC 位址尋找當前 IP。

### 功能說明：

* **MAC 查詢模式（手動）**：

  * 使用者輸入 ESP32 的 MAC 位址（如：34:85:18\:AB\:CD\:EF）
  * 程式從 DHCP 資訊或網路掃描中查詢對應 IP
  * 回傳結果供手動設定 ESP32 上傳目標伺服器位址

### 使用方式：

啟動程式後依照指引輸入 ESP32 的 MAC 位址，即可查詢對應 IP。

```bash
python IP_Finder.py
```

### 範例輸出：

```bash
== MAC 查詢模式 ==
Searching for MAC: 34:85:18:AB:CD:EF
Found IP: 192.168.1.101
```

## 資料庫結構（SQLite）

| 欄位          | 說明       |
| ----------- | -------- |
| plate       | 車牌號碼     |
| first\_seen | 初次偵測時間   |
| last\_seen  | 最近偵測時間   |
| alert\_sent | 是否已提醒過駕駛 |
| left        | 車輛是否已離開  |
| violate     | 是否違規     |

## 安裝與執行

### 伺服器端

```bash
pip install flask requests
python Violation.py
```

### ESP32 偵測端與顯示端

請將 `ESP32 code/` 內的 `.ino` 程式上傳至對應裝置：

* `video_stream.ino` → CAM 端
* `get_plate.ino` → 顯示端

## 系統特色

* 支援多車牌辨識與拍照排程
* 車牌違規通知可排隊自動發送
* 支援 MAC 查詢伺服器 IP（手動）
* 資料本地儲存，可供後續查詢分析
* 具備測試模組與可擴充架構

## 授權

MIT License
