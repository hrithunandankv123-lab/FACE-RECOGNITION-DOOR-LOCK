import os
import time
import base64
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify

app = Flask(_name_)

# Configuration
ESP32_TOKEN = os.environ.get("ESP32_TOKEN", "CHANGE_THIS_TOKEN")
UPLOAD_FOLDER = "user_faces"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ESP32 State Management
esp32_connected = False
last_esp32_seen = 0
esp32_command = "NONE"


# --- Page Routes ---

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/setup")
def setup():
    return render_template("setup.html")


@app.route("/ready")
def ready():
    return render_template("ready.html")


# --- Face Registration ---

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data or "images" not in data:
        return jsonify({"success": False, "message": "No face samples received."})

    images = data["images"]
    if len(images) < 30:
        return jsonify({"success": False, "message": "Please provide 30 samples."})

    # Create unique user folder
    user_id = str(len(os.listdir(UPLOAD_FOLDER)) + 1)
    user_folder = os.path.join(UPLOAD_FOLDER, f"user_{user_id}")
    os.makedirs(user_folder, exist_ok=True)

    saved = 0
    for i, image_data in enumerate(images[:30]):
        try:
            # Decode base64 image string
            base64_str = image_data.split(",")[1]
            image_bytes = base64.b64decode(base64_str)
            image_array = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)

            if image is not None:
                file_path = os.path.join(user_folder, f"face_{i+1}.jpg")
                cv2.imwrite(file_path, image)
                saved += 1
        except Exception:
            continue

    if saved < 30:
        return jsonify({"success": False, "message": "Could not save all samples."})

    return jsonify({
        "success": True,
        "message": "30 face samples registered successfully!",
        "user_id": user_id
    })


# --- ESP32 Communication & Controls ---

@app.route("/api/esp32/status")
def esp32_status():
    global esp32_connected

    # Mark as disconnected if no heartbeat within 10 seconds
    if time.time() - last_esp32_seen > 10:
        esp32_connected = False

    return jsonify({
        "connected": esp32_connected,
        "device": "ESP32-CAM"
    })


@app.route("/api/esp32/heartbeat", methods=["POST"])
def esp32_heartbeat():
    global esp32_connected, last_esp32_seen

    # Optional token verification check
    token = request.headers.get("X-ESP32-TOKEN") or request.json.get("token") if request.is_json else None
    if token and token != ESP32_TOKEN:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    esp32_connected = True
    last_esp32_seen = time.time()

    return jsonify({"success": True, "message": "ESP32-CAM connected"})


@app.route("/api/esp32/command")
def esp32_get_command():
    global esp32_command

    command = esp32_command
    esp32_command = "NONE"  # Reset after polling

    return jsonify({"command": command})


@app.route("/api/face/authorized", methods=["POST"])
def authorized_face():
    global esp32_command
    esp32_command = "UNLOCK"

    return jsonify({
        "success": True,
        "command": "UNLOCK",
        "message": "Authorized face detected."
    })


@app.route("/api/face/unknown", methods=["POST"])
def unknown_face():
    global esp32_command
    esp32_command = "ALERT"

    return jsonify({
        "success": True,
        "command": "ALERT",
        "message": "Unknown face detected."
    })


# --- Server Entrypoint ---

if _name_ == "_main_":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
