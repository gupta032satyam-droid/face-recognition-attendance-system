"""Dashboard page: live camera, enrolment, attendance taking, today's table."""
import os
import time
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
from PIL import Image, ImageTk

import config
import database
import face_utils
from gui_common import (ACCENT, BG, BLUE, CARD, DANGER, FONT, FONT_HEAD, GREEN, MUTED, OK, RED, TEXT, WARN,
                        beep, make_card, open_excel, retrain_model, all_students)


class DashboardPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.cfg = app.cfg

        self.cap = None
        self.mode = "idle"            # idle | enroll | attend
        self.recognizer = None
        self.streak = {}              # label -> consecutive matches
        self.marked = set()           # labels already handled this session
        self.enroll_label = None
        self.sample_count = 0
        self.frame_count = 0
        self.attend_started = 0.0
        self._last_frame_t = time.time()
        self._fps = 0.0

        self._build()

    # ------------------------------------------------------------------ UI
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # stat cards
        stats = tk.Frame(self, bg=BG)
        stats.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        self.stat_vars = {}
        for i, (key, title, color) in enumerate((("enrolled", "Enrolled students", ACCENT),
                                                  ("present", "Present today", OK),
                                                  ("absent", "Absent today", DANGER),
                                                  ("camera", "Camera status", WARN))):
            stats.grid_columnconfigure(i, weight=1, uniform="s")
            c = make_card(stats)
            c.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 10, 0))
            tk.Frame(c, bg=color, width=5).pack(side="left", fill="y")
            inner = tk.Frame(c, bg=CARD)
            inner.pack(side="left", padx=14, pady=10)
            tk.Label(inner, text=title, bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w")
            v = tk.StringVar(value="-")
            tk.Label(inner, textvariable=v, bg=CARD, fg=TEXT, font=(FONT, 18, "bold")).pack(anchor="w")
            self.stat_vars[key] = v

        # video card
        vcard = make_card(self)
        vcard.grid(row=1, column=0, sticky="nsew", padx=(0, 14))
        tk.Label(vcard, text="Live camera", bg=CARD, fg=TEXT, font=(FONT_HEAD, 13, "bold"),
                 anchor="w").pack(fill="x", padx=14, pady=(12, 6))
        self.video = tk.Label(vcard, bg="#0b1220", fg="#94a3b8", text="Camera is off",
                              font=(FONT, 14))
        self.video.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # right panel
        right = tk.Frame(self, bg=BG, width=390)
        right.grid(row=1, column=1, sticky="ns")
        right.grid_propagate(False)
        right.pack_propagate(False)

        enroll = make_card(right)
        enroll.pack(fill="x")
        tk.Label(enroll, text="Enroll new student", bg=CARD, fg=TEXT,
                 font=(FONT_HEAD, 13, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        form = tk.Frame(enroll, bg=CARD)
        form.pack(fill="x", padx=14, pady=(0, 14))
        form.grid_columnconfigure(1, weight=1)
        self.roll_var, self.name_var, self.email_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        for i, (label, var) in enumerate((("Roll No", self.roll_var), ("Name", self.name_var),
                                          ("Email", self.email_var))):
            ttk.Label(form, text=label, style="Card.TLabel").grid(row=i, column=0, sticky="w", pady=4)
            ttk.Entry(form, textvariable=var).grid(row=i, column=1, sticky="ew", pady=4, padx=(10, 0))
        ttk.Button(form, text="Enroll & Capture Face", style="Accent.TButton",
                   command=self.start_enroll).grid(row=3, column=0, columnspan=2,
                                                    sticky="ew", pady=(8, 0))

        act = make_card(right)
        act.pack(fill="x", pady=12)
        tk.Label(act, text="Take attendance", bg=CARD, fg=TEXT,
                 font=(FONT_HEAD, 13, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        row = tk.Frame(act, bg=CARD)
        row.pack(fill="x", padx=14, pady=(0, 14))
        row.grid_columnconfigure((0, 1), weight=1, uniform="b")
        ttk.Button(row, text="Start", style="Success.TButton",
                   command=self.start_attendance).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(row, text="Stop", style="Danger.TButton",
                   command=self.stop).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Button(row, text="Re-train Model", command=lambda: retrain_model(self.app))\
            .grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        tcard = make_card(right)
        tcard.pack(fill="both", expand=True)
        tk.Label(tcard, text="Today's attendance", bg=CARD, fg=TEXT,
                 font=(FONT_HEAD, 13, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        cols = ("roll", "name", "time")
        self.table = ttk.Treeview(tcard, columns=cols, show="headings", height=6)
        for c, t, w in (("roll", "Roll No", 80), ("name", "Name", 160), ("time", "Time", 80)):
            self.table.heading(c, text=t)
            self.table.column(c, width=w)
        self.table.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        ttk.Button(right, text="Open Excel Sheet", command=open_excel).pack(fill="x", pady=(10, 0))

    # --------------------------------------------------------------- state
    def on_show(self):
        self.refresh_table()

    def refresh_table(self):
        self.table.delete(*self.table.get_children())
        for roll, name, _email, t in database.todays_attendance():
            self.table.insert("", "end", values=(roll, name, t))
        self.update_stats()

    def update_stats(self):
        try:
            enrolled = len(all_students())
            present = len(database.todays_attendance())
        except Exception:
            enrolled, present = 0, 0
        self.stat_vars["enrolled"].set(str(enrolled))
        self.stat_vars["present"].set(str(present))
        self.stat_vars["absent"].set(str(max(enrolled - present, 0)))
        self.stat_vars["camera"].set({"idle": "Off", "enroll": "Enrolling",
                                      "attend": "Scanning"}[self.mode])

    # -------------------------------------------------------------- camera
    def _open_camera(self):
        self.cap = cv2.VideoCapture(int(self.cfg["camera_index"]))
        if not self.cap.isOpened():
            self.cap = None
            messagebox.showerror("Camera", "Could not open the camera.\n"
                                           "Try another camera index in Settings.")
            return False
        return True

    def stop(self, message="Camera stopped."):
        self.mode = "idle"
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.video.configure(image="", text="Camera is off")
        self.video.image = None
        self.app.set_status(message)
        self.update_stats()

    def _loop(self):
        if self.mode == "idle" or self.cap is None:
            return
        ok, frame = self.cap.read()
        if not ok:
            self.stop("Camera read failed.")
            return
        if self.cfg["mirror"]:
            frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_utils.detect_faces(gray)
        try:
            if self.mode == "enroll":
                self._enroll_step(frame, gray, faces)
            elif self.mode == "attend":
                self._attend_step(frame, gray, faces)
        except Exception as exc:                     # keep GUI alive on errors
            self.stop(f"Error: {exc}")
            messagebox.showerror("Error", str(exc))
            return
        if (self.mode == "attend" and self.cfg["auto_stop"] > 0
                and time.time() - self.attend_started > self.cfg["auto_stop"] * 60):
            self.stop("Attendance session auto-stopped (time limit reached).")
            return
        if self.mode != "idle":
            now = time.time()
            self._fps = 0.9 * self._fps + 0.1 * (1.0 / max(now - self._last_frame_t, 1e-3))
            self._last_frame_t = now
            if self.cfg["show_fps"]:
                cv2.putText(frame, f"{self._fps:.0f} FPS", (10, frame.shape[0] - 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            self._show(frame)
            self.after(30, self._loop)

    def _show(self, frame):
        w, h = max(self.video.winfo_width(), 100), max(self.video.winfo_height(), 100)
        fh, fw = frame.shape[:2]
        scale = min(w / fw, h / fh)
        frame = cv2.resize(frame, (max(int(fw * scale), 1), max(int(fh * scale), 1)))
        img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        self.video.configure(image=img, text="")
        self.video.image = img          # keep a reference

    # ----------------------------------------------------------- enrollment
    def start_enroll(self):
        if self.mode != "idle":
            self.stop()
        try:
            self.enroll_label = database.add_student(
                self.roll_var.get(), self.name_var.get(), self.email_var.get())
        except ValueError as exc:
            messagebox.showwarning("Enrollment", str(exc))
            return
        if not self._open_camera():
            database.remove_student(self.enroll_label)
            return
        os.makedirs(os.path.join(config.DATASET_DIR, str(self.enroll_label)), exist_ok=True)
        self.sample_count = self.frame_count = 0
        self.mode = "enroll"
        self.update_stats()
        self.app.set_status("Look at the camera (keep 50 cm+ away). Slowly turn your head a little.")
        self._loop()

    def _enroll_step(self, frame, gray, faces):
        box = face_utils.largest_face(faces)
        if box is None:
            return
        x, y, w, h = box
        if self.cfg["show_boxes"]:
            cv2.rectangle(frame, (x, y), (x + w, y + h), BLUE, 2)
        self.frame_count += 1
        if self.frame_count % config.CAPTURE_EVERY_N_FRAMES == 0:
            self.sample_count += 1
            path = os.path.join(config.DATASET_DIR, str(self.enroll_label),
                                f"{self.sample_count}.jpg")
            cv2.imwrite(path, face_utils.preprocess(gray, box))
        cv2.putText(frame, f"Captured {self.sample_count}/{config.SAMPLES_PER_STUDENT}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, BLUE, 2)
        self.app.set_status(f"Capturing... {self.sample_count}/{config.SAMPLES_PER_STUDENT}")
        if self.sample_count >= config.SAMPLES_PER_STUDENT:
            self.stop("Enrollment complete. Training model...")
            self.update_idletasks()
            retrain_model(self.app, silent=True)
            name = self.name_var.get()
            self.roll_var.set(""); self.name_var.set(""); self.email_var.set("")
            self.update_stats()
            messagebox.showinfo("Enrollment", f"{name} enrolled successfully.")

    # ----------------------------------------------------------- attendance
    def start_attendance(self):
        if self.mode != "idle":
            self.stop()
        try:
            self.recognizer = face_utils.load_model()
        except Exception as exc:
            messagebox.showerror("Model", str(exc))
            return
        if not self._open_camera():
            return
        self.streak.clear()
        self.marked.clear()
        self.attend_started = time.time()
        self.mode = "attend"
        self.update_stats()
        self.app.set_status("Attendance running. Stand in front of the camera.")
        self._loop()

    def _attend_step(self, frame, gray, faces):
        seen = set()
        boxes = self.cfg["show_boxes"]
        for box in faces:
            x, y, w, h = box
            label, conf = face_utils.recognize(self.recognizer, face_utils.preprocess(gray, box))
            student = database.get_student_by_label(label) if label is not None else None
            if student is None:                      # unknown face -> ignored
                if boxes:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), RED, 2)
                    cv2.putText(frame, "Unknown", (x, y - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, RED, 2)
                continue
            seen.add(label)
            self.streak[label] = self.streak.get(label, 0) + 1
            if label not in self.marked and self.streak[label] >= config.CONSECUTIVE_MATCHES:
                self.marked.add(label)
                try:
                    if database.mark_attendance(student):
                        self.app.set_status(f"Marked present: {student['name']}")
                        beep(self, self.cfg["beep"])
                    else:
                        self.app.set_status(f"{student['name']} was already marked today.")
                except PermissionError:
                    self.marked.discard(label)
                    self.app.set_status("Close the Excel file so attendance can be saved!")
                self.refresh_table()
            done = label in self.marked
            if boxes:
                cv2.rectangle(frame, (x, y), (x + w, y + h), GREEN, 2)
                cv2.putText(frame, f"{student['name']} {'(present)' if done else ''}",
                            (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, GREEN, 2)
        for lbl in list(self.streak):                 # reset streak for faces not in frame
            if lbl not in seen:
                self.streak[lbl] = 0
