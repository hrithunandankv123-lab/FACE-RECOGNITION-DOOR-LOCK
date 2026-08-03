#include <TinyGPS++.h>

// --- Pin Assignments ---
const int TRIG_PIN    = 5;
const int ECHO_PIN    = 18;
const int WATER_PIN   = 34;
const int BUZZER_PIN  = 25;
const int VIB_MOTOR   = 26;
const int SOS_BTN     = 27;

const int GPS_RX = 16, GPS_TX = 17;
const int GSM_RX = 4,  GSM_TX = 2;

// --- Config Constants ---
const int OBSTACLE_LIMIT_CM = 50;   // Trigger alert if obstacle < 50cm
const int WATER_THRESHOLD   = 1500; // Trigger alert if water analog > 1500
const String EMERGENCY_NO   = "+919876543210";

// --- Hardware Instances ---
TinyGPSPlus gps;
HardwareSerial gpsSerial(1);
HardwareSerial gsmSerial(2);

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(WATER_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(VIB_MOTOR, OUTPUT);
  pinMode(SOS_BTN, INPUT_PULLUP);

  // Turn off feedback outputs on start
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(VIB_MOTOR, LOW);

  // Initialize Serial Buses (ESP32 RX, TX)
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);
  gsmSerial.begin(9600, SERIAL_8N1, GSM_RX, GSM_TX);

  Serial.println("System Ready: Smart Blind Stick initialized.");
}

void loop() {
  // 1. Process incoming GPS bytes constantly
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  // 2. Read Sensors
  int currentDistance = readUltrasonicDistance();
  int waterLevel = analogRead(WATER_PIN);

  // 3. Alert Logic (Ultrasonic or Water detection)
  bool obstacleDetected = (currentDistance > 0 && currentDistance <= OBSTACLE_LIMIT_CM);
  bool waterDetected = (waterLevel > WATER_THRESHOLD);

  if (obstacleDetected || waterDetected) {
    digitalWrite(BUZZER_PIN, HIGH);
    digitalWrite(VIB_MOTOR, HIGH);
  } else {
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(VIB_MOTOR, LOW);
  }

  // 4. Handle Emergency Button (Active LOW)
  if (digitalRead(SOS_BTN) == LOW) {
    delay(50); // Debounce check
    if (digitalRead(SOS_BTN) == LOW) {
      Serial.println("SOS Triggered!");
      triggerAlertSMS();
      
      // Cooldown to prevent accidental multiple texts
      delay(5000); 
    }
  }

  delay(100); // Short cycle delay
}

// Helper: Measure distance via HC-SR04
int readUltrasonicDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Read Echo pulse width with a 30ms timeout (~5m max range)
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);

  if (duration == 0) {
    return 0; // Return 0 if timeout / out of range
  }

  return duration * 0.0343 / 2; // Speed of sound conversion
}

// Helper: Send SMS via GSM module
void triggerAlertSMS() {
  Serial.println("Initiating SMS send process...");

  gsmSerial.println("AT");
  delay(500);
  gsmSerial.println("AT+CMGF=1"); // Set SMS text mode
  delay(500);

  gsmSerial.print("AT+CMGS=\"");
  gsmSerial.print(EMERGENCY_NO);
  gsmSerial.println("\"");
  delay(500);

  // Build message payload
  gsmSerial.print("EMERGENCY ALERT! Smart Stick user needs help. ");
  
  if (gps.location.isValid()) {
    gsmSerial.print("Location: https://maps.google.com/?q=");
    gsmSerial.print(gps.location.lat(), 6);
    gsmSerial.print(",");
    gsmSerial.print(gps.location.lng(), 6);
  } else {
    gsmSerial.print("Location unavailable (GPS fixing...)");
  }

  delay(200);
  gsmSerial.write(0x1A); // Send CTRL+Z to send the text
  delay(3000);

  Serial.println("SMS sent successfully.");
}