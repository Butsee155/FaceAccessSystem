import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import numpy as np
import time
import cv2
import mediapipe as mp
from db_config import get_connection
from datetime import datetime
import openpyxl
import csv
import os

BG_DARK    = "#0A1628"
BG_PANEL   = "#0F2044"
BG_CARD    = "#162950"
BLUE_ACCENT= "#1E6FD9"
BLUE_LIGHT = "#4A9FFF"
TEXT_WHITE = "#FFFFFF"
TEXT_GRAY  = "#8BA3C7"
BTN_HOVER  = "#2580F0"
SUCCESS    = "#00C896"
DANGER     = "#FF4C4C"
WARNING    = "#FFB84C"

mp_face_detection = mp.solutions.face_detection
mp_face_mesh      = mp.solutions.face_mesh
face_detection    = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.7)
face_mesh         = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1,
                                           refine_landmarks=True, min_detection_confidence=0.7)


def get_face_encoding(frame_bgr):
    rgb     = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    if not results.multi_face_landmarks:
        return None, 0
    if len(results.multi_face_landmarks) > 1:
        return None, len(results.multi_face_landmarks)
    landmarks = results.multi_face_landmarks[0].landmark
    encoding  = np.array([[lm.x, lm.y, lm.z] for lm in landmarks]).flatten()
    return encoding, 1


class AdminPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Access System — Admin Dashboard")
        self.root.geometry("1100x700")
        self.root.configure(bg=BG_DARK)
        self.center_window(1100, 700)
        self.build_ui()
        self.load_employees()
        self.load_stats()

    def center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def build_ui(self):
        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = tk.Frame(self.root, bg=BG_PANEL, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="🔐", font=("Segoe UI", 30),
                 bg=BG_PANEL, fg=BLUE_LIGHT).pack(pady=(30, 5))
        tk.Label(sidebar, text="FACE ACCESS", font=("Segoe UI", 12, "bold"),
                 bg=BG_PANEL, fg=TEXT_WHITE).pack()
        tk.Label(sidebar, text="Admin Dashboard", font=("Segoe UI", 9),
                 bg=BG_PANEL, fg=TEXT_GRAY).pack(pady=(0, 30))

        tk.Frame(sidebar, bg=BLUE_ACCENT, height=1).pack(fill="x", padx=20)

        # Nav buttons
        self.nav_btns = {}
        nav_items = [
            ("📊  Dashboard",    "dashboard"),
            ("👥  Employees",    "employees"),
            ("➕  Add Employee", "add"),
            ("📋  Access Logs",  "logs"),
            ("📤  Export",       "export"),
        ]
        for label, key in nav_items:
            btn = tk.Button(sidebar, text=label, font=("Segoe UI", 10),
                            bg=BG_PANEL, fg=TEXT_GRAY, relief="flat",
                            cursor="hand2", anchor="w", padx=20,
                            activebackground=BG_CARD, activeforeground=TEXT_WHITE,
                            command=lambda k=key: self.show_page(k))
            btn.pack(fill="x", ipady=10, pady=1)
            self.nav_btns[key] = btn

        # Logout
        tk.Frame(sidebar, bg=BG_CARD, height=1).pack(fill="x", padx=20, pady=20)
        tk.Button(sidebar, text="🚪  Logout", font=("Segoe UI", 10),
                  bg=BG_PANEL, fg=DANGER, relief="flat", cursor="hand2",
                  anchor="w", padx=20, activebackground=BG_CARD,
                  command=self.logout).pack(fill="x", ipady=10)

        # ── Main Content ─────────────────────────────────────────────────────
        self.content = tk.Frame(self.root, bg=BG_DARK)
        self.content.pack(side="left", fill="both", expand=True)

        # Build all pages
        self.pages = {}
        self.build_dashboard_page()
        self.build_employees_page()
        self.build_add_page()
        self.build_logs_page()
        self.build_export_page()

        self.show_page("dashboard")

    # ── Page Navigation ───────────────────────────────────────────────────────
    def show_page(self, key):
        for k, frame in self.pages.items():
            frame.pack_forget()
        for k, btn in self.nav_btns.items():
            btn.config(bg=BG_PANEL, fg=TEXT_GRAY)
        self.pages[key].pack(fill="both", expand=True)
        self.nav_btns[key].config(bg=BG_CARD, fg=TEXT_WHITE)
        if key == "logs":
            self.load_logs()
        if key == "dashboard":
            self.load_stats()

    # ── Dashboard Page ────────────────────────────────────────────────────────
    def build_dashboard_page(self):
        page = tk.Frame(self.content, bg=BG_DARK)
        self.pages["dashboard"] = page

        # Header
        hdr = tk.Frame(page, bg=BG_PANEL, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📊  Dashboard Overview", font=("Segoe UI", 14, "bold"),
                 bg=BG_PANEL, fg=TEXT_WHITE).pack(side="left", padx=25, pady=20)
        tk.Label(hdr, textvariable=tk.StringVar(value=datetime.now().strftime("%A, %d %B %Y")),
                 font=("Segoe UI", 9), bg=BG_PANEL, fg=TEXT_GRAY).pack(side="right", padx=25)

        # Stats cards
        cards_frame = tk.Frame(page, bg=BG_DARK)
        cards_frame.pack(fill="x", padx=25, pady=20)

        self.stat_vars = {}
        stats = [
            ("👥", "Total Employees", "total_emp",  BLUE_ACCENT),
            ("✅", "Access Today",    "access_today", SUCCESS),
            ("❌", "Denied Today",    "denied_today", DANGER),
            ("📅", "Total Logs",      "total_logs",  WARNING),
        ]
        for i, (icon, label, key, color) in enumerate(stats):
            card = tk.Frame(cards_frame, bg=BG_CARD, width=180, height=110)
            card.grid(row=0, column=i, padx=8, sticky="nsew")
            card.pack_propagate(False)
            cards_frame.columnconfigure(i, weight=1)

            tk.Frame(card, bg=color, width=4).pack(side="left", fill="y")
            inner = tk.Frame(card, bg=BG_CARD)
            inner.pack(side="left", fill="both", expand=True, padx=15, pady=15)

            tk.Label(inner, text=icon, font=("Segoe UI", 22),
                     bg=BG_CARD, fg=color).pack(anchor="w")
            var = tk.StringVar(value="0")
            self.stat_vars[key] = var
            tk.Label(inner, textvariable=var, font=("Segoe UI", 22, "bold"),
                     bg=BG_CARD, fg=TEXT_WHITE).pack(anchor="w")
            tk.Label(inner, text=label, font=("Segoe UI", 8),
                     bg=BG_CARD, fg=TEXT_GRAY).pack(anchor="w")

        # Recent logs table
        tk.Label(page, text="Recent Access Logs", font=("Segoe UI", 11, "bold"),
                 bg=BG_DARK, fg=TEXT_WHITE).pack(anchor="w", padx=25, pady=(10, 5))

        tbl_frame = tk.Frame(page, bg=BG_DARK)
        tbl_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dashboard.Treeview", background=BG_CARD, foreground=TEXT_WHITE,
                         fieldbackground=BG_CARD, rowheight=32,
                         font=("Segoe UI", 9))
        style.configure("Dashboard.Treeview.Heading", background=BG_PANEL,
                         foreground=BLUE_LIGHT, font=("Segoe UI", 9, "bold"))
        style.map("Dashboard.Treeview", background=[("selected", BLUE_ACCENT)])

        cols = ("Name", "Department", "Time", "Status")
        self.dash_tree = ttk.Treeview(tbl_frame, columns=cols, show="headings",
                                       style="Dashboard.Treeview", height=10)
        for col in cols:
            self.dash_tree.heading(col, text=col)
            self.dash_tree.column(col, width=180)
        self.dash_tree.pack(fill="both", expand=True)

    def load_stats(self):
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            today  = datetime.now().strftime("%Y-%m-%d")

            cursor.execute("SELECT COUNT(*) FROM Employees")
            self.stat_vars["total_emp"].set(str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM AccessLogs WHERE CAST(AccessTime AS DATE) = ? AND AccessGranted=1", today)
            self.stat_vars["access_today"].set(str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM AccessLogs WHERE CAST(AccessTime AS DATE) = ? AND AccessGranted=0", today)
            self.stat_vars["denied_today"].set(str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM AccessLogs")
            self.stat_vars["total_logs"].set(str(cursor.fetchone()[0]))

            # Recent logs
            cursor.execute("""
                SELECT TOP 10 e.FullName, e.Department, l.AccessTime,
                CASE WHEN l.AccessGranted=1 THEN 'GRANTED' ELSE 'DENIED' END
                FROM AccessLogs l JOIN Employees e ON l.EmployeeID=e.EmployeeID
                ORDER BY l.AccessTime DESC
            """)
            for item in self.dash_tree.get_children():
                self.dash_tree.delete(item)
            for row in cursor.fetchall():
                tag = "granted" if row[3] == "GRANTED" else "denied"
                self.dash_tree.insert("", "end", values=row, tags=(tag,))
            self.dash_tree.tag_configure("granted", foreground=SUCCESS)
            self.dash_tree.tag_configure("denied",  foreground=DANGER)
            conn.close()
        except Exception as e:
            print(f"Stats error: {e}")

    # ── Employees Page ────────────────────────────────────────────────────────
    def build_employees_page(self):
        page = tk.Frame(self.content, bg=BG_DARK)
        self.pages["employees"] = page

        hdr = tk.Frame(page, bg=BG_PANEL, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="👥  Employee Management", font=("Segoe UI", 14, "bold"),
                 bg=BG_PANEL, fg=TEXT_WHITE).pack(side="left", padx=25, pady=20)

        # Search bar
        search_frame = tk.Frame(page, bg=BG_DARK)
        search_frame.pack(fill="x", padx=25, pady=15)
        tk.Label(search_frame, text="🔍", bg=BG_DARK, fg=TEXT_GRAY,
                 font=("Segoe UI", 12)).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self.filter_employees())
        tk.Entry(search_frame, textvariable=self.search_var, bg=BG_CARD,
                 fg=TEXT_WHITE, insertbackground=TEXT_WHITE, relief="flat",
                 font=("Segoe UI", 10), bd=0).pack(side="left", fill="x",
                 expand=True, ipady=8, padx=10)

        # Table
        tbl = tk.Frame(page, bg=BG_DARK)
        tbl.pack(fill="both", expand=True, padx=25, pady=(0, 10))

        style = ttk.Style()
        style.configure("Emp.Treeview", background=BG_CARD, foreground=TEXT_WHITE,
                         fieldbackground=BG_CARD, rowheight=32, font=("Segoe UI", 9))
        style.configure("Emp.Treeview.Heading", background=BG_PANEL,
                         foreground=BLUE_LIGHT, font=("Segoe UI", 9, "bold"))
        style.map("Emp.Treeview", background=[("selected", BLUE_ACCENT)])

        cols = ("ID", "Full Name", "ID Number", "Department", "Company ID", "Registered")
        self.emp_tree = ttk.Treeview(tbl, columns=cols, show="headings",
                                      style="Emp.Treeview")
        widths = [50, 200, 130, 150, 100, 150]
        for col, w in zip(cols, widths):
            self.emp_tree.heading(col, text=col)
            self.emp_tree.column(col, width=w)

        sb = ttk.Scrollbar(tbl, orient="vertical", command=self.emp_tree.yview)
        self.emp_tree.configure(yscrollcommand=sb.set)
        self.emp_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Delete button
        tk.Button(page, text="🗑  Delete Selected Employee",
                  font=("Segoe UI", 10), bg=DANGER, fg=TEXT_WHITE,
                  relief="flat", cursor="hand2", padx=20,
                  activebackground="#CC0000",
                  command=self.delete_employee).pack(pady=10)

    def load_employees(self):
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT EmployeeID, FullName, IDNumber, Department, CompanyID, RegisteredDate FROM Employees ORDER BY EmployeeID DESC")
            self.all_employees = cursor.fetchall()
            conn.close()
            self.filter_employees()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def filter_employees(self):
        query = self.search_var.get().lower()
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
        for row in self.all_employees:
            if query in str(row).lower():
                self.emp_tree.insert("", "end", values=row)

    def delete_employee(self):
        sel = self.emp_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Please select an employee to delete.")
            return
        values = self.emp_tree.item(sel[0])["values"]
        emp_id, name = values[0], values[1]
        if messagebox.askyesno("Confirm Delete", f"Delete employee '{name}'?\nThis cannot be undone."):
            try:
                conn   = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM AccessLogs WHERE EmployeeID=?", emp_id)
                cursor.execute("DELETE FROM Employees WHERE EmployeeID=?", emp_id)
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", f"Employee '{name}' deleted.")
                self.load_employees()
                self.load_stats()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── Add Employee Page ─────────────────────────────────────────────────────
    def build_add_page(self):
        page = tk.Frame(self.content, bg=BG_DARK)
        self.pages["add"] = page

        hdr = tk.Frame(page, bg=BG_PANEL, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="➕  Register New Employee", font=("Segoe UI", 14, "bold"),
                 bg=BG_PANEL, fg=TEXT_WHITE).pack(side="left", padx=25, pady=20)

        form = tk.Frame(page, bg=BG_DARK, padx=60)
        form.pack(fill="both", expand=True, pady=20)

        self.add_vars = {}
        fields = [
            ("Full Name",    "full_name"),
            ("ID Number",    "id_number"),
            ("Department",   "department"),
            ("Company ID",   "company_id"),
        ]
        for label, key in fields:
            tk.Label(form, text=label.upper(), font=("Segoe UI", 8, "bold"),
                     bg=BG_DARK, fg=TEXT_GRAY).pack(anchor="w", pady=(10, 3))
            var = tk.StringVar()
            self.add_vars[key] = var
            f = tk.Frame(form, bg=BG_CARD)
            f.pack(fill="x")
            tk.Entry(f, textvariable=var, bg=BG_CARD, fg=TEXT_WHITE,
                     insertbackground=TEXT_WHITE, relief="flat",
                     font=("Segoe UI", 11), bd=0).pack(fill="x", ipady=10, padx=15)

        # Face capture status
        self.face_status_var = tk.StringVar(value="⚪  No face captured yet")
        tk.Label(form, textvariable=self.face_status_var,
                 font=("Segoe UI", 10), bg=BG_DARK, fg=TEXT_GRAY).pack(pady=(20, 5))

        self.captured_encoding = None

        btn_row = tk.Frame(form, bg=BG_DARK)
        btn_row.pack(fill="x", pady=10)

        tk.Button(btn_row, text="📷  Capture Face",
                  font=("Segoe UI", 10, "bold"), bg=BLUE_ACCENT, fg=TEXT_WHITE,
                  relief="flat", cursor="hand2", padx=20,
                  activebackground=BTN_HOVER,
                  command=self.capture_face).pack(side="left", ipady=10, padx=(0, 10))

        tk.Button(btn_row, text="💾  Save Employee",
                  font=("Segoe UI", 10, "bold"), bg=SUCCESS, fg="#000000",
                  relief="flat", cursor="hand2", padx=20,
                  command=self.save_employee).pack(side="left", ipady=10)

        tk.Button(btn_row, text="🔄  Clear Form",
                  font=("Segoe UI", 10), bg=BG_CARD, fg=TEXT_GRAY,
                  relief="flat", cursor="hand2", padx=20,
                  command=self.clear_form).pack(side="right", ipady=10)

    def capture_face(self):
        self.face_status_var.set("📷  Opening camera...")
        self.root.update()

        cap = cv2.VideoCapture(0)
        time.sleep(0.5)
        encoding = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame   = cv2.resize(frame, (640, 480))
            display = frame.copy()
            rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            det_res = face_detection.process(rgb)

            if det_res.detections:
                cv2.putText(display, "Face detected! Press SPACE to capture",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,255,0), 2)
            else:
                cv2.putText(display, "No face - look at camera",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,0,255), 2)
            cv2.putText(display, "Press Q to cancel", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,0), 1)
            cv2.imshow("Capture Face", display)

            key = cv2.waitKey(1) & 0xFF
            if key == 32:
                enc, count = get_face_encoding(frame)
                if count == 0:
                    cv2.putText(display, "No face!", (250, 240),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                elif count > 1:
                    cv2.putText(display, "Multiple faces!", (200, 240),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                else:
                    encoding = enc
                    break
            elif key == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        if encoding is not None:
            self.captured_encoding = encoding
            self.face_status_var.set("✅  Face captured successfully!")
        else:
            self.face_status_var.set("❌  Face capture failed. Try again.")

    def save_employee(self):
        full_name  = self.add_vars["full_name"].get().strip()
        id_number  = self.add_vars["id_number"].get().strip()
        department = self.add_vars["department"].get().strip()
        company_id = self.add_vars["company_id"].get().strip()

        if not all([full_name, id_number, department, company_id]):
            messagebox.showwarning("Missing Fields", "Please fill all fields.")
            return
        if self.captured_encoding is None:
            messagebox.showwarning("No Face", "Please capture face data first.")
            return

        encoding_json = json.dumps(self.captured_encoding.tolist())
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Employees WHERE IDNumber=?", id_number)
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Duplicate", f"ID Number '{id_number}' already exists.")
                conn.close()
                return
            cursor.execute("""
                INSERT INTO Employees (CompanyID, FullName, IDNumber, Department, FaceEncoding)
                VALUES (?, ?, ?, ?, ?)
            """, (company_id, full_name, id_number, department, encoding_json))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"Employee '{full_name}' registered!")
            self.clear_form()
            self.load_employees()
            self.load_stats()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_form(self):
        for var in self.add_vars.values():
            var.set("")
        self.captured_encoding = None
        self.face_status_var.set("⚪  No face captured yet")

    # ── Access Logs Page ──────────────────────────────────────────────────────
    def build_logs_page(self):
        page = tk.Frame(self.content, bg=BG_DARK)
        self.pages["logs"] = page

        hdr = tk.Frame(page, bg=BG_PANEL, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📋  Access Logs", font=("Segoe UI", 14, "bold"),
                 bg=BG_PANEL, fg=TEXT_WHITE).pack(side="left", padx=25, pady=20)
        tk.Button(hdr, text="🔄 Refresh", font=("Segoe UI", 9),
                  bg=BLUE_ACCENT, fg=TEXT_WHITE, relief="flat", cursor="hand2",
                  command=self.load_logs).pack(side="right", padx=25, pady=20)

        tbl = tk.Frame(page, bg=BG_DARK)
        tbl.pack(fill="both", expand=True, padx=25, pady=15)

        style = ttk.Style()
        style.configure("Logs.Treeview", background=BG_CARD, foreground=TEXT_WHITE,
                         fieldbackground=BG_CARD, rowheight=30, font=("Segoe UI", 9))
        style.configure("Logs.Treeview.Heading", background=BG_PANEL,
                         foreground=BLUE_LIGHT, font=("Segoe UI", 9, "bold"))
        style.map("Logs.Treeview", background=[("selected", BLUE_ACCENT)])

        cols = ("Log ID", "Full Name", "ID Number", "Department", "Company ID", "Access Time", "Status")
        self.log_tree = ttk.Treeview(tbl, columns=cols, show="headings",
                                      style="Logs.Treeview")
        widths = [60, 180, 120, 140, 100, 160, 90]
        for col, w in zip(cols, widths):
            self.log_tree.heading(col, text=col)
            self.log_tree.column(col, width=w)

        sb = ttk.Scrollbar(tbl, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=sb.set)
        self.log_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def load_logs(self):
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 200 l.LogID, e.FullName, e.IDNumber, e.Department,
                       e.CompanyID, l.AccessTime,
                       CASE WHEN l.AccessGranted=1 THEN 'GRANTED' ELSE 'DENIED' END
                FROM AccessLogs l JOIN Employees e ON l.EmployeeID=e.EmployeeID
                ORDER BY l.AccessTime DESC
            """)
            for item in self.log_tree.get_children():
                self.log_tree.delete(item)
            for row in cursor.fetchall():
                tag = "granted" if row[6] == "GRANTED" else "denied"
                self.log_tree.insert("", "end", values=row, tags=(tag,))
            self.log_tree.tag_configure("granted", foreground=SUCCESS)
            self.log_tree.tag_configure("denied",  foreground=DANGER)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ── Export Page ───────────────────────────────────────────────────────────
    def build_export_page(self):
        page = tk.Frame(self.content, bg=BG_DARK)
        self.pages["export"] = page

        hdr = tk.Frame(page, bg=BG_PANEL, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📤  Export Reports", font=("Segoe UI", 14, "bold"),
                 bg=BG_PANEL, fg=TEXT_WHITE).pack(side="left", padx=25, pady=20)

        cards = tk.Frame(page, bg=BG_DARK)
        cards.pack(fill="both", expand=True, padx=40, pady=40)

        exports = [
            ("📊", "Employee List",       "Export all employees to Excel/CSV",   self.export_employees),
            ("📋", "Access Logs",         "Export all access logs to Excel/CSV",  self.export_logs),
            ("📅", "Today's Report",      "Export today's access activity",       self.export_today),
            ("📈", "Full Report",         "Export complete system report",        self.export_full),
        ]
        for i, (icon, title, desc, cmd) in enumerate(exports):
            card = tk.Frame(cards, bg=BG_CARD, width=220, height=180)
            card.grid(row=i//2, column=i%2, padx=15, pady=15, sticky="nsew")
            card.pack_propagate(False)
            cards.columnconfigure(i%2, weight=1)

            tk.Label(card, text=icon, font=("Segoe UI", 35),
                     bg=BG_CARD, fg=BLUE_LIGHT).pack(pady=(25, 5))
            tk.Label(card, text=title, font=("Segoe UI", 11, "bold"),
                     bg=BG_CARD, fg=TEXT_WHITE).pack()
            tk.Label(card, text=desc, font=("Segoe UI", 8),
                     bg=BG_CARD, fg=TEXT_GRAY).pack(pady=3)

            btn_row = tk.Frame(card, bg=BG_CARD)
            btn_row.pack(pady=8)
            tk.Button(btn_row, text="Excel", font=("Segoe UI", 9),
                      bg=SUCCESS, fg="#000", relief="flat", cursor="hand2",
                      padx=10, command=lambda c=cmd: c("xlsx")).pack(side="left", padx=3)
            tk.Button(btn_row, text="CSV", font=("Segoe UI", 9),
                      bg=BLUE_ACCENT, fg=TEXT_WHITE, relief="flat", cursor="hand2",
                      padx=10, command=lambda c=cmd: c("csv")).pack(side="left", padx=3)

    def _save_file(self, fmt, default_name):
        ext  = ".xlsx" if fmt == "xlsx" else ".csv"
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")],
            initialfile=default_name)
        return path

    def _write(self, path, headers, rows, fmt):
        if fmt == "xlsx":
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(headers)
            for row in rows:
                ws.append(list(row))
            wb.save(path)
        else:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(headers)
                w.writerows(rows)
        messagebox.showinfo("Exported", f"File saved:\n{path}")
        os.startfile(path)

    def export_employees(self, fmt):
        path = self._save_file(fmt, "Employees")
        if not path: return
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT EmployeeID, FullName, IDNumber, Department, CompanyID, RegisteredDate FROM Employees")
        rows = cursor.fetchall()
        conn.close()
        self._write(path, ["ID","Full Name","ID Number","Department","Company ID","Registered"], rows, fmt)

    def export_logs(self, fmt):
        path = self._save_file(fmt, "AccessLogs")
        if not path: return
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.LogID, e.FullName, e.IDNumber, e.Department, e.CompanyID,
                   l.AccessTime, CASE WHEN l.AccessGranted=1 THEN 'GRANTED' ELSE 'DENIED' END
            FROM AccessLogs l JOIN Employees e ON l.EmployeeID=e.EmployeeID
            ORDER BY l.AccessTime DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        self._write(path, ["Log ID","Full Name","ID Number","Department","Company ID","Time","Status"], rows, fmt)

    def export_today(self, fmt):
        path = self._save_file(fmt, f"TodayReport_{datetime.now().strftime('%Y%m%d')}")
        if not path: return
        today = datetime.now().strftime("%Y-%m-%d")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.LogID, e.FullName, e.IDNumber, e.Department, e.CompanyID,
                   l.AccessTime, CASE WHEN l.AccessGranted=1 THEN 'GRANTED' ELSE 'DENIED' END
            FROM AccessLogs l JOIN Employees e ON l.EmployeeID=e.EmployeeID
            WHERE CAST(l.AccessTime AS DATE) = ?
            ORDER BY l.AccessTime DESC
        """, today)
        rows = cursor.fetchall()
        conn.close()
        self._write(path, ["Log ID","Full Name","ID Number","Department","Company ID","Time","Status"], rows, fmt)

    def export_full(self, fmt):
        path = self._save_file(fmt, f"FullReport_{datetime.now().strftime('%Y%m%d')}")
        if not path: return
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.FullName, e.IDNumber, e.Department, e.CompanyID,
                   COUNT(l.LogID) AS TotalAccess,
                   SUM(CASE WHEN l.AccessGranted=1 THEN 1 ELSE 0 END) AS Granted,
                   SUM(CASE WHEN l.AccessGranted=0 THEN 1 ELSE 0 END) AS Denied,
                   MAX(l.AccessTime) AS LastAccess
            FROM Employees e LEFT JOIN AccessLogs l ON e.EmployeeID=l.EmployeeID
            GROUP BY e.FullName, e.IDNumber, e.Department, e.CompanyID
        """)
        rows = cursor.fetchall()
        conn.close()
        self._write(path, ["Full Name","ID Number","Department","Company ID","Total Access","Granted","Denied","Last Access"], rows, fmt)

    def logout(self):
        if messagebox.askyesno("Logout", "Return to login screen?"):
            self.root.destroy()
            import main_app
            main_app.launch()


def launch():
    root = tk.Tk()
    AdminPanel(root)
    root.mainloop()


if __name__ == "__main__":
    launch()