# Automated Attendance via Face Recognition

BCA Major Project - Centre of Computer Education & Training, IPS, University of Allahabad.

A desktop application that marks student attendance automatically from a webcam feed.
Faces are detected with a Haar cascade and recognised with the **LBPH (Local Binary Patterns
Histograms)** algorithm from OpenCV. Attendance is saved to an Excel file (one sheet per date).

## Features
- Modern multi-page Tkinter GUI (Dashboard, Students, Reports, Settings)
- Quick on-the-spot enrollment (roll no, name, email + 30 face samples)
- Real-time detection and recognition from video frames
- Unknown faces are ignored automatically
- Duplicate-proof: a student is marked only once per day
- Attendance exported to `data/attendance.xlsx`, with CSV export from the Reports page
- Student management: search, preview face samples, delete, re-train model
- Adjustable settings: camera index, samples per student, recognition strictness,
  auto-stop timer, mirror view, FPS counter, beep on attendance

## Project structure
```
guimain.py        main window - RUN THIS (connects all pages)
app.py            small launcher, same as running guimain.py
gui_common.py     theme, fonts, settings storage, shared helpers
gui_dashboard.py  Dashboard page: camera, enroll, attendance
gui_students.py   Students page: list, preview, delete
gui_reports.py    Reports page: Excel viewer, search, CSV export
gui_settings.py   Settings page
face_utils.py     detection, preprocessing, training, recognition
database.py       students (CSV) and attendance (Excel)
config.py         thresholds, paths, camera index
requirements.txt  Python dependencies
```

## Setup
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
python -m venv venv
venv\Scripts\activate          # Windows   (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
python guimain.py
```
> Linux users may need `sudo apt install python3-tk`.

## Usage
1. Open **Dashboard**, fill Roll No, Name, Email and click **Enroll & Capture Face**
   (stay ~50 cm from the camera and turn your head slightly).
2. Click **Start** and stand in front of the camera - attendance is marked automatically.
3. Open the **Reports** page (or **Open Excel Sheet**) to view the record.
   Close Excel before marking attendance.
4. Use **Students** to review or remove enrolled students, and **Settings** to tune the system.

## Tuning
In `config.py`, `CONFIDENCE_THRESHOLD` (lower = stricter). Raise it if known students show as
"Unknown", lower it if strangers get recognised.

## How it works
Camera frame -> grayscale + histogram equalisation -> Haar cascade face detection ->
crop/resize 200x200 -> LBPH predict -> match below threshold -> mark attendance in Excel.

## Tech stack
Python, OpenCV (opencv-contrib-python), NumPy, Pillow, openpyxl, Tkinter.

## Privacy
Face images and student records live in `data/`, which is git-ignored. Do not push them.

## Author
<Satyam Kumar Gupta> - BCA, University of Allahabad
