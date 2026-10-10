"""Automated Attendance via Face Recognition - main window.

This is the file you run:   python guimain.py

It builds the sidebar + header + status bar and connects the pages:
    gui_dashboard.py  -> Dashboard (camera, enrol, attendance)
    gui_students.py   -> Students  (list, preview, delete)
    gui_reports.py    -> Reports   (Excel viewer, CSV export)
    gui_settings.py   -> Settings  (camera / recognition options)
    gui_common.py     -> shared theme, settings storage and helpers
"""
import os
import sys

# Ensure Tcl/Tk libraries can be located when running in virtual environments on Windows
if sys.platform.startswith("win"):
    base_prefix = sys.base_prefix
    tcl_dir = os.path.join(base_prefix, "tcl", "tcl8.6")
    tk_dir = os.path.join(base_prefix, "tcl", "tk8.6")
    if os.path.exists(tcl_dir) and "TCL_LIBRARY" not in os.environ:
        os.environ["TCL_LIBRARY"] = tcl_dir
    if os.path.exists(tk_dir) and "TK_LIBRARY" not in os.environ:
        os.environ["TK_LIBRARY"] = tk_dir

import datetime as dt
import tkinter as tk

import database
from gui_common import (ACCENT, BG, BORDER, CARD, FONT, FONT_HEAD, MUTED, SIDEBAR, SIDEBAR_HOVER, TEXT,
                        apply_settings, load_settings, setup_style)
from gui_dashboard import DashboardPage
from gui_reports import ReportsPage
from gui_settings import SettingsPage
from gui_students import StudentsPage

NAV = (("dashboard", "▣   Dashboard", "Dashboard", DashboardPage),
       ("students", "☺   Students", "Students", StudentsPage),
       ("reports", "☰   Reports", "Attendance Reports", ReportsPage),
       ("settings", "⚙   Settings", "Settings", SettingsPage))


class AttendanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Automated Attendance via Face Recognition")
        self.geometry("1280x740")
        self.minsize(1100, 680)
        self.configure(bg=BG)

        self.cfg = load_settings()          # shared (mutable) settings dict
        apply_settings(self.cfg)
        database.init_storage()
        setup_style(self)

        self._build_shell()
        self._build_pages()
        self.show_page("dashboard")
        self._tick()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----------------------------------------------------------------- shell
    def _build_shell(self):
        side = tk.Frame(self, bg=SIDEBAR, width=230)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        tk.Label(side, text="●  FaceAttend", bg=SIDEBAR, fg="white",
                 font=(FONT_HEAD, 17, "bold"), anchor="w").pack(fill="x", padx=22, pady=(26, 2))
        tk.Label(side, text="Smart attendance system", bg=SIDEBAR, fg="#94a3b8",
                 font=(FONT, 9), anchor="w").pack(fill="x", padx=24, pady=(0, 26))

        self.nav_btns = {}
        for key, text, _title, _cls in NAV:
            b = tk.Button(side, text=text, anchor="w", bg=SIDEBAR, fg="#cbd5e1",
                          activebackground=SIDEBAR_HOVER, activeforeground="white",
                          relief="flat", bd=0, font=(FONT, 11), padx=22, pady=11,
                          cursor="hand2", command=lambda k=key: self.show_page(k))
            b.pack(fill="x", pady=1)
            b.bind("<Enter>", lambda e, b=b: b.configure(bg=SIDEBAR_HOVER) if b["bg"] == SIDEBAR else None)
            b.bind("<Leave>", lambda e, b=b: b.configure(bg=SIDEBAR) if b["bg"] == SIDEBAR_HOVER else None)
            self.nav_btns[key] = b

        tk.Label(side, text="v2.0  •  OpenCV + Tkinter", bg=SIDEBAR, fg="#475569",
                 font=(FONT, 8)).pack(side="bottom", pady=14)

        main = tk.Frame(self, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        header = tk.Frame(main, bg=BG)
        header.pack(fill="x", padx=24, pady=(18, 0))
        self.page_title = tk.Label(header, text="", bg=BG, fg=TEXT, font=(FONT_HEAD, 22, "bold"))
        self.page_title.pack(side="left")
        self.clock = tk.StringVar()
        tk.Label(header, textvariable=self.clock, bg=BG, fg=MUTED, font=(FONT, 11)).pack(side="right")

        bar = tk.Frame(main, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        bar.pack(fill="x", side="bottom")
        self.status = tk.StringVar(value="Ready.")
        tk.Label(bar, textvariable=self.status, bg=CARD, fg=MUTED, anchor="w",
                 font=(FONT, 9), padx=14, pady=6).pack(fill="x")

        self.container = tk.Frame(main, bg=BG)
        self.container.pack(fill="both", expand=True, padx=24, pady=14)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def _build_pages(self):
        self.pages, self.titles = {}, {}
        for key, _text, title, cls in NAV:
            page = cls(self.container, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = page
            self.titles[key] = title

    # ------------------------------------------------------------ public API
    def show_page(self, key):
        dash = self.pages["dashboard"]
        if key != "dashboard" and dash.mode != "idle":
            dash.stop()
        self.pages[key].tkraise()
        self.page_title.configure(text=self.titles[key])
        for k, b in self.nav_btns.items():
            b.configure(bg=ACCENT if k == key else SIDEBAR,
                        fg="white" if k == key else "#cbd5e1")
        self.pages[key].on_show()

    def set_status(self, text):
        self.status.set(text)

    # -------------------------------------------------------------- internals
    def _tick(self):
        self.clock.set(dt.datetime.now().strftime("%A, %d %B %Y   %H:%M:%S"))
        self.after(1000, self._tick)

    def _on_close(self):
        self.pages["dashboard"].stop()
        self.destroy()


def main():
    AttendanceApp().mainloop()


if __name__ == "__main__":
    main()
