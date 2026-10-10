"""Shared theme, settings storage and helper functions used by all GUI pages."""
import datetime as dt
import json
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

import config
import database
import face_utils

# ---------------------------------------------------------------- palette
GREEN, RED, BLUE = (0, 200, 0), (0, 0, 220), (220, 120, 0)   # BGR (OpenCV)

SIDEBAR = "#0f172a"
SIDEBAR_HOVER = "#1e293b"
ACCENT = "#6366f1"
ACCENT_DARK = "#4f46e5"
BG = "#f1f5f9"
CARD = "#ffffff"
BORDER = "#e2e8f0"
TEXT = "#0f172a"
MUTED = "#64748b"
DANGER = "#ef4444"
OK = "#22c55e"
WARN = "#f59e0b"


def _pick_font(*names):
    """Return the first installed font from names (last one is the fallback)."""
    try:
        import tkinter.font as tkfont
        r = tk.Tk()
        r.withdraw()
        have = set(tkfont.families(r))
        r.destroy()
        for n in names:
            if n in have:
                return n
    except Exception:
        pass
    return names[-1]


# Classic look: Georgia for titles/headings, Palatino for body text.
# To change the style, edit just these two lines.
FONT_HEAD = _pick_font("Georgia", "Cambria", "Times New Roman", "serif")
FONT = _pick_font("Palatino Linotype", "Book Antiqua", "Palatino", "Cambria",
                  "Georgia", "Times New Roman")

# --------------------------------------------------------------- settings
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
DEFAULTS = {
    "camera_index": getattr(config, "CAMERA_INDEX", 0),
    "samples": getattr(config, "SAMPLES_PER_STUDENT", 30),
    "capture_every": getattr(config, "CAPTURE_EVERY_N_FRAMES", 3),
    "consecutive": getattr(config, "CONSECUTIVE_MATCHES", 5),
    "mirror": True,
    "show_fps": True,
    "show_boxes": True,
    "beep": True,
    "auto_stop": 0,          # minutes, 0 = never
}


def load_settings():
    cfg = dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            cfg.update({k: v for k, v in json.load(f).items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    return cfg


def save_settings(cfg):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def apply_settings(cfg):
    """Push settings into the config module so face_utils/database see them."""
    config.CAMERA_INDEX = int(cfg["camera_index"])
    config.SAMPLES_PER_STUDENT = int(cfg["samples"])
    config.CAPTURE_EVERY_N_FRAMES = int(cfg["capture_every"])
    config.CONSECUTIVE_MATCHES = int(cfg["consecutive"])


# ---------------------------------------------------------------- helpers
def sget(student, *keys):
    """Safely read a field from a student record (dict / Row / None)."""
    for k in keys:
        try:
            v = student[k]
            if v is not None:
                return v
        except Exception:
            continue
    return ""


def cell_text(v):
    if v is None:
        return ""
    if isinstance(v, dt.datetime):
        return v.strftime("%Y-%m-%d") if v.time() == dt.time(0) else v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, dt.date):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, dt.time):
        return v.strftime("%H:%M:%S")
    return str(v)


def all_students():
    """Return [(label, student_record, sample_count)] from the dataset folders."""
    out = []
    root = config.DATASET_DIR
    if not os.path.isdir(root):
        return out
    for d in sorted(os.listdir(root), key=lambda x: (len(x), x)):
        path = os.path.join(root, d)
        if not os.path.isdir(path):
            continue
        label = int(d) if d.isdigit() else d
        try:
            st = database.get_student_by_label(label)
        except Exception:
            st = None
        if st is None:
            continue
        n = len([f for f in os.listdir(path) if f.lower().endswith(".jpg")])
        out.append((label, st, n))
    return out


def open_path(path):
    if sys.platform.startswith("win"):
        os.startfile(path)
    else:
        import subprocess
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])


def open_excel():
    if not os.path.exists(config.ATTENDANCE_XLSX):
        messagebox.showinfo("Excel", "No attendance recorded yet.")
        return
    open_path(config.ATTENDANCE_XLSX)


def beep(widget, enabled=True):
    if not enabled:
        return
    try:
        if sys.platform.startswith("win"):
            import winsound
            winsound.Beep(1000, 120)
        else:
            widget.bell()
    except Exception:
        pass


def retrain_model(app, silent=False):
    """Re-train the face model and report the result in the status bar."""
    try:
        n_students, n_images = face_utils.train_model()
        msg = f"Model trained: {n_students} student(s), {n_images} images."
        app.set_status(msg)
        if not silent:
            messagebox.showinfo("Training", msg)
        return True
    except Exception as exc:
        messagebox.showerror("Training", str(exc))
        return False


def make_card(parent, **kw):
    return tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1, **kw)


# ------------------------------------------------------------------ style
def setup_style(root):
    s = ttk.Style(root)
    try:
        s.theme_use("clam")
    except tk.TclError:
        pass
    s.configure(".", font=(FONT, 10), background=BG, foreground=TEXT)
    s.configure("TFrame", background=BG)
    s.configure("Card.TFrame", background=CARD)
    s.configure("Card.TLabel", background=CARD, foreground=TEXT)
    s.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=(FONT, 9))
    s.configure("Card.TCheckbutton", background=CARD)
    s.map("Card.TCheckbutton", background=[("active", CARD)])
    s.configure("TEntry", fieldbackground="white", bordercolor=BORDER, padding=5)
    s.configure("TSpinbox", fieldbackground="white", bordercolor=BORDER, padding=4)
    s.configure("TCombobox", fieldbackground="white", padding=4)

    s.configure("TButton", padding=(12, 8), background="#e2e8f0", foreground=TEXT,
                borderwidth=0, focusthickness=0, font=(FONT, 10))
    s.map("TButton", background=[("active", "#cbd5e1")])
    s.configure("Accent.TButton", background=ACCENT, foreground="white", font=(FONT, 10, "bold"))
    s.map("Accent.TButton", background=[("active", ACCENT_DARK)])
    s.configure("Success.TButton", background=OK, foreground="white", font=(FONT, 10, "bold"))
    s.map("Success.TButton", background=[("active", "#16a34a")])
    s.configure("Danger.TButton", background=DANGER, foreground="white", font=(FONT, 10, "bold"))
    s.map("Danger.TButton", background=[("active", "#dc2626")])

    s.configure("Treeview", rowheight=30, background="white", fieldbackground="white",
                foreground=TEXT, bordercolor=BORDER, borderwidth=0, font=(FONT, 10))
    s.configure("Treeview.Heading", background="#f8fafc", foreground=MUTED,
                font=(FONT, 9, "bold"), padding=6, borderwidth=0)
    s.map("Treeview", background=[("selected", "#e0e7ff")], foreground=[("selected", TEXT)])
    s.configure("Vertical.TScrollbar", background="#cbd5e1", troughcolor=BG, borderwidth=0)
