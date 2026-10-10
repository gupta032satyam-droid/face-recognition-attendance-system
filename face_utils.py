"""Face detection, preprocessing, training and recognition helpers (OpenCV)."""
import os

import cv2
import numpy as np

import config

_detector = cv2.CascadeClassifier(config.CASCADE_PATH)


def detect_faces(gray):
    """Return list of (x, y, w, h) boxes for faces found in a grayscale frame."""
    gray = cv2.equalizeHist(gray)
    faces = _detector.detectMultiScale(
        gray, scaleFactor=1.2, minNeighbors=5, minSize=config.MIN_FACE)
    return list(faces)


def largest_face(faces):
    return max(faces, key=lambda b: b[2] * b[3]) if len(faces) else None


def preprocess(gray, box):
    """Crop the face, resize and normalise lighting."""
    x, y, w, h = box
    face = cv2.resize(gray[y:y + h, x:x + w], config.FACE_SIZE)
    return cv2.equalizeHist(face)


def _make_recognizer():
    if not hasattr(cv2, "face"):
        raise RuntimeError(
            "cv2.face not found. Install the contrib build:\n"
            "pip uninstall opencv-python\npip install opencv-contrib-python")
    return cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)


def train_model():
    """Train LBPH on every image in data/dataset/<label>/. Returns (students, images)."""
    faces, labels = [], []
    if os.path.isdir(config.DATASET_DIR):
        for folder in os.listdir(config.DATASET_DIR):
            path = os.path.join(config.DATASET_DIR, folder)
            if not (folder.isdigit() and os.path.isdir(path)):
                continue
            for name in os.listdir(path):
                img = cv2.imread(os.path.join(path, name), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    faces.append(img)
                    labels.append(int(folder))
    if not faces:
        raise RuntimeError("No face images found. Enroll at least one student first.")
    rec = _make_recognizer()
    rec.train(faces, np.array(labels))
    rec.write(config.MODEL_PATH)
    return len(set(labels)), len(faces)


def load_model():
    if not os.path.exists(config.MODEL_PATH):
        raise RuntimeError("Model not trained yet. Enroll students / click 'Train Model'.")
    rec = _make_recognizer()
    rec.read(config.MODEL_PATH)
    return rec


def recognize(recognizer, face_img):
    """Return (label, confidence) or (None, confidence) if the face is unknown."""
    label, confidence = recognizer.predict(face_img)
    if confidence <= config.CONFIDENCE_THRESHOLD:
        return label, confidence
    return None, confidence
