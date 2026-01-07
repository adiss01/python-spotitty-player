import tkinter as tk
from tkinter import messagebox
import json
import os
import hashlib
import re

BG = "#121212"
FG = "#ffffff"
GREEN = "#1DB954"
GRAY = "#b3b3b3"
RED = "#ff4d4d"
YELLOW = "#f1c40f"

USERS_FILE = "data/users.json"
SESSION_FILE = "data/session.json"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def password_strength(password: str):
    score = 0
    if len(password) >= 6:
        score += 1
    if re.search(r"[A-Z]", password):
        score += 1
    if re.search(r"[0-9]", password):
        score += 1
    if re.search(r"[!@#$%^&*]", password):
        score += 1

    if score <= 1:
        return "Zayıf", RED
    elif score == 2 or score == 3:
        return "Orta", YELLOW
    else:
        return "Güçlü", GREEN


class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotitty Login")
        self.root.geometry("400x560")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # ---- EKRAN ORTALAMA ----
        self.root.update_idletasks()
        width = 400
        height = 560
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        # ------------------------

        self.ensure_data_files()
        self.load_users()

        if not self.auto_login():
            self.build_ui()

    # ---------------- FILE SYSTEM ---------------- #
    def ensure_data_files(self):
        os.makedirs("data", exist_ok=True)

        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)

    # ---------------- DATA ---------------- #
    def load_users(self):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                self.users_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.users_data = {}


    def save_users(self):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.users_data, f, indent=4, ensure_ascii=False)


    # ---------------- UI ---------------- #
    def build_ui(self):
        tk.Label(
            self.root, text="Spotitty",
            fg=FG, bg=BG,
            font=("Helvetica", 22, "bold")
        ).pack(pady=30)

        tk.Label(self.root, text="Kullanıcı Adı", fg=GRAY, bg=BG).pack(anchor="w", padx=50)
        self.username_entry = tk.Entry(self.root, font=("Helvetica", 12))
        self.username_entry.pack(fill="x", padx=50, pady=5)

        tk.Label(self.root, text="Şifre", fg=GRAY, bg=BG).pack(anchor="w", padx=50, pady=(15, 0))

        password_frame = tk.Frame(self.root, bg=BG)
        password_frame.pack(fill="x", padx=50, pady=5)

        self.password_entry = tk.Entry(password_frame, show="*", font=("Helvetica", 12))
        self.password_entry.pack(side="left", fill="x", expand=True)
        self.password_entry.bind("<KeyRelease>", self.on_password_change)
        self.password_entry.bind("<KeyPress>", self.check_caps_lock)

        self.show_password = False
        self.toggle_btn = tk.Button(
            password_frame,
            text="👁",
            bg=BG,
            fg=FG,
            relief="flat",
            command=self.toggle_password
        )
        self.toggle_btn.pack(side="right", padx=(5, 0))

        self.caps_label = tk.Label(
            self.root,
            text="Caps Lock Açık",
            fg=RED,
            bg=BG,
            font=("Helvetica", 9)
        )
        self.caps_label.pack(anchor="w", padx=50)
        self.caps_label.pack_forget()

        self.strength_label = tk.Label(
            self.root,
            text="",
            fg=GRAY,
            bg=BG,
            font=("Helvetica", 9)
        )
        self.strength_label.pack(anchor="w", padx=50, pady=(5, 0))

        self.remember_var = tk.BooleanVar()
        tk.Checkbutton(
            self.root,
            text="Beni Hatırla",
            variable=self.remember_var,
            fg=GRAY,
            bg=BG,
            selectcolor=BG,
            activebackground=BG
        ).pack(anchor="w", padx=50, pady=10)

        tk.Button(
            self.root,
            text="Giriş Yap",
            bg=GREEN,
            fg="black",
            font=("Helvetica", 11),
            relief="flat",
            command=self.login
        ).pack(fill="x", padx=50, pady=15)

        tk.Button(
            self.root,
            text="Kayıt Ol",
            bg="#2a2a2a",
            fg=FG,
            font=("Helvetica", 11),
            relief="flat",
            command=self.register
        ).pack(fill="x", padx=50)

    # ---------------- EXTRA FEATURES ---------------- #
    def toggle_password(self):
        self.show_password = not self.show_password
        self.password_entry.config(show="" if self.show_password else "*")

    def on_password_change(self, event=None):
        pwd = self.password_entry.get()
        if pwd:
            text, color = password_strength(pwd)
            self.strength_label.config(text=f"Şifre Gücü: {text}", fg=color)
        else:
            self.strength_label.config(text="")

    def check_caps_lock(self, event):
        if event.state & 0x2:
            self.caps_label.pack(anchor="w", padx=50)
        else:
            self.caps_label.pack_forget()

    # ---------------- AUTH ---------------- #
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        hashed = hash_password(password)
    
        user = self.users_data.get(username)
    
        if not user or user["password"] != hashed:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre yanlış")
            return
    
        if self.remember_var.get():
            self.save_session(username)
    
        self.open_main_app(user)


    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if len(username) < 3 or len(password) < 4:
            messagebox.showwarning("Uyarı", "Geçerli bir kullanıcı adı ve şifre gir")
            return

        if username in self.users_data:
            messagebox.showerror("Hata", "Bu kullanıcı adı zaten var")
            return

        self.users_data[username] = {
            "username": username,
            "password": hash_password(password),
            "name": username,
            "avatar": "assets/images/sp"
        }

        self.save_users()
        messagebox.showinfo("Başarılı", "Kayıt tamamlandı")


    # ---------------- SESSION ---------------- #
    def save_session(self, username):
        user = self.users_data.get(username)
        if not user:
            return
    
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(user, f, indent=4, ensure_ascii=False)


    def auto_login(self):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                user = json.load(f)

            if "username" in user:
                self.open_main_app(user)
                return True
        except Exception:
            pass

        return False


    # ---------------- MAIN ---------------- #
    def open_main_app(self, data):
        self.root.destroy()
        from main import MainApp
        root = tk.Tk()
        MainApp(root, data)
        root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    LoginApp(root)
    root.mainloop()



