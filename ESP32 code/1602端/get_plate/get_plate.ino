#include <WiFi.h>
#include <WiFiManager.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2); 

WiFiManager wm;

unsigned long lastScan = 0;
const unsigned long scanInterval = 10000;  //掃描時間

String Plate = "";

const char* PARAM_INPUT = "value";

// Create AsyncWebServer object on port 80
AsyncWebServer server(80);

const char index_html[] PROGMEM = R"rawliteral(<!DOCTYPE HTML><html><body></body></html>)rawliteral";

void setup(){
  // Serial port for debugging purposes
  Serial.begin(115200);

  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("WiFi Pairing...");
  
  // Connect to Wi-Fi
    WiFiManager wm;
  bool res = wm.autoConnect("ESP32-Setup");

  if (!res) {
    Serial.println("WiFi 連線失敗，重啟中...");
    delay(3000);
    ESP.restart();
  }

  Serial.println("WiFi 已連線！");
  Serial.println(WiFi.localIP());

  // Print ESP Local IP Address
  Serial.println(WiFi.localIP());
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(WiFi.localIP());

  // Route for root / web page
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send(200, "text/html", index_html);
  });

  // Send a GET request to <ESP_IP>/slider?value=<inputMessage>
  server.on("/plate", HTTP_GET, [] (AsyncWebServerRequest *request) {
    String inputMessage;
    // GET input1 value on <ESP_IP>/slider?value=<inputMessage>
    if (request->hasParam(PARAM_INPUT)) {
      Plate = request->getParam(PARAM_INPUT)->value();
      Serial.println("Received Plate： " + Plate);
      if(Plate == "stop"){
        lcd.clear();
      }else{
        lcd.setCursor(0, 0);
        lcd.print("Number:" + Plate);
        lcd.setCursor(0, 1);
        lcd.print("Violation!!");
      }
    }request->send(200, "text/plain", "OK");
  });
  
  // Start server
  server.begin();
}
  
void loop() {
  //如果找到ssid wifi_reset重置wifi
  if (millis() - lastScan > scanInterval) {
    lastScan = millis();
    int n = WiFi.scanNetworks();
    for (int i = 0; i < n; i++) {
      if (WiFi.SSID(i) == "wifi_reset") {
        Serial.println("開始重設Wi-Fi...");
        wm.resetSettings();     //清除儲存的Wi-Fi
        delay(1000);
        ESP.restart();          //重新啟動
      }
    }
  }
}
