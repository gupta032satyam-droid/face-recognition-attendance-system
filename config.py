"""Central configuration for the Automated Attendance System."""
import os
import cv2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATASET_DIR = os.path.join(DATA_DIR, "dataset")          # face images per student
MODEL_PATH = os.path.join(DATA_DIR, "trainer.yml")       # trained LBPH model
STUDENTS_CSV = os.path.join(DATA_DIR, "students.csv")    # enrolled students
ATTENDANCE_XLSX = os.path.join(DATA_DIR, "attendance.xlsx")  # one sheet per date

CASCADE_PATH = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")

CAMERA_INDEX = 0
FACE_SIZE = (200, 200)       # all faces are resized to this before training/recognition
MIN_FACE = (80, 80)          # ignore faces smaller than this (user too far away)
SAMPLES_PER_STUDENT = 30     # images captured during enrollment
CAPTURE_EVERY_N_FRAMES = 3   # spacing between samples so they differ slightly

# LBPH: LOWER confidence value = better match. Tune this for your camera/lighting.
CONFIDENCE_THRESHOLD = 65
CONSECUTIVE_MATCHES = 3      # frames in a row needed before attendance is marked
