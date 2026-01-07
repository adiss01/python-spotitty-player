import ctypes
from ctypes import wintypes

DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMSBT_MAINWINDOW = 2  # Mica

def apply_mica(root):
    hwnd = wintypes.HWND(root.winfo_id())
    value = wintypes.DWORD(DWMSBT_MAINWINDOW)

    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_SYSTEMBACKDROP_TYPE,
        ctypes.byref(value),
        ctypes.sizeof(value)
    )
