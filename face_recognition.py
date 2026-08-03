import os
import sys
import time
import cv2
import serial

# Configurations
ESP32_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
THRESHOLD = 70.0  # Lower confidence score in LBPH means a better match


def init_esp32(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # Allow time for ESP32 serial reset
        print(f"[*] Connected to ESP32 on {port}")
        return ser
    except serial.SerialException:
        print("[!] ESP32 not detected. Running in simulation mode.")
        return None


def main():
    esp32 = init_esp32(ESP32_PORT, BAUD_RATE)

    # Load Haar cascade
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    # Load model
    model_path = os.path.join(os.path.dirname(os.path.abspath(_file_)), "face_model.yml")
    if not os.path.exists(model_path):
        print(f"[ERROR] Model file missing: {model_path}")
        sys.exit(1)

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)

    # Open video capture
    camera = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
    if not camera.isOpened():
        print("[ERROR] Failed to open camera stream.")
        if esp32:
            esp32.close()
        sys.exit(1)

    print("[*] Recognition running. Press 'q' to exit.")
    last_command = None

    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                print("[!] Frame capture failed.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(80, 80)
            )

            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                label, confidence = recognizer.predict(face_roi)

                if confidence < THRESHOLD:
                    text = f"AUTHORIZED ({confidence:.1f})"
                    color = (0, 255, 0)
                    command = "AUTHORIZED"
                else:
                    text = f"UNKNOWN ({confidence:.1f})"
                    color = (0, 0, 255)
                    command = "UNKNOWN"

                # State change check: send serial payload only on status flip
                if command != last_command:
                    if esp32:
                        esp32.write(f"{command}\n".encode())
                        print(f"[TX -> ESP32] {command}")
                    else:
                        print(f"[SIM] State change: {command}")
                    last_command = command

                # Draw UI overlays
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(
                    frame, text, (x, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
                )

            cv2.imshow("Face Recognition Door Lock", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        # Guaranteed cleanup regardless of how the loop exits
        print("[*] Cleaning up resources...")
        camera.release()
        cv2.destroyAllWindows()
        if esp32:
            esp32.close()


if _name_ == "_main_":
    main()
