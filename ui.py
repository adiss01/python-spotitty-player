import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import threading
from io import BytesIO
from storage import add_favorite, remove_favorite, get_favorites, is_favorite
from assets.styles import hover
from PIL import Image, ImageTk, ImageDraw
import json
import shutil
import time
import os
import random

#theme
BG = "#000000"
CARD = "#121212"
FG = "#ffffff"
ACCENT = "#1db954"
TROUGH = "#2b2b2b"
BTN_HOVER = "#2a2a2a"
SUB = "#b3b3b3"
CLOSE_HOVER = "#e81123"
SESSION_FILE = "data/session.json"
USERS_FILE = "data/users.json"

# ---------------- MAIN UI ----------------

class UI:
    def __init__(self, root, player, client_id, data):
        self.root = root
        self.player = player
        self.client_id = client_id
        self.username = data["username"]
        self.tracks = []
        self.images = []
        self.cards = []
        self.active_bars = []
        self.current_index = -1
        self.dragging = False
        self.user = {
            "name": data["name"],
            "email": self.username+"@spotitty.app",
            "avatar": data["avatar"]
        }
        # --- PLAYER MODES ---
        self.shuffle_enabled = False
        self.repeat_mode = "off"  # off | all | one

        self.build_ui()
        self.bottom_bar = BottomPlayerBar(
            self.root,
            self.player,
            on_prev=self.prev,
            on_next=self.play_next,
            sf = self.toggle_shuffle,
            rpt = self.toggle_repeat,
            sfe = self.shuffle_enabled,
            rpte = self.repeat_mode,
            add_fav = self.add_fav,
        )

        self.bottom_bar.pack(side="bottom", fill="x")
        self.update_progress()

    def load_icon(self, path, size=(24, 24)):
        img = Image.open(path).resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    def build_ui(self):
        self.root.configure(bg=BG)
        self.profile_page = tk.Frame(self.root, bg=PLAYER_BG)

        # ==============================
        # SPOTİTTY HEADER (TITLE + SEARCH)
        # ==============================

        HEADER_BG = "#121212"
        SEARCH_BG = "#242424"
        SEARCH_FG = "#b3b3b3"
        SEARCH_ACTIVE = "#ffffff"
        SPOTIFY_GREEN = "#1db954"
        SEARCH_BORDER = "#333333"

        header = tk.Frame(self.root, bg=HEADER_BG, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        # ---------- WINDOW DRAG ----------
        def start_move(e):
            self._x = e.x
            self._y = e.y

        def on_move(e):
            x = self.root.winfo_x() + (e.x - self._x)
            y = self.root.winfo_y() + (e.y - self._y)
            self.root.geometry(f"+{x}+{y}")

        header.bind("<ButtonPress-1>", start_move)
        header.bind("<B1-Motion>", on_move)

        # ---------- LEFT : MACOS CONTROLS ----------
        left = tk.Frame(header, bg=HEADER_BG)
        left.pack(side="left", padx=12)

        def mac_btn(color, icon, command):
            c = tk.Canvas(left, width=12, height=12, bg=HEADER_BG, highlightthickness=0)
            c.create_oval(1, 1, 11, 11, fill=color, outline=color)
            t = c.create_text(6, 6, text=icon, fill="#2a2a2a",
                              font=("Segoe UI", 8, "bold"), state="hidden")

            c.bind("<Enter>", lambda e: c.itemconfigure(t, state="normal"))
            c.bind("<Leave>", lambda e: c.itemconfigure(t, state="hidden"))
            c.bind("<Button-1>", lambda e: command())
            c.pack(side="left", padx=4)

        mac_btn("#ff5f57", "✕", self.root.destroy)
        mac_btn("#ffbd2e", "—", self.root.iconify)

        def toggle_max():
            self.root.state("normal" if self.root.state() == "zoomed" else "zoomed")

        mac_btn("#28c840", "▢", toggle_max)

        # ---------- CENTER : SEARCH ----------
        center = tk.Frame(header, bg=HEADER_BG)
        center.pack(side="left", expand=True)

        search_box = tk.Frame(
            center,
            bg=SEARCH_BG,
            height=34,
            width=360,
            highlightthickness=1,
            highlightbackground=SEARCH_BORDER,
            highlightcolor=SPOTIFY_GREEN
        )
        search_box.pack(pady=10)
        search_box.pack_propagate(False)

        # 🔍 ICON
        tk.Label(
            search_box,
            text="🔍",
            bg=SEARCH_BG,
            fg=SEARCH_FG,
            font=("Segoe UI", 11)
        ).pack(side="left")

        history_frame = tk.Frame(
            center,
            bg="#181818",
            highlightthickness=1,
            highlightbackground="#2a2a2a"
        )
        history_frame.pack_forget()

        # -----------------------
        # ENTRY
        # -----------------------
        PLACEHOLDER = "Ne dinlemek istiyorsun?"

        self.search_var = tk.StringVar()

        search_entry = tk.Entry(
            search_box,
            textvariable=self.search_var,
            bd=0,
            bg=SEARCH_BG,
            fg=SEARCH_FG,
            insertbackground=SEARCH_ACTIVE,
            font=("Segoe UI", 11)
        )
        search_entry.pack(side="left", fill="both", expand=True)

        search_entry.insert(0, PLACEHOLDER)

        # -----------------------
        # CLEAR BUTTON (✕)
        # -----------------------
        clear_btn = tk.Label(
            search_box,
            text="✕",
            bg=SEARCH_BG,
            fg="#b3b3b3",
            font=("Segoe UI", 10),
            cursor="hand2"
        )
        clear_btn.pack(side="right", padx=(6, 10))
        clear_btn.pack_forget()  # başlangıçta gizli

        def clear_search(_=None):
            self.search_var.set("")
            clear_btn.pack_forget()
            search_entry.focus_set()
        clear_btn.bind("<Button-1>", clear_search)

        # -----------------------
        # PLACEHOLDER + GLOW
        # -----------------------
        def on_focus_in(e):
            search_box.config(highlightthickness=2)
            if search_entry.get() == PLACEHOLDER:
                search_entry.delete(0, "end")
                search_entry.config(fg=SEARCH_ACTIVE)

        def on_focus_out(e):
            search_box.config(highlightthickness=1)
            if not search_entry.get():
                search_entry.insert(0, PLACEHOLDER)
                search_entry.config(fg=SEARCH_FG)
                clear_btn.pack_forget()

        def on_text_change(*_):
            text = self.search_var.get()
            if text and text != PLACEHOLDER:
                if not clear_btn.winfo_ismapped():
                    clear_btn.pack(side="right", padx=(6, 10))
            else:
                clear_btn.pack_forget()

        self.search_var.trace_add("write", on_text_change)

        search_entry.bind("<FocusIn>", on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)

        # -----------------------
        # BOŞ ARAMA KİLİT
        # -----------------------
        def submit_search(_=None):
            q = self.search_var.get().strip()
            if not q or q == PLACEHOLDER:
                return
            self.search()

        search_entry.bind("<Return>", submit_search)


        # ======================================================
        # ---------- SAĞ TARAF : AVATAR + NAME ----------
        # ======================================================
        right = tk.Frame(header, bg=HEADER_BG)
        right.pack(side="right", padx=26)
        size = 50

        img = Image.open(self.user["avatar"]).resize((size, size), Image.LANCZOS).convert("RGBA")
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        self.avatar_img = ImageTk.PhotoImage(img)

        # LABEL
        self.avatar = tk.Label(
            right,
            image=self.avatar_img,
            bg=HEADER_BG,
            cursor="hand2"
        )
        self.avatar.pack(side="left")
        self.avatar.pack(side="left")

        self.name_lbl = tk.Label(
            right,
            text=self.user["name"].upper(),
            bg=HEADER_BG,
            fg="white",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2"
        )
        self.name_lbl.pack(side="left", padx=(8, 0))


        # ======================================================
        # AVATAR TOOLTIP
        # ======================================================
        avatar_tooltip = tk.Label(
            self.root,
            text="Ayarlar Menüsü",
            bg="#282828",
            fg="white",
            font=("Segoe UI", 9),
            padx=8,
            pady=4
        )

        def show_avatar_tip(e):
            x = self.avatar.winfo_rootx() - self.root.winfo_rootx()
            y = self.avatar.winfo_rooty() - self.root.winfo_rooty() + 44
            avatar_tooltip.place(x=x, y=y)
            avatar_tooltip.lift()

        def hide_avatar_tip(e):
            avatar_tooltip.place_forget()

        self.avatar.bind("<Enter>", show_avatar_tip)
        self.avatar.bind("<Leave>", hide_avatar_tip)


        # ======================================================
        # DROPDOWN MENU
        # ======================================================
        menu = tk.Frame(
            self.root,
            bg="#181818",
            highlightthickness=1,
            highlightbackground="#2a2a2a"
        )

        def open_menu():
            # Menü açıksa kapat (toggle)
            if menu.winfo_ismapped():
                menu.place_forget()
                return
        
            self.root.update_idletasks()
        
            # Avatar'ın ROOT'a göre pozisyonu
            x = self.avatar.winfo_rootx() - self.root.winfo_rootx()
            y = self.avatar.winfo_rooty() - self.root.winfo_rooty() + self.avatar.winfo_height()
        
            menu.place(x=x, y=y, width=200)
            menu.lift()


        def close_menu():
            menu.place_forget()

        def menu_item(text, cmd):
            b = tk.Label(
                menu,
                text=text,
                bg="#181818",
                fg="white",
                anchor="w",
                padx=14,
                pady=10,
                cursor="hand2"
            )
            b.pack(fill="x")
            b.bind("<Enter>", lambda e: b.config(bg="#282828"))
            b.bind("<Leave>", lambda e: b.config(bg="#181818"))
            b.bind("<Button-1>", lambda e: (close_menu(), cmd()))

        menu_item("👤 Profil", lambda: open_profile())
        menu_item("❤️ Favoriler", lambda: FavoritesWindow(self.root, self, self.username))
        menu_item("⏻ Çıkış Yap", self.logout)

        self.avatar.bind("<Button-1>", lambda e: open_menu())
        self.name_lbl.bind("<Button-1>", lambda e: open_menu())


        # ROOT CLICK -> MENU KAPAT (SAFE)
        def root_click(e):
            if not menu.winfo_ismapped():
                return
            if e.widget in (menu, self.avatar, self.name_lbl):
                return
            close_menu()

        self.root.bind("<Button-1>", root_click, add="+")
        def open_profile():
            win = tk.Toplevel(self.root)
            win.title("Profil Düzenle")
            win.geometry("460x560")
            win.configure(bg="#121212")
            win.resizable(False, False)
            win.transient(self.root)
            win.grab_set()

            # =========================
            # LOAD DATA
            # =========================
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                session = json.load(f)
            with open("data/users.json", "r", encoding="utf-8") as f:
                users = json.load(f)

            user = users[self.username]
            username = self.username
            original_name = user["name"]
            original_avatar = user["avatar"]

            temp_avatar_path = original_avatar

            # =========================
            # HELPERS
            # =========================
            def round_image(path, size):
                img = Image.open(path).resize((size, size)).convert("RGBA")
                mask = Image.new("L", (size, size), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, size, size), fill=255)
                img.putalpha(mask)
                return img

            # =========================
            # AVATAR PREVIEW
            # =========================
            avatar_img = round_image(temp_avatar_path, 120)
            avatar_photo = ImageTk.PhotoImage(avatar_img)

            self.avatar_lbl = tk.Label(
                win,
                image=avatar_photo,
                bg="#121212",
                cursor="hand2"
            )
            self.avatar_lbl.image = avatar_photo
            self.avatar_lbl.pack(pady=(30, 8))

            tk.Label(
                win,
                text="Avatarı değiştirmek için tıkla",
                bg="#121212",
                fg="#b3b3b3",
                font=("Segoe UI", 9)
            ).pack()

            # =========================
            # AVATAR HOVER PREVIEW
            # =========================
            preview = tk.Toplevel(win)
            preview.withdraw()
            preview.overrideredirect(True)

            def show_preview(e):
                img = round_image(temp_avatar_path, 200)
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(preview, image=photo, bg="#000000")
                lbl.image = photo
                lbl.pack()
                x = win.winfo_rootx() + 350
                y = win.winfo_rooty() + 80
                preview.geometry(f"+{x}+{y}")
                preview.deiconify()

            def hide_preview(e):
                preview.withdraw()
                for w in preview.winfo_children():
                    w.destroy()

            self.avatar_lbl.bind("<Enter>", show_preview)
            self.avatar_lbl.bind("<Leave>", hide_preview)

            # =========================
            # NAME ENTRY
            # =========================
            tk.Label(
                win,
                text="İSİM",
                bg="#121212",
                fg="#b3b3b3",
                font=("Segoe UI", 10)
            ).pack(pady=(30, 6))

            name_var = tk.StringVar(value=original_name)

            name_entry = tk.Entry(
                win,
                textvariable=name_var,
                bg="#282828",
                fg="white",
                insertbackground="white",
                relief="flat",
                font=("Segoe UI", 11),
                justify="center"
            )
            name_entry.pack(ipadx=90, ipady=6)

            # =========================
            # AVATAR CHANGE
            # =========================
            def change_avatar():
                nonlocal temp_avatar_path

                file = filedialog.askopenfilename(
                    title="Avatar Seç",
                    filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
                )
                if not file:
                    return

                ext = os.path.splitext(file)[1]
                dest = f"assets/images/avatar_{username}{ext}"
                shutil.copy(file, dest)

                temp_avatar_path = dest

                img = round_image(dest, 120)
                photo = ImageTk.PhotoImage(img)
                self.avatar_lbl.config(image=photo)
                self.avatar_lbl.image = photo

            self.avatar_lbl.bind("<Button-1>", lambda e: change_avatar())

            # =========================
            # SAVE
            # =========================
            def save_profile():
                new_name = name_var.get().strip()

                if not new_name:
                    messagebox.showerror("Hata", "İsim boş olamaz")
                    return

                # update user
                user["name"] = new_name
                user["avatar"] = temp_avatar_path

                users[username] = user

                # update session
                session["name"] = new_name
                session["avatar"] = temp_avatar_path

                with open(USERS_FILE, "w", encoding="utf-8") as f:
                    json.dump(users, f, indent=4, ensure_ascii=False)

                with open(SESSION_FILE, "w", encoding="utf-8") as f:
                    json.dump(session, f, indent=4, ensure_ascii=False)

                # =========================
                # LIVE HEADER UPDATE
                # =========================
                self.name_lbl.config(text=new_name.upper())

                header_img = round_image(temp_avatar_path, 40)
                header_photo = ImageTk.PhotoImage(header_img)
                self.avatar.config(image=header_photo)
                self.avatar.image = header_photo

                messagebox.showinfo("Başarılı", "Profil güncellendi")
                win.destroy()

            # =========================
            # UNDO / CANCEL
            # =========================
            def cancel_profile():
                self.name_lbl.config(text=original_name.upper())

                img = round_image(original_avatar, 40)
                photo = ImageTk.PhotoImage(img)
                self.avatar.config(image=photo)
                self.avatar.image = photo

                win.destroy()

            # =========================
            # BUTTONS
            # =========================
            tk.Button(
                win,
                text="KAYDET",
                bg="#1db954",
                fg="black",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                padx=50,
                pady=8,
                cursor="hand2",
                command=save_profile
            ).pack(pady=(40, 10))

            tk.Button(
                win,
                text="İPTAL",
                bg="#282828",
                font=("Segoe UI", 10, "bold"),
                fg="white",
                relief="flat",
                padx=58,
                pady=9,
                cursor="hand2",
                command=cancel_profile
            ).pack()

        # ---------- RESULTS PANEL ----------
        results_frame = tk.Frame(self.root, bg=BG)
        results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        canvas = tk.Canvas(results_frame, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)

        self.results_container = tk.Frame(canvas, bg=BG)

        self.results_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.results_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
        
    def add_fav(self):
        if not hasattr(self, "current_track") or not self.current_track:
            return

        track = self.current_track

        if is_favorite(self.username, track):
            remove_favorite(self.username, track["id"])
            self.bottom_bar.set_favorite_state(False)
        else:
            add_favorite(self.username, track)
            self.bottom_bar.set_favorite_state(True)




    def search(self):
        q = self.search_var.get().strip()
        if not q:
            return

        r = requests.get(
            "https://api.jamendo.com/v3.0/tracks",
            params={"client_id": self.client_id, "search": q, "limit": 20},
            timeout=10
        ).json()

        self.tracks = r.get("results", [])

        self.active_bars.clear()
        self.cards.clear()

        for widget in self.results_container.winfo_children():
            widget.destroy()

        for i, track in enumerate(self.tracks):
            self.create_track_card(track, i)
        
        self.root.after(500)


    def play_selected(self, _):
        if not self.listbox.curselection():
            return

        track = self.favorites[self.listbox.curselection()[0]]
        self.ui.play_external_track(track)


    def update_progress(self):
        if not self.dragging:
            try:
                pos = self.player.get_position()
                if pos >= 0:
                    self.progress.set(pos * 100)
            except:
                pass
        self.root.after(500, self.update_progress)

    def seek(self, val):
        if self.dragging:
            try:
                self.player.set_position(float(val) / 100)
            except:
                pass

    def create_track_card(self, track, index):
        COLS = 4

        row = index // COLS
        col = index % COLS

        card = tk.Frame(
            self.results_container,
            bg=CARD,
            height=82
        )
        card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
        card.grid_propagate(False)

        self.results_container.grid_columnconfigure(col, weight=1)
        self.results_container.bind("<Configure>", lambda e: self.current_index)
        # -------- ACTIVE BAR --------
        active_bar = tk.Frame(card, bg=CARD, width=4)
        active_bar.pack(side="left", fill="y")
        self.active_bars.append(active_bar)

        # -------- CONTENT --------
        content = tk.Frame(card, bg=CARD)
        content.pack(expand=True, fill="both", padx=10)

        # -------- IMAGE --------
        default_img = Image.open("assets/images/spotitty.png").resize((48, 48))
        photo = ImageTk.PhotoImage(default_img)
        card.cover_image = photo
        self.images.append(photo)

        img_label = tk.Label(content, image=photo, bg=CARD)
        img_label.pack(side="left", pady=12)

        # -------- TEXT --------
        text = tk.Frame(content, bg=CARD)
        text.pack(side="left", expand=True, fill="both", padx=12, pady=10)

        tk.Label(
            text,
            text=track["name"][:14] + "…" if len(track["name"]) > 14 else track["name"],
            bg=CARD,
            fg=FG,
            font=("Segoe UI Semibold", 10),
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            text,
            text=track["artist_name"],
            bg=CARD,
            fg="#b3b3b3",
            font=("Segoe UI", 9),
            anchor="w"
        ).pack(fill="x", pady=(2, 0))

        duration = int(track["duration"])
        minutes = duration // 60
        seconds = duration % 60
        formatted_duration = f"{minutes}:{seconds:02d}"

        tk.Label(
            content,
            text=formatted_duration,
            bg=CARD,
            fg="#9a9a9a",
            font=("Segoe UI", 9),
            anchor="e"
        ).pack(side="right", padx=8)

        # -------- CLICK --------
        def play(_):
            current_index = self.cards.index(card)
            track = self.tracks[current_index]

            self.current_index = current_index
            self.current_track = track   # 🔥

            self.bottom_bar.set_track_info(
                track["name"],
                track["artist_name"],
                card.cover_image
            )

            self.bottom_bar.set_favorite_state(
                is_favorite(self.username, track)
            )

            self.set_active_card(current_index)
            self.play_track(current_index)





        for w in (card, content, img_label, text):
            w.bind("<Button-1>", play)

        self.cards.append(card)

        # -------- IMAGE ASYNC --------
        if track.get("image"):
            import threading
            threading.Thread(
                target=self.load_image_async,
                args=(track["image"], img_label, card, track, index),
                daemon=True
            ).start()


    # def pin_active_card_to_top(self, active_index):
    #     # Kart + active bar senkron şekilde taşınır
    #     card = self.cards.pop(active_index)
    #     bar = self.active_bars.pop(active_index)

    #     self.cards.insert(0, card)
    #     self.active_bars.insert(0, bar)

    #     self.relayout_cards()

    # def relayout_cards(self):
    #     COLS = 4
    #     for i, card in enumerate(self.cards):
    #         row = i // COLS
    #         col = i % COLS
    #         card.grid_configure(row=row, column=col)

    def load_image_async(self, url, label, card, track, index):
        try:
            r = requests.get(url, timeout=3)
            img = Image.open(BytesIO(r.content)).resize((50, 50))
            photo = ImageTk.PhotoImage(img)
            self.images.append(photo)

            def apply():
                label.config(image=photo)
                card.cover_image = photo
                track["_image"] = photo   # TRACK STATE GÜNCEL

                # Eğer bu şarkı şu an çalıyorsa alt barı da güncelle
                if index == self.current_index:
                    self.bottom_bar.set_track_info(
                        track["name"],
                        track["artist_name"],
                        track["_image"]
                    )

            label.after(0, apply)
        except:
            pass

    def _play_by_index(self, index):
        self.current_index = index
        track = self.tracks[index]

        self.player.play(track)
        self.set_active_card(index)
        self.bottom_bar.set_playing(True)

        self.bottom_bar.set_track_info(
            track["name"],
            track["artist_name"],
            track["_image"]
        )
         
        
    def play_track(self, index):
        self._play_by_index(index)




    def set_active_card(self, index):
        self.current_index = index
    
        for i, bar in enumerate(self.active_bars):
            if not bar.winfo_exists():
                continue
            bar.config(bg=ACCENT if i == index else CARD)

    def logout(self):
        try:
            self.player.stop()
        except:
            pass

        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

        self.root.destroy()

        from login import LoginApp
        root = tk.Tk()
        LoginApp(root)
        root.mainloop()

    def on_play(self):
        self.bottom_bar.set_playing(True)

    def on_pause(self):
        self.bottom_bar.set_playing(False)

    def toggle_shuffle(self):
        self.shuffle_enabled = not self.shuffle_enabled


    def toggle_repeat(self):
        if self.repeat_mode == "off":
            self.repeat_mode = "all"
    
        elif self.repeat_mode == "all":
            self.repeat_mode = "one"
    
        else:
            self.repeat_mode = "off"
    


    def play_next(self):
        if not self.tracks:
            return

        # 🔁 REPEAT ONE
        if self.repeat_mode == "one":
            self._play_by_index(self.current_index)
            return

        # 🔀 SHUFFLE
        if self.shuffle_enabled:
            next_index = random.randint(0, len(self.tracks) - 1)

            while next_index == self.current_index and len(self.tracks) > 1:
                next_index = random.randint(0, len(self.tracks) - 1)

        # ▶️ NORMAL
        else:
            next_index = self.current_index + 1

            if next_index >= len(self.tracks):
                if self.repeat_mode == "off":
                    return
                next_index = 0  # repeat all

        self._play_by_index(next_index)


    def prev(self):
        if not self.tracks:
            return
        self._play_by_index((self.current_index - 1) % len(self.tracks))

    def play_external_track(self, track: dict):

        self.current_index = -1          # search listesinde yok
        self.current_track = track       # 🔥 TEK GERÇEK KAYNAK

        self.player.play(track)

        self.bottom_bar.set_track_info(
            track["name"],
            track["artist_name"],
            None
        )
        self.bottom_bar.set_playing(True)

        # ✅ FAVORİ KONTROLÜ TRACK ÜZERİNDEN
        self.bottom_bar.set_favorite_state(
            is_favorite(self.username, track)
        )

        if track.get("image"):
            threading.Thread(
                target=self._load_fav_image_async,
                args=(track,),
                daemon=True
            ).start()

    def _load_fav_image_async(self, track):
        try:
            r = requests.get(track["image"], timeout=5)
            img = Image.open(BytesIO(r.content)).resize((56, 56))
            photo = ImageTk.PhotoImage(img)

            def apply():
                self.bottom_bar.set_track_info(
                    track["name"],
                    track["artist_name"],
                    photo
                )

            self.root.after(0, apply)
        except:
            pass

    
