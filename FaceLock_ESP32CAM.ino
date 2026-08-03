#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>

// --- Configuration ---
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

const char* HEARTBEAT_URL = "https://facelock-pgd8.onrender.com/api/esp32/heartbeat";
const char* COMMAND_URL   = "https://facelock-pgd8.onrender.com/api/esp32/command";
const char* ESP32_TOKEN   = "YOUR_PRIVATE_TOKEN";

// --- Pin Definitions ---
constexpr int SERVO_PIN  = 13;
constexpr int BUZZER_PIN = 14;

// --- Servo Settings ---
constexpr int LOCKED_POS   = 0;
constexpr int UNLOCKED_POS = 90;

// --- State & Timers ---
Servo doorServo;
unsigned long lastPollTime = 0;
const unsigned long POLL_INTERVAL = 3000; // Poll server every 3 seconds

// --- Function Prototypes ---
void connectWiFi();
void sendHeartbeat();
void checkCommand();
void unlockDoor();
void triggerAlert();

void setup() {
    Serial.begin(115200);
    Serial.println("\n==================================");
    Serial.println("       FaceLock ESP32-CAM");
    Serial.println("==================================");

    // Hardware Initialization
    pinMode(BUZZER_PIN, OUTPUT);
    digitalWrite(BUZZER_PIN, LOW);

    doorServo.setPeriodHertz(50);
    doorServo.attach(SERVO_PIN, 500, 2400);
    doorServo.write(LOCKED_POS);

    connectWiFi();
    Serial.println("FaceLock system ready.");
}

void loop() {
    // Keep Wi-Fi connected
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }

    // Non-blocking timer check
    if (millis() - lastPollTime >= POLL_INTERVAL) {
        lastPollTime = millis();
        
        sendHeartbeat();
        checkCommand();
    }
}

void connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) return;

    Serial.print("Connecting to Wi-Fi...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.printf("\nWi-Fi Connected! IP: %s\n", WiFi.localIP().toString().c_str());
}

void sendHeartbeat() {
    HTTPClient http;
    http.begin(HEARTBEAT_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-ESP32-TOKEN", ESP32_TOKEN);

    int httpCode = http.POST("{}");
    if (httpCode > 0) {
        Serial.printf("[Heartbeat] HTTP %d\n", httpCode);
    } else {
        Serial.printf("[Heartbeat] Failed, error: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();
}

void checkCommand() {
    HTTPClient http;
    http.begin(COMMAND_URL);
    http.addHeader("X-ESP32-TOKEN", ESP32_TOKEN);

    int httpCode = http.GET();
    
    if (httpCode == HTTP_CODE_OK) {
        String response = http.getString();
        Serial.printf("[Command] Received: %s\n", response.c_str());

        if (response.indexOf("UNLOCK") != -1) {
            unlockDoor();
        } else if (response.indexOf("ALERT") != -1) {
            triggerAlert();
        }
    }
    http.end();
}

void unlockDoor() {
    Serial.println("--> Access Granted: Unlocking door");
    doorServo.write(UNLOCKED_POS);
    delay(5000); // Hold open for 5 seconds
    doorServo.write(LOCKED_POS);
    Serial.println("--> Door Relocked");
}

void triggerAlert() {
    Serial.println("--> Unauthorized Access: Triggering Alert!");
    digitalWrite(BUZZER_PIN, HIGH);
    delay(1000);
    digitalWrite(BUZZER_PIN, LOW);
}