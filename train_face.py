import os
import cv2
import numpy as np

TRAIN_DIR = os.path.expanduser("~/training")
MODEL_DIR = os.path.expanduser("~/face_lock")
MODEL_PATH = os.path.join(MODEL_DIR, "face_model.yml")


def load_dataset(folder_path):
    faces = []
    labels = []

    if not os.path.exists(folder_path):
        print(f"[ERROR] Directory not found: {folder_path}")
        return faces, labels

    for filename in os.listdir(folder_path):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        image_path = os.path.join(folder_path, filename)
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            print(f"[WARN] Failed to load image: {filename}")
            continue

        # Extract user ID from filename (e.g., 'user_1_01.jpg' -> label 1)
        # Defaults to 1 if no numerical ID is found in the filename
        try:
            label = int("".join(filter(str.isdigit, filename)))
        except ValueError:
            label = 1

        faces.append(img)
        labels.append(label)

    return faces, labels


def main():
    print("[*] Loading training images...")
    faces, labels = load_dataset(TRAIN_DIR)

    if not faces:
        print("[!] No valid face images found. Exiting.")
        return

    print(f"[*] Training LBPH recognizer on {len(faces)} images...")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))

    os.makedirs(MODEL_DIR, exist_ok=True)
    recognizer.write(MODEL_PATH)
    print(f"[+] Model saved successfully to: {MODEL_PATH}")


if _name_ == "_main_":
    main()
