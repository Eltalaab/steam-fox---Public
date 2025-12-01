import customtkinter as ctk
import os
import sys
import subprocess
import time
import threading
import tkinter as tk
from tkinter import messagebox
import requests
import webbrowser
import ctypes
import io
from PIL import Image
from datetime import datetime
import re

# إعدادات المظهر
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# الألوان
COLOR_BG = "#0f0f0f"
COLOR_CARD = "#1a1a1a"
COLOR_ACCENT = "#00e676"
COLOR_DELETE = "#ff4c4c"
COLOR_BYPASS = "#ffaa00"
COLOR_TEXT_GRAY = "#808080"

loading_token = 0

# مسارات ستيم
TARGET_PATH = r"C:\Program Files (x86)\Steam\config\stplug-in"
STEAM_EXE = r"C:\Program Files (x86)\Steam\steam.exe"

# قاعدة البيانات
GAMES_DB = {
    "Ubisoft": [
        {"name": "Assassin's Creed Mirage", "link": "https://pixeldrain.sriflix.my/mQr19FSK"},
        {"name": "Far Cry 6", "link": "https://drive.usercontent.google.com/download?id=1AnLR9TxK7-nbpYMP-fseXdmvOH2jO9jK&export=download&authuser=0&confirm=t"},
    ],
    "Rockstar": [
        {"name": "GTA V Enhanced", "link": "https://pixeldrain.sriflix.my/mV7oHSLZ"},
        {"name": "Red Dead Redemption 1", "link": "https://pixeldrain.sriflix.my/3y8bRtAP"},
    ],
    "EA Sports": [
        {"name": "FC 23 (Fix)", "link": "https://drive.usercontent.google.com/download?id=1cvp9tfw9pV2Nu21Hr5NghLclKOx4FK7i&export=download&confirm=t"},
    ],
    "Activision": [
        {"name": "Call of Duty MW2", "link": "https://pixeldrain.sriflix.my/Fq7dGXwd"},
    ]
}

# دوال مساعدة
def transform_to_direct_link(old_link):
    if not old_link: return ""
    match = re.search(r'(?:pixeldrain\.sriflix\.my|pixeldrain\.com\/u)\/([a-zA-Z0-9]+)', old_link)
    if match:
        file_id = match.group(1)
        return f"https://pixeldrain.com/api/file/{file_id}?download"
    if "drive.google.com" in old_link and "export=download" not in old_link:
        sep = "&" if "?" in old_link else "?"
        return old_link + sep + "export=download&confirm=t"
    return old_link

def download_selected_game():
    category = combo_category.get()
    game_name = combo_games.get()
    target_link = ""
    if category in GAMES_DB:
        for game in GAMES_DB[category]:
            if game['name'] == game_name:
                target_link = game['link']
                break
    if target_link:
        direct_link = transform_to_direct_link(target_link)
        lbl_status_msg.configure(text=f"Starting Download: {game_name}", text_color=COLOR_BYPASS)
        webbrowser.open(direct_link)
    else:
        messagebox.showerror("Error", "Please select a game first.")

def update_game_dropdown(choice):
    if choice in GAMES_DB:
        games_list = [g['name'] for g in GAMES_DB[choice]]
        combo_games.configure(values=games_list)
        if games_list:
            combo_games.set(games_list[0])
    else:
        combo_games.configure(values=["Select Category First"])

# دوال النظام والبحث (تم تبسيطها لضمان العمل)
def start_search_main():
    # Placeholder for search to prevent crash if backend fails
    lbl_status_msg.configure(text="Search functionality requires internet.", text_color=COLOR_TEXT_GRAY)

def add_file_logic():
    # Placeholder
    pass

def restart_steam_logic():
    try:
        subprocess.call("taskkill /F /IM steam.exe", shell=True)
        time.sleep(2)
        if os.path.exists(STEAM_EXE):
            subprocess.Popen([STEAM_EXE])
            lbl_status_msg.configure(text="Steam Restarted", text_color=COLOR_ACCENT)
    except:
        lbl_status_msg.configure(text="Error restarting Steam", text_color=COLOR_DELETE)

def btn_restart_click():
    threading.Thread(target=restart_steam_logic, daemon=True).start()

def open_steamdb(): webbrowser.open("https://steamdb.info/")

# --- بناء الواجهة ---
app = ctk.CTk()
app.title("Steam Fox Lite")
app.geometry("700x500")
app.configure(fg_color=COLOR_BG)

# محاولة تعيين ID للتطبيق (اختياري)
try:
    myappid = 'steam.fox.lite.v1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except: pass

# الهيدر
header_frame = ctk.CTkFrame(app, fg_color="transparent")
header_frame.pack(pady=15, padx=20, fill="x")
ctk.CTkLabel(header_frame, text="Steam Fox", font=("Segoe UI", 24, "bold"), text_color="white").pack(side="left")
ctk.CTkButton(header_frame, text="SteamDB", command=open_steamdb, width=80, height=25, fg_color="#333").pack(side="right")

# التبويبات
tab_view = ctk.CTkTabview(app, fg_color=COLOR_CARD)
tab_view.pack(pady=10, padx=20, fill="both", expand=True)
tab_home = tab_view.add("Downloader")
tab_library = tab_view.add("Manager")

# قسم التحميل المباشر
bypass_frame = ctk.CTkFrame(tab_home, fg_color="#222", corner_radius=10)
bypass_frame.pack(pady=20, padx=20, fill="x")

ctk.CTkLabel(bypass_frame, text="Direct Bypass Downloader", font=("Segoe UI", 16, "bold"), text_color=COLOR_BYPASS).pack(pady=10)

combo_frame = ctk.CTkFrame(bypass_frame, fg_color="transparent")
combo_frame.pack(pady=10)

categories = list(GAMES_DB.keys())
combo_category = ctk.CTkOptionMenu(combo_frame, values=categories, command=update_game_dropdown, width=150, fg_color="#333", button_color=COLOR_BYPASS)
combo_category.pack(side="left", padx=10)
combo_category.set("Category")

combo_games = ctk.CTkOptionMenu(combo_frame, values=["Select Category"], width=200, fg_color="#333")
combo_games.pack(side="left", padx=10)

ctk.CTkButton(combo_frame, text="Download", command=download_selected_game, width=100, fg_color=COLOR_ACCENT, text_color="black").pack(side="left", padx=10)

# زر إعادة تشغيل ستيم
ctk.CTkButton(tab_home, text="Restart Steam", command=btn_restart_click, fg_color="#333", border_color="#ff5555", border_width=1).pack(pady=20)

# شريط الحالة
lbl_status_msg = ctk.CTkLabel(app, text="Ready.", text_color="gray")
lbl_status_msg.pack(side="bottom", pady=5)

app.mainloop()