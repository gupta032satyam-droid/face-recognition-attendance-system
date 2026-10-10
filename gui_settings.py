"""Settings page: camera, capture, recognition and behaviour options."""
import os
import tkinter as tk
from tkinter import messagebox, ttk

import cv2

import config
from gui_common import (BG, CARD, DEFAULTS, FONT, FONT_HEAD, TEXT, apply_settings, make_card, open_path,
                        save_settings)


class SettingsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.cfg = app.cfg
        self._build()

    def _build(self):
        card = make_card(self)
        card.pack(fill="both", expand=True)
        body = tk.Frame(card, bg=CARD)
        body.pack(fill="both", expand=True, padx=24, pady=20)
        body.grid_columnconfigure((0, 1), weight=1, uniform="c")

        self.sv = {
            "camera_index": tk.IntVar(value=self.cfg["camera_index"]),
            "samples": tk.IntVar(value=self.cfg["samples"]),
            "capture_every": tk.IntVar(value=self.cfg["capture_every"]),
            "consecutive": tk.IntVar(value=self.cfg["consecutive"]),
            "auto_stop": tk.IntVar(value=self.cfg["auto_stop"]),
            "mirror": tk.BooleanVar(value=self.cfg["mirror"]),
            "show_fps": tk.BooleanVar(value=self.cfg["show_fps"]),
            "show_boxes": tk.BooleanVar(value=self.cfg["show_boxes"]),
            "beep": tk.BooleanVar(value=self.cfg["beep"]),
        }

        def section(col, title):
            f = tk.Frame(body, bg=CARD)
            f.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 20, 0))
            tk.Label(f, text=title, bg=CARD, fg=TEXT,
                     font=(FONT_HEAD, 14, "bold")).pack(anchor="w", pady=(0, 10))
            return f

        def spin(parent, label, key, lo, hi, hint):
            r = tk.Frame(parent, bg=CARD)
            r.pack(fill="x", pady=7)
            ttk.Label(r, text=label, style="Card.TLabel").pack(anchor="w")
            line = tk.Frame(r, bg=CARD)
            line.pack(fill="x")
            ttk.Spinbox(line, from_=lo, to=hi, textvariable=self.sv[key], width=8).pack(side="left")
            ttk.Label(line, text=hint, style="Muted.TLabel").pack(side="left", padx=10)

        def check(parent, label, key):
            ttk.Checkbutton(parent, text=label, variable=self.sv[key],
                            style="Card.TCheckbutton").pack(anchor="w", pady=5)

        cam = section(0, "Camera & capture")
        spin(cam, "Camera index", "camera_index", 0, 10, "0 = default webcam")
        spin(cam, "Face samples per student", "samples", 10, 200, "more = better accuracy")
        spin(cam, "Capture every N frames", "capture_every", 1, 15, "higher = more varied poses")
        row = tk.Frame(cam, bg=CARD)
        row.pack(fill="x", pady=8)
        ttk.Button(row, text="Detect cameras", command=self.detect_cameras).pack(side="left")
        self.cam_info = tk.StringVar()
        ttk.Label(row, textvariable=self.cam_info, style="Muted.TLabel").pack(side="left", padx=10)

        rec = section(1, "Recognition & behaviour")
        spin(rec, "Consecutive matches to mark present", "consecutive", 1, 30,
             "higher = fewer false positives")
        spin(rec, "Auto-stop attendance after (minutes)", "auto_stop", 0, 600, "0 = never")
        check(rec, "Mirror camera image", "mirror")
        check(rec, "Show face boxes & names", "show_boxes")
        check(rec, "Show FPS counter", "show_fps")
        check(rec, "Beep when attendance is marked", "beep")

        foot = tk.Frame(card, bg=CARD)
        foot.pack(fill="x", padx=24, pady=(0, 20))
        ttk.Button(foot, text="Save settings", style="Accent.TButton",
                   command=self.save).pack(side="left")
        ttk.Button(foot, text="Reset to defaults", command=self.reset).pack(side="left", padx=8)
        ttk.Button(foot, text="Open data folder",
                   command=lambda: open_path(os.path.abspath(config.DATASET_DIR))).pack(side="right")

    def on_show(self):
        pass

    def save(self):
        try:
            for k, v in self.sv.items():
                self.cfg[k] = v.get()          # updates the shared dict in place
        except tk.TclError:
            messagebox.showwarning("Settings", "Please enter valid numbers.")
            return
        apply_settings(self.cfg)
        try:
            save_settings(self.cfg)
        except OSError as exc:
            messagebox.showerror("Settings", str(exc))
            return
        self.app.set_status("Settings saved.")
        messagebox.showinfo("Settings", "Settings saved.")

    def reset(self):
        for k, v in DEFAULTS.items():
            self.sv[k].set(v)

    def detect_cameras(self):
        self.cam_info.set("Scanning...")
        self.update_idletasks()
        found = []
        for i in range(5):
            c = cv2.VideoCapture(i)
            if c.isOpened():
                found.append(i)
            c.release()
        self.cam_info.set("Found: " + (", ".join(map(str, found)) if found else "none"))
