import os
import sys
import cv2

# Configuration
CAMERA_INDEX = "/dev/video10"
TRAIN_DIR = os.path.expanduser("~/training")
MAX_SAMPLES = 30


def clear_existing_samples(folder_path):
    """Deletes existing face dataset images before recording a new batch."""
    os.makedirs(folder_path, exist_ok=True)
    for filename in os.listdir(folder_path):
        if filename.startswith("face_") and filename.endswith(".jpg"):
            os.remove(os.path.join(folder_path, filename))


def main():
    clear_existing_samples(TRAIN_DIR)

    # Initialize video stream
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    if not camera.isOpened():
        print(f"[ERROR] Could not open camera at {CAMERA_INDEX}")
        sys.exit(1)

    # Load face detector
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    sample_count = 0
    print(f"[*] Look at the camera. Collecting {MAX_SAMPLES} face samples...")

    try:
        while sample_count < MAX_SAMPLES:
            ret, frame = camera.read()
            if not ret:
                print("[!] Failed to grab frame.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(80, 80)
            )

            for (x, y, w, h) in faces:
                if sample_count >= MAX_SAMPLES:
                    break

                sample_count += 1
                face_roi = gray[y:y+h, x:x+w]

                # Save cropped gray face ROI
                file_path = os.path.join(TRAIN_DIR, f"face_{sample_count}.jpg")
                cv2.imwrite(file_path, face_roi)

                # Visual feedback
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    frame, 
                    f"Saved: {sample_count}/{MAX_SAMPLES}", 
                    (x, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                )

            cv2.imshow("Register Face", frame)

            # Manual exit check
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("[*] Collection canceled by user.")
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()

    # Final summary
    if sample_count >= MAX_SAMPLES:
        print(f"[+] Dataset collection complete! Saved {sample_count} samples to {TRAIN_DIR}")
    else:
        print(f"[!] Stopped early. Saved {sample_count}/{MAX_SAMPLES} samples.")


if _name_ == "_main_":
    main()
