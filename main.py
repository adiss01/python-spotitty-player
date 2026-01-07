import tkinter as tk
import ctypes
from player import Player
from ui import UI
from mica import apply_mica


class MainApp:
    def __init__(self, root, data):
        self.root = root
        self.data = data

        JAMENDO_CLIENT_ID = "651c30cf"

        # ---------------- WINDOW SETUP ---------------- #
        self.root.title(f"Spotitty - {data["username"].upper()}")
        self.root.overrideredirect(False)

        apply_mica(self.root)

        WIDTH = 1280
        HEIGHT = 720

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        x = (screen_w // 2) - (WIDTH // 2)
        y = (screen_h // 2) - (HEIGHT // 2)

        self.root.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")
        self.root.minsize(400, 300)
        self.root.maxsize(WIDTH, HEIGHT + 200)

        try:
            self.root.iconbitmap("assets/images/spotitty.ico")
        except:
            pass

        self._remove_title_bar()
        # ------------------------------------------------ #

        # ---------------- CORE OBJECTS ---------------- #
        self.player = Player()

        # UI HER ŞEYİ YÖNETİR
        self.ui = UI(
            self.root,
            self.player,
            JAMENDO_CLIENT_ID,
            self.data
        )
        # ------------------------------------------------ #

    def _remove_title_bar(self):
        self.root.update_idletasks()

        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())

        GWL_STYLE = -16
        WS_CAPTION = 0x00C00000
        WS_THICKFRAME = 0x00040000
        WS_SYSMENU = 0x00080000

        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)

        style &= ~WS_CAPTION
        style &= ~WS_THICKFRAME
        style &= ~WS_SYSMENU

        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)

        ctypes.windll.user32.SetWindowPos(
            hwnd, None, 0, 0, 0, 0,
            0x0027  # SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER
        )


# ---------------- APP START ---------------- #
if __name__ == "__main__":
    root = tk.Tk()
    MainApp(root, "demo")
    root.mainloop()
