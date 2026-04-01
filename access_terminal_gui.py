import tkinter as tk
from tkinter import ttk
import cv2
import json
import numpy as np
import time
import mediapipe as mp
from db_config import get_connection
from datetime import datetime
from PIL import Image, ImageTk

BG_DARK    = "#0A1628"
BG_PANEL   = "#0F2044"
BG_CARD    = "#162950"
BLUE_ACCENT= "#1E6FD9"
BLUE_LIGHT = "#4A9FFF"
TEXT_WHITE = "#FFFFFF"
TEXT_GRAY  = "#8BA3C7"
SUCCESS    = "#00C896"
DANGER     = "#FF4C4C"

MATCH_THRESHOLD = 0.035

mp_face_detection = mp.solutions.face_detection
mp_face_mesh      = mp.solutions.face_mesh
face_detection    = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.7)
face_mesh         = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1,
                                           refine_landmarks=True, min_detection_confidence=0.7)


def get_face_encoding(frame_bgr):
    rgb     = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    if not results.multi_face_landmarks:
        return None
    landmarks = results.multi_face_landmarks[0].landmark
    return np.array([[lm.x, lm.y, lm.z] for lm in landmarks]).flatten()


def load_employees():
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT EmployeeID, FullName, IDNumber, Department, CompanyID, FaceEncoding FROM Employees")
    rows   = cursor.fetchall()
    conn.close()
    employees = []
    for row in rows:
        enc = np.array(json.loads(row[5]))
        employees.append({"id": row[0], "full_name": row[1], "id_number": row[2],
                           "department": row[3], "company_id": row[4], "encoding": enc})
    return employees


def log_access(employee_id, granted):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO AccessLogs (EmployeeID, AccessGranted) VALUES (?, ?)",
                       (employee_id, 1 if granted else 0))
        conn.commit()
        conn.close()
    except: pass