# ================= ALTTAKİ PLAYER BAR =================

PLAYER_BG = "#181818"
ACCENT = "#1DB954"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#b3b3b3"
PROGRESS_BG = "#404040"
PLAYER_BAR_HEIGHT = 72

class BottomPlayerBar(tk.Frame):
    def __init__(self, root, player, on_prev, on_next, sf, rpt, sfe, rpte, add_fav):
        super().__init__(root, bg=PLAYER_BG, height=PLAYER_BAR_HEIGHT)
        self.pack_propagate(False)

        self.player = player
        self.is_playing = False

        self.left = tk.Frame(self, bg=PLAYER_BG, width=260)
        self.center = tk.Frame(self, bg=PLAYER_BG)
        self.right = tk.Frame(self, bg=PLAYER_BG, width=200)
        self.player = player
        
        self.on_prev = on_prev
        self.on_next = on_next
        self.sf = sf
        self.rpt = rpt
        self.sfe = sfe
        self.rpte = rpte
        self.add_fav = add_fav
        self.is_favorite = False
        self.icon = False
        self.left.pack(side="left", fill="y")
        self.center.pack(side="left", expand=True, fill="both")
        self.right.pack(side="right", fill="y")

        self.left.pack_propagate(False)
        self.right.pack_propagate(False)

        self._build_left()
        self._build_center()
        self._build_right()

        self.after(500, self.update_progress)

    # ---------- LEFT ----------
    def _build_left(self):
        self.cover = tk.Label(self.left, bg=PLAYER_BG, width=56, height=56)
        self.cover.pack(side="left", padx=10)

        info = tk.Frame(self.left, bg=PLAYER_BG)
        info.pack(side="left")

        self.title = tk.Label(
            info, text="Şarkı Adı",
            fg=TEXT_PRIMARY, bg=PLAYER_BG,
            font=("Segoe UI", 10, "bold")
        )
        self.title.pack(anchor="w")

        self.artist = tk.Label(
            info, text="Sanatçı",
            fg=TEXT_SECONDARY, bg=PLAYER_BG,
            font=("Segoe UI", 9)
        )
        self.artist.pack(anchor="w")

    # ---------- CENTER ----------
    def load_icon(self, path, size=(24, 24)):
        img = Image.open(path).resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def _build_center(self):
        controls = tk.Frame(self.center, bg=PLAYER_BG)
        controls.pack(pady=(4, 0))

        # --- ICONS ---
        self.prev_icon  = self.load_icon("assets/icons/previous.png")
        self.play_icon  = self.load_icon("assets/icons/play.png")
        self.pause_icon = self.load_icon("assets/icons/pause.png")
        self.next_icon  = self.load_icon("assets/icons/next.png")
        self.fav_icon = self.load_icon("assets/icons/add_fav.png")
        self.fav_active_icon = self.load_icon("assets/icons/faved.png")
        # --- SHUFFLE ICONS ---
        self.shuffle_icon = self.load_icon("assets/icons/shuffle.png")
        self.shuffle_active_icon = self.load_icon("assets/icons/shuffle_active.png")

        # --- REPEAT ICONS ---
        self.repeat_icon = self.load_icon("assets/icons/repeat_icon.png")
        self.repeat_all_icon = self.load_icon("assets/icons/repeat_all.png")
        self.repeat_one_icon = self.load_icon("assets/icons/repeat_active.png")

        # --- SHUFFLE BUTTON ---
        self.shuffle_btn = tk.Button(
            controls,
            image=self.shuffle_icon,
            bg=PLAYER_BG,
            bd=0,
            command=self._sf_clicked,
            activebackground=PLAYER_BG,
        )
        self.shuffle_btn.pack(side="left", padx=6)

        # --- PREV ---
        tk.Button(
            controls,
            image=self.prev_icon,
            bg=PLAYER_BG,
            bd=0,
            activebackground=PLAYER_BG,
            command=self._prev_clicked
        ).pack(side="left", padx=10)
        
        # --- PLAY / PAUSE ---
        self.play_btn = tk.Button(
            controls,
            image=self.play_icon,
            bg=PLAYER_BG,
            bd=0,
            width=30,
            height=30,
            command=self.toggle_play,
            activebackground=PLAYER_BG
        )
        self.play_btn.pack(side="left")
        
        # --- NEXT ---
        tk.Button(
            controls,
            image=self.next_icon,
            bg=PLAYER_BG,
            bd=0,
            activebackground=PLAYER_BG,
            command=self._next_clicked
        ).pack(side="left", padx=10)

        # --- REPEAT BUTTON ---
        self.repeat_btn = tk.Button(
            controls,
            image=self.repeat_icon,
            bg=PLAYER_BG,
            bd=0,
            activebackground=PLAYER_BG,
            command=self._rpt_clicked
        )
        self.repeat_btn.pack(side="left", padx=6)
        # --- NEXT ---
        self.fav_btn = tk.Button(
            controls,
            image=self.fav_icon,
            bg=PLAYER_BG,
            bd=0,
            activebackground=PLAYER_BG,
            command=self._fav_clicked
        )
        self.fav_btn.pack(side="left", padx=10)


        # ---- PROGRESS BAR ----
        progress_frame = tk.Frame(self.center, bg=PLAYER_BG)
        progress_frame.pack(fill="x", padx=40, pady=(6, 0))

        self.current_time = tk.Label(
            progress_frame, text="0:00",
            fg=TEXT_SECONDARY, bg=PLAYER_BG,
            font=("Segoe UI", 9)
        )
        self.current_time.pack(side="left")

        self.progress = tk.Canvas(
            progress_frame,
            height=4,
            bg=PROGRESS_BG,
            highlightthickness=0,
            cursor="hand2"
        )
        self.progress.pack(side="left", fill="x", expand=True, padx=10)

        self.progress_fill = self.progress.create_rectangle(
            0, 0, 0, 4, fill=ACCENT, outline=""
        )

        self.total_time = tk.Label(
            progress_frame, text="0:00",
            fg=TEXT_SECONDARY, bg=PLAYER_BG,
            font=("Segoe UI", 9)
        )
        self.total_time.pack(side="right")

        self.progress.bind("<Button-1>", self.seek)
        self.progress.bind("<B1-Motion>", self.seek)

    # ---------- RIGHT ----------
    def set_favorite_state(self, state: bool):
        self.is_favorite = state
        self.fav_btn.config(
            image=self.fav_active_icon if state else self.fav_icon
        )
    def _fav_clicked(self):
        if callable(self.add_fav):
            self.add_fav()
    
    def _prev_clicked(self):
        if callable(self.on_prev):
            self.on_prev()

    def _next_clicked(self):
        if callable(self.on_next):
            self.on_next()
    def _sf_clicked(self):
        self.sfe = not self.sfe

        if self.sfe:
            self.shuffle_btn.config(image=self.shuffle_active_icon)
        elif not self.sfe:
            self.shuffle_btn.config(image=self.shuffle_icon)

        if callable(self.sf):
            self.sf()

    def _rpt_clicked(self):
        if self.rpte == "off":
            self.rpte = "all"
            self.repeat_btn.config(image=self.repeat_all_icon)
    
        elif self.rpte == "all":
            self.rpte = "one"
            self.repeat_btn.config(image=self.repeat_one_icon)
    
        else:
            self.rpte = "off"
            self.repeat_btn.config(image=self.repeat_icon)

        if callable(self.rpt):
            self.rpt()



    

    def _build_right(self):
        VolumeBar(self.right, self.player).pack(side="bottom", padx=12, pady=9.2)



        
    # ---------- LOGIC ----------
    def toggle_play(self):
        action = self.player.pause if self.is_playing else self.player.play
        self.icon = not self.icon
        action()
        if self.icon:
            self.play_btn.config(image=self.play_icon)
        else:
            self.play_btn.config(image=self.pause_icon)

        if self.is_playing:
            self.is_playing = True
        else:
            self.is_playing = False


    def set_volume(self, value):
        self.player.set_volume(int(value))

    def seek(self, event):
        width = self.progress.winfo_width()
        if width <= 0:
            return
        ratio = event.x / width
        ratio = max(0.0, min(1.0, ratio))
        self.player.seek(ratio)

    def update_progress(self):
        try:
            current, total = self.player.get_progress()
            if total > 0:
                width = self.progress.winfo_width()
                fill = int((current / total) * width)
                self.progress.coords(self.progress_fill, 0, 0, fill, 4)

                self.current_time.config(text=self._fmt(current))
                self.total_time.config(text=self._fmt(total))
        except:
            pass

        self.after(500, self.update_progress)

    def _fmt(self, sec):
        m = int(sec // 60)
        s = int(sec % 60)
        return f"{m}:{s:02d}"
    def set_track_info(self, title, artist, image=None):
        self.title.config(text=title[:30])
        self.artist.config(text=artist[:30])
        if image:
            self.cover_img = image
            self.cover.config(image=self.cover_img)
    def set_playing(self, playing: bool):
        self.is_playing = playing
        self.play_btn.config(image=self.pause_icon if playing else self.play_icon)

# ---------------- TOOLTIP ----------------

class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip = None

    def show(self, text):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() - 30
        self.tip = tk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.configure(bg="#111")
        tk.Label(
            self.tip, text=text,
            bg="#111", fg="white",
            font=("Segoe UI", 9),
            padx=6, pady=2
        ).pack()
        self.tip.geometry(f"+{x}+{y}")

    def hide(self):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class VolumeBar(tk.Frame):
    def __init__(self, root, player):
        super().__init__(root, bg=PLAYER_BG)

        self.player = player
        self.value = 50
        self.last_value = 50
        self.dragging = False

        # --- ICON ---
        self.icon = tk.Label(
            self,
            text="🔊",
            bg=PLAYER_BG,
            fg=TEXT_PRIMARY,
            font=("Segoe UI", 11),
            cursor="hand2"
        )
        self.icon.pack(side="left", padx=(0, 8))
        self.icon.bind("<Button-1>", self.toggle_mute)

        # --- CANVAS SLIDER ---
        self.canvas = tk.Canvas(
            self,
            width=120,
            height=12,
            bg=PLAYER_BG,
            highlightthickness=0,
            cursor="hand2"
        )
        self.canvas.pack(side="left")

        self.track_bg = self.canvas.create_rectangle(
            0, 5, 120, 7, fill="#404040", outline=""
        )

        self.track_fill = self.canvas.create_rectangle(
            0, 5, 60, 7, fill=ACCENT, outline=""
        )

        self.knob = self.canvas.create_oval(
            56, 1, 64, 9, fill="white", outline=""
        )
        self.canvas.itemconfigure(self.knob, state="hidden")

        # --- EVENTS ---
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<Enter>", self.show_knob)
        self.canvas.bind("<Leave>", self.hide_knob)

        self.update_ui()
        self.player.set_volume(self.value)

    # -------------------------
    # EVENTS
    # -------------------------

    def click(self, event):
        self.set_from_x(event.x)

    def drag(self, event):
        self.set_from_x(event.x)

    def set_from_x(self, x):
        x = max(0, min(120, x))
        self.value = int((x / 120) * 100)
        self.player.set_volume(self.value)
        self.update_ui()

    # -------------------------
    # ICON LOGIC
    # -------------------------

    def toggle_mute(self, _=None):
        if self.value > 0:
            self.last_value = self.value
            self.value = 0
        else:
            self.value = self.last_value

        self.player.set_volume(self.value)
        self.update_ui()

    def update_icon(self):
        if self.value == 0:
            self.icon.config(text="🔇")
        elif self.value < 40:
            self.icon.config(text="🔈")
        else:
            self.icon.config(text="🔊")

    # -------------------------
    # UI UPDATE
    # -------------------------

    def update_ui(self):
        fill_x = int((self.value / 100) * 120)
        self.canvas.coords(self.track_fill, 0, 5, fill_x, 7)
        self.canvas.coords(self.knob, fill_x - 4, 1, fill_x + 4, 9)
        self.update_icon()

    def show_knob(self, _):
        self.canvas.itemconfigure(self.knob, state="normal")

    def hide_knob(self, _):
        self.canvas.itemconfigure(self.knob, state="hidden")




# ---------------- FAVORITES WINDOW ----------------
class FavoritesWindow:
    def __init__(self, root, ui, user_id):
        self.ui = ui
        self.user_id = user_id

        self.win = tk.Toplevel(root)
        self.win.title("Favoriler")
        self.win.configure(bg=BG)
        self.win.geometry("400x300")

        tk.Label(
            self.win,
            text="❤︎ Favoriler",
            bg=BG,
            fg=FG,
            font=("Segoe UI", 11, "bold")
        ).pack(pady=6)

        self.listbox = tk.Listbox(
            self.win,
            bg=CARD,
            fg=FG,
            selectbackground=ACCENT,
            activestyle="none"
        )
        self.listbox.pack(fill="both", expand=True, padx=10, pady=6)
        self.listbox.bind("<Double-Button-1>", self.play_selected)

        btns = tk.Frame(self.win, bg=BG)
        btns.pack(pady=6)

        del_btn = tk.Button(
            btns,
            text="🗑 Sil",
            bg=CARD,
            fg=FG,
            command=self.remove_selected
        )
        hover(del_btn, CARD, ACCENT)
        del_btn.pack()

        self.load()

    def load(self):
        self.favorites = get_favorites(self.user_id)
        self.listbox.delete(0, tk.END)

        for t in self.favorites:
            self.listbox.insert(
                tk.END,
                f'{t["artist_name"]} - {t["name"]}'
            )

    def play_selected(self, _):
        if not self.listbox.curselection():
            return

        track = self.favorites[self.listbox.curselection()[0]]

        # 🔥 ÖNEMLİ NOKTA
        self.ui.play_external_track(track)

    def remove_selected(self):
        if not self.listbox.curselection():
            return

        index = self.listbox.curselection()[0]
        track = self.favorites[index]

        if messagebox.askyesno("Favoriler", "Favorilerden silinsin mi?"):
            remove_favorite(self.user_id, track["id"])
            self.load()
