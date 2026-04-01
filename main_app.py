import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys

# ── Theme Colors ─────────────────────────────────────────────────────────────
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

ADMIN_PASSWORD = "admin123"  # Change this to your password


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Access System — Login")
        self.root.geometry("480x580")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DARK)
        self.center_window(480, 580)
        self.build_ui()

    def center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=BG_PANEL, height=160)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🔐", font=("Segoe UI", 40), bg=BG_PANEL,
                 fg=BLUE_LIGHT).pack(pady=(25, 5))
        tk.Label(header, text="FACE ACCESS SYSTEM",
                 font=("Segoe UI", 16, "bold"), bg=BG_PANEL,
                 fg=TEXT_WHITE).pack()
        tk.Label(header, text="Secure Identity Verification",
                 font=("Segoe UI", 9), bg=BG_PANEL,
                 fg=TEXT_GRAY).pack()

        # Divider
        tk.Frame(self.root, bg=BLUE_ACCENT, height=2).pack(fill="x")

        # Form
        form = tk.Frame(self.root, bg=BG_DARK, padx=50)
        form.pack(fill="both", expand=True, pady=30)

        tk.Label(form, text="SELECT LOGIN TYPE", font=("Segoe UI", 9, "bold"),
                 bg=BG_DARK, fg=TEXT_GRAY).pack(anchor="w", pady=(0, 15))

        # Role selection
        self.role_var = tk.StringVar(value="admin")

        for role, label, icon in [("admin", "Administrator", "⚙️"),
                                   ("terminal", "Access Terminal", "📷")]:
            rb_frame = tk.Frame(form, bg=BG_CARD, cursor="hand2")
            rb_frame.pack(fill="x", pady=4, ipady=10, ipadx=10)

            tk.Label(rb_frame, text=icon, font=("Segoe UI", 18),
                     bg=BG_CARD, fg=BLUE_LIGHT).pack(side="left", padx=(15, 10))
            tk.Label(rb_frame, text=label, font=("Segoe UI", 11, "bold"),
                     bg=BG_CARD, fg=TEXT_WHITE).pack(side="left")
            tk.Radiobutton(rb_frame, variable=self.role_var, value=role,
                           bg=BG_CARD, fg=BLUE_LIGHT, selectcolor=BG_DARK,
                           activebackground=BG_CARD, cursor="hand2").pack(side="right", padx=15)

        # Password field
        tk.Label(form, text="ADMIN PASSWORD", font=("Segoe UI", 9, "bold"),
                 bg=BG_DARK, fg=TEXT_GRAY).pack(anchor="w", pady=(20, 5))

        pw_frame = tk.Frame(form, bg=BG_CARD)
        pw_frame.pack(fill="x")
        tk.Label(pw_frame, text="🔒", bg=BG_CARD, fg=TEXT_GRAY,
                 font=("Segoe UI", 12)).pack(side="left", padx=10)
        self.pw_entry = tk.Entry(pw_frame, show="●", bg=BG_CARD, fg=TEXT_WHITE,
                                  insertbackground=TEXT_WHITE, relief="flat",
                                  font=("Segoe UI", 12), bd=0)
        self.pw_entry.pack(side="left", fill="x", expand=True, ipady=10)
        self.pw_entry.bind("<Return>", lambda e: self.login())

        # Login button
        self.login_btn = tk.Button(form, text="ENTER SYSTEM",
                                    font=("Segoe UI", 11, "bold"),
                                    bg=BLUE_ACCENT, fg=TEXT_WHITE,
                                    relief="flat", cursor="hand2",
                                    activebackground=BTN_HOVER,
                                    activeforeground=TEXT_WHITE,
                                    command=self.login)
        self.login_btn.pack(fill="x", pady=(20, 0), ipady=12)

        # Status
        self.status_label = tk.Label(form, text="", font=("Segoe UI", 9),
                                      bg=BG_DARK, fg=DANGER)
        self.status_label.pack(pady=5)

        # Footer
        tk.Label(self.root, text="© 2025 Face Access System  |  All Rights Reserved",
                 font=("Segoe UI", 8), bg=BG_DARK, fg=TEXT_GRAY).pack(pady=10)

    def login(self):
        role     = self.role_var.get()
        password = self.pw_entry.get()

        if role == "admin":
            if password != ADMIN_PASSWORD:
                self.status_label.config(text="❌ Incorrect password.")
                return
            self.root.destroy()
            import admin_panel
            admin_panel.launch()
        else:
            self.root.destroy()
            import access_terminal_gui
            access_terminal_gui.launch()


def launch():
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    launch()