class AccessTerminal:
    def __init__(self, root):
        self.root      = root
        self.root.title("Face Access Terminal")
        self.root.geometry("1000x650")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)
        self.employees   = load_employees()
        self.cap         = cv2.VideoCapture(0)
        self.last_log    = {}
        self.running     = True
        self.build_ui()
        self.update_frame()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=BG_PANEL, height=65)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🔐  FACE ACCESS TERMINAL", font=("Segoe UI", 14, "bold"),
                 bg=BG_PANEL, fg=TEXT_WHITE).pack(side="left", padx=25, pady=15)
        self.clock_var = tk.StringVar()
        tk.Label(hdr, textvariable=self.clock_var, font=("Segoe UI", 11),
                 bg=BG_PANEL, fg=BLUE_LIGHT).pack(side="right", padx=25)
        tk.Button(hdr, text="⬅ Back to Login", font=("Segoe UI", 9),
                  bg=BG_CARD, fg=TEXT_GRAY, relief="flat", cursor="hand2",
                  command=self.on_close).pack(side="right", padx=10, pady=15)
        self.update_clock()

        # Body
        body = tk.Frame(self.root, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=20, pady=15)

        # Camera feed
        cam_frame = tk.Frame(body, bg=BG_CARD, width=560, height=460)
        cam_frame.pack(side="left", padx=(0, 15))
        cam_frame.pack_propagate(False)
        self.cam_label = tk.Label(cam_frame, bg=BG_CARD)
        self.cam_label.pack(fill="both", expand=True)

        # Info panel
        info_panel = tk.Frame(body, bg=BG_DARK, width=360)
        info_panel.pack(side="left", fill="both", expand=True)
        info_panel.pack_propagate(False)

        # Status indicator
        self.status_frame = tk.Frame(info_panel, bg=BG_CARD, height=80)
        self.status_frame.pack(fill="x", pady=(0, 10))
        self.status_frame.pack_propagate(False)
        self.status_icon  = tk.Label(self.status_frame, text="👁", font=("Segoe UI", 25),
                                      bg=BG_CARD, fg=TEXT_GRAY)
        self.status_icon.pack(side="left", padx=15)
        self.status_text  = tk.Label(self.status_frame, text="Scanning...",
                                      font=("Segoe UI", 12, "bold"),
                                      bg=BG_CARD, fg=TEXT_GRAY)
        self.status_text.pack(side="left")

        # Employee info card
        info_card = tk.Frame(info_panel, bg=BG_CARD)
        info_card.pack(fill="x", pady=(0, 10))

        tk.Label(info_card, text="EMPLOYEE INFORMATION",
                 font=("Segoe UI", 8, "bold"), bg=BG_CARD,
                 fg=TEXT_GRAY).pack(anchor="w", padx=15, pady=(12, 5))
        tk.Frame(info_card, bg=BLUE_ACCENT, height=1).pack(fill="x", padx=15)

        self.info_vars = {}
        fields = [("👤 Name",        "name"),
                  ("🪪 ID Number",   "id_number"),
                  ("🏢 Department",  "department"),
                  ("🏷  Company ID", "company_id"),
                  ("🕐 Time",        "time"),
                  ("📅 Date",        "date")]

        for label, key in fields:
            row = tk.Frame(info_card, bg=BG_CARD)
            row.pack(fill="x", padx=15, pady=4)
            tk.Label(row, text=label, font=("Segoe UI", 9),
                     bg=BG_CARD, fg=TEXT_GRAY, width=14, anchor="w").pack(side="left")
            var = tk.StringVar(value="—")
            self.info_vars[key] = var
            tk.Label(row, textvariable=var, font=("Segoe UI", 9, "bold"),
                     bg=BG_CARD, fg=TEXT_WHITE, anchor="w").pack(side="left")

        # Recent log
        tk.Label(info_panel, text="RECENT ACCESS", font=("Segoe UI", 8, "bold"),
                 bg=BG_DARK, fg=TEXT_GRAY).pack(anchor="w", pady=(10, 5))

        style = ttk.Style()
        style.configure("Term.Treeview", background=BG_CARD, foreground=TEXT_WHITE,
                         fieldbackground=BG_CARD, rowheight=26, font=("Segoe UI", 8))
        style.configure("Term.Treeview.Heading", background=BG_PANEL,
                         foreground=BLUE_LIGHT, font=("Segoe UI", 8, "bold"))
        style.map("Term.Treeview", background=[("selected", BLUE_ACCENT)])

        cols = ("Name", "Time", "Status")
        self.log_tree = ttk.Treeview(info_panel, columns=cols, show="headings",
                                      style="Term.Treeview", height=7)
        for col, w in zip(cols, [130, 90, 80]):
            self.log_tree.heading(col, text=col)
            self.log_tree.column(col, width=w)
        self.log_tree.pack(fill="x")

    def update_clock(self):
        self.clock_var.set(datetime.now().strftime("%A  %d %b %Y  |  %H:%M:%S"))
        self.root.after(1000, self.update_clock)

    def update_frame(self):
        if not self.running:
            return

        ret, frame = self.cap.read()
        if ret and frame is not None:
            frame   = cv2.resize(frame, (540, 430))
            encoding = get_face_encoding(frame)

            matched  = False
            if encoding is not None and len(self.employees) > 0:
                distances = [np.linalg.norm(encoding - e["encoding"]) for e in self.employees]
                best_idx  = np.argmin(distances)
                best_dist = distances[best_idx]

                if best_dist < MATCH_THRESHOLD:
                    emp = self.employees[best_idx]
                    matched = True
                    now = datetime.now()

                    # Update info panel
                    self.info_vars["name"].set(emp["full_name"])
                    self.info_vars["id_number"].set(emp["id_number"])
                    self.info_vars["department"].set(emp["department"])
                    self.info_vars["company_id"].set(emp["company_id"])
                    self.info_vars["time"].set(now.strftime("%H:%M:%S"))
                    self.info_vars["date"].set(now.strftime("%Y-%m-%d"))

                    self.status_frame.config(bg="#0A2E1A")
                    self.status_icon.config(text="✅", bg="#0A2E1A", fg=SUCCESS)
                    self.status_text.config(text="ACCESS GRANTED", bg="#0A2E1A", fg=SUCCESS)

                    cv2.rectangle(frame, (10, 10), (530, 420), (0, 200, 100), 3)

                    # Log once per 5 sec
                    last = self.last_log.get(emp["id"], 0)
                    if time.time() - last > 5:
                        log_access(emp["id"], True)
                        self.last_log[emp["id"]] = time.time()
                        self.add_log_entry(emp["full_name"], now.strftime("%H:%M:%S"), "GRANTED")

            if not matched and encoding is not None:
                self.status_frame.config(bg="#2E0A0A")
                self.status_icon.config(text="❌", bg="#2E0A0A", fg=DANGER)
                self.status_text.config(text="ACCESS DENIED", bg="#2E0A0A", fg=DANGER)
                for key in self.info_vars:
                    self.info_vars[key].set("—")
                cv2.rectangle(frame, (10, 10), (530, 420), (0, 0, 220), 3)

            elif encoding is None:
                self.status_frame.config(bg=BG_CARD)
                self.status_icon.config(text="👁", bg=BG_CARD, fg=TEXT_GRAY)
                self.status_text.config(text="Scanning...", bg=BG_CARD, fg=TEXT_GRAY)

            # Display in Tkinter
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=img)
            self.cam_label.imgtk = imgtk
            self.cam_label.config(image=imgtk)

        self.root.after(30, self.update_frame)

    def add_log_entry(self, name, time_str, status):
        tag = "granted" if status == "GRANTED" else "denied"
        self.log_tree.insert("", 0, values=(name, time_str, status), tags=(tag,))
        self.log_tree.tag_configure("granted", foreground=SUCCESS)
        self.log_tree.tag_configure("denied",  foreground=DANGER)
        # Keep only last 7
        children = self.log_tree.get_children()
        if len(children) > 7:
            self.log_tree.delete(children[-1])

    def on_close(self):
        self.running = False
        self.cap.release()
        self.root.destroy()
        import main_app
        main_app.launch()


def launch():
    root = tk.Tk()
    AccessTerminal(root)
    root.mainloop()


if __name__ == "__main__":
    launch()