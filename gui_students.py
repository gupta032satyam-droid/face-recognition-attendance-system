"""Students page: list, search, preview face samples, delete, re-train."""
import os
import shutil
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

import config
import database
import face_utils
from gui_common import BG, CARD, FONT, MUTED, all_students, make_card, retrain_model, sget


class StudentsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        card = make_card(self)
        card.pack(fill="both", expand=True)

        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x", padx=14, pady=12)
        tk.Label(top, text="Search", bg=CARD, fg=MUTED, font=(FONT, 10)).pack(side="left")
        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(top, textvariable=self.search, width=30).pack(side="left", padx=8)
        self.count = tk.StringVar()
        tk.Label(top, textvariable=self.count, bg=CARD, fg=MUTED).pack(side="left", padx=10)
        ttk.Button(top, text="Delete selected", style="Danger.TButton",
                   command=self.delete_student).pack(side="right")
        ttk.Button(top, text="Re-train model",
                   command=lambda: retrain_model(self.app)).pack(side="right", padx=8)
        ttk.Button(top, text="Preview face", command=self.preview_student).pack(side="right")

        cols = ("label", "roll", "name", "email", "samples")
        self.table = ttk.Treeview(card, columns=cols, show="headings", selectmode="browse")
        for c, t, w in (("label", "ID", 60), ("roll", "Roll No", 120), ("name", "Name", 240),
                        ("email", "Email", 280), ("samples", "Face samples", 110)):
            self.table.heading(c, text=t)
            self.table.column(c, width=w, anchor="w")
        sb = ttk.Scrollbar(card, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0, 6), pady=(0, 10))
        self.table.pack(fill="both", expand=True, padx=(14, 0), pady=(0, 10))
        self.table.bind("<Double-1>", lambda e: self.preview_student())

    def on_show(self):
        self.refresh()

    def refresh(self):
        q = self.search.get().strip().lower()
        self.table.delete(*self.table.get_children())
        shown = 0
        for label, st, n in all_students():
            row = (label, sget(st, "roll", "roll_no", "rollno"), sget(st, "name"),
                   sget(st, "email"), n)
            if q and q not in " ".join(str(x).lower() for x in row):
                continue
            self.table.insert("", "end", values=row)
            shown += 1
        self.count.set(f"{shown} student(s)")

    def _selected_label(self):
        sel = self.table.selection()
        if not sel:
            messagebox.showinfo("Students", "Select a student first.")
            return None
        val = self.table.item(sel[0], "values")[0]
        return int(val) if str(val).isdigit() else val

    def preview_student(self):
        label = self._selected_label()
        if label is None:
            return
        folder = os.path.join(config.DATASET_DIR, str(label))
        files = (sorted(f for f in os.listdir(folder) if f.lower().endswith(".jpg"))
                 if os.path.isdir(folder) else [])
        if not files:
            messagebox.showinfo("Preview", "No face samples found.")
            return
        win = tk.Toplevel(self)
        win.title(f"Face samples - ID {label}")
        win.configure(bg=CARD)
        win.resizable(False, False)
        grid = tk.Frame(win, bg=CARD)
        grid.pack(padx=12, pady=12)
        imgs = []
        for i, f in enumerate(files[:12]):
            im = Image.open(os.path.join(folder, f)).convert("L").resize((110, 110))
            ph = ImageTk.PhotoImage(im)
            imgs.append(ph)
            tk.Label(grid, image=ph, bg=CARD).grid(row=i // 4, column=i % 4, padx=4, pady=4)
        win.imgs = imgs                      # keep references

    def delete_student(self):
        label = self._selected_label()
        if label is None:
            return
        if not messagebox.askyesno("Delete", "Delete this student and all face samples?"):
            return
        try:
            database.remove_student(label)
        except Exception as exc:
            messagebox.showerror("Delete", str(exc))
            return
        shutil.rmtree(os.path.join(config.DATASET_DIR, str(label)), ignore_errors=True)
        try:
            face_utils.train_model()
            self.app.set_status("Student deleted and model re-trained.")
        except Exception:
            self.app.set_status("Student deleted. (Add students to re-train the model.)")
        self.refresh()
