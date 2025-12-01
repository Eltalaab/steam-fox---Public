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

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

COLOR_BG = "#0f0f0f"
COLOR_CARD = "#1a1a1a"
COLOR_ACCENT = "#00e676"
COLOR_DELETE = "#ff4c4c"
COLOR_BTN_HOVER = "#00b359"
COLOR_DEL_HOVER = "#d63030"
COLOR_BYPASS = "#ffaa00"
COLOR_BYPASS_HOVER = "#cc8800"
COLOR_TEXT = "#ffffff"
COLOR_TEXT_GRAY = "#808080"

loading_token = 0

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

TARGET_PATH = r"C:\Program Files (x86)\Steam\config\stplug-in"
STEAM_EXE = r"C:\Program Files (x86)\Steam\steam.exe"
ICON_NAME = resource_path("steam_fox_transparent.ico")

GAMES_DB = {
    "Ubisoft": [
        {"name": "Assassin's Creed Mirage", "link": "https://pixeldrain.sriflix.my/mQr19FSK"},
        {"name": "Assassin's Creed Valhalla", "link": "https://pixeldrain.sriflix.my/dhqF7jFA"},
        {"name": "Assassin's Creed Odyssey", "link": "https://pixeldrain.sriflix.my/B16nF29S"},
        {"name": "Far Cry 6", "link": "https://drive.usercontent.google.com/download?id=1AnLR9TxK7-nbpYMP-fseXdmvOH2jO9jK&export=download&authuser=0&confirm=t&uuid=f0e30e37-edbe-40a5-a1e7-c15cb0b883e1"},
        {"name": "Far Cry 5", "link": "https://pixeldrain.sriflix.my/uyo63Ut4"},
        {"name": "Watch Dogs Legion", "link": "https://drive.usercontent.google.com/download?id=1BU-DS2j0Uo3TG9xOmJyEqqXly1dACIrc&export=download&confirm=t&uuid=c5ed9788-ce8e-4853-9267-adc71509ddb4"},
        {"name": "Riders Republic", "link": "https://pixeldrain.sriflix.my/HrHenPFU"},
    ],
    "Rockstar": [
        {"name": "GTA V Enhanced", "link": "https://pixeldrain.sriflix.my/mV7oHSLZ"},
        {"name": "Red Dead Redemption 1", "link": "https://pixeldrain.sriflix.my/3y8bRtAP"},
        {"name": "GTA Trilogy (DE)", "link": "https://pixeldrain.sriflix.my/FHCjBX1c"},
        {"name": "Max Payne 3", "link": "https://pixeldrain.sriflix.my/k9VRbMtn"},
    ],
    "EA Sports": [
        {"name": "Battlefield 6 (Zip)", "link": "https://www.mediafire.com/file/f4tt31q0wkkyeow/Battlefield6.zip/file"},
        {"name": "FC 23 (Fix)", "link": "https://drive.usercontent.google.com/download?id=1cvp9tfw9pV2Nu21Hr5NghLclKOx4FK7i&export=download&confirm=t"},
        {"name": "FC 26 Showcase", "link": "https://download2392.mediafire.com/kqvxa1esy0rglIqBYsO0mrvrv5Mw9CKgOOAY9WH8zoinhLCGVObiwQ9hK7pH_r2-N7jzJTgYxItSwoxBguiiNcJlED8FY-m7Y5oxtLRwGyUXGayWRm5nI2yH5kpXRhgsXevjLMe-h0YWZAS35MzH67bWfrtvPbKw9N5JvEAAXkwYWfIC/ijt2llxtgd2zbl1/FC+26+MAGIC+UPDATE.rar"},
        {"name": "Need For Speed Heat", "link": "https://buzzheavier.com/mcz8tma72grt"},
        {"name": "Star Wars Jedi Survivor", "link": "https://pixeldrain.sriflix.my/Ag2yk3QX"},
    ],
    "Activision": [
        {"name": "Black Ops 3 (BOIII)", "link": "https://github.com/shiversoftdev/t7-patch/releases/download/current/t7_patch.exe"},
        {"name": "Call of Duty MW2", "link": "https://pixeldrain.sriflix.my/Fq7dGXwd"},
        {"name": "ProtoType 2", "link": "https://pixeldrain.sriflix.my/QZJc2ByW"},
    ],
    "Capcom & Others": [
        {"name": "Resident Evil 4 Remake", "link": "https://pixeldrain.sriflix.my/PP7sQkbp"},
        {"name": "God of War Ragnarök", "link": "https://pixeldrain.sriflix.my/cSJRY1RY"},
        {"name": "Hogwarts Legacy", "link": "https://pixeldrain.sriflix.my/PMKjJmYa"},
    ]
}


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

def get_game_details_full(app_id):
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=US&l=english"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data and str(app_id) in data and data[str(app_id)]['success']:
            game_data = data[str(app_id)]['data']
            name = game_data.get('name', 'Unknown Game')
            dlc_list = game_data.get('dlc', [])
            return name, dlc_list
    except:
        pass
    return None, []


def clear_results():
    for widget in search_results_frame.winfo_children():
        widget.destroy()

def show_results(items):
    search_results_frame.pack(pady=(0, 10), padx=40, fill="x", after=input_frame)
    for item in items:
        game_name = item['name']
        game_id = item['id']
        item_btn = ctk.CTkButton(search_results_frame, text=f"{game_name}  |  ID: {game_id}", anchor="w",
                                 fg_color="#2b2b2b", hover_color="#3a3a3a", height=35,
                                 command=lambda gid=game_id: select_game_id(gid))
        item_btn.pack(fill="x", pady=2)

def select_game_id(game_id):
    entry_file.delete(0, 'end')
    entry_file.insert(0, str(game_id))
    search_results_frame.pack_forget()
    lbl_status_msg.configure(text=f"Selected ID: {game_id}", text_color=COLOR_ACCENT)

def start_search_main():
    query = entry_file.get().strip()
    if not query:
        lbl_status_msg.configure(text="Please enter game name first", text_color="#ff5555")
        return
    threading.Thread(target=search_game_thread, args=(query,), daemon=True).start()

def get_filename():
    filename = entry_file.get().strip()
    if not filename:
        lbl_status_msg.configure(text="Please enter Steam App ID or Name", text_color="#ff5555")
        return None
    clean_name = filename.replace(".lua", "").replace(".LUA", "")
    if not filename.lower().endswith(".lua"): filename += ".lua"
    return filename, clean_name

def add_file_logic():
    threading.Thread(target=add_file_thread, daemon=True).start()

def add_file_thread():
    res = get_filename()
    if not res: return
    filename, clean_name = res
    content_id = clean_name
    if not clean_name.isdigit():
        lbl_status_msg.configure(text=f"Searching ID for: {clean_name}...", text_color="#ffaa00")
        found_id = fetch_id_from_name(clean_name)
        if found_id:
            content_id = found_id
            filename = f"{content_id}.lua" 
        else:
            lbl_status_msg.configure(text="ID Not Found! Cancelled.", text_color="#ff5555")
            return
    full_path = os.path.join(TARGET_PATH, filename)
    lua_content = ""
    source_msg = ""
    lbl_status_msg.configure(text=f"Checking ManifestHub for ID: {content_id}...", text_color="#ffaa00")
    github_content = fetch_manifest_from_hub(content_id)
    if github_content:
        lua_content = f"-- [Source: ManifestHub] Fetched by Steam Fox\n" + github_content
        source_msg = "Fetched from ManifestHub"
    else:
        lbl_status_msg.configure(text=f"Not in Hub. Trying Steam API...", text_color="#ffaa00")
        game_real_name, dlc_list = get_game_details_full(content_id)
        if not game_real_name and not dlc_list:
            lbl_status_msg.configure(text="Game data not found! No file created.", text_color="#ff5555")
            return
        if not game_real_name: game_real_name = clean_name
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lua_content = f"-- {content_id} Manifest and Lua created by Steam Fox\n-- {game_real_name}\n-- Created: {timestamp}\n\naddappid({content_id})\n"
        if dlc_list:
            lua_content += f"-- DLC List ({len(dlc_list)} items)\n"
            for dlc_id in dlc_list: lua_content += f"addappid({dlc_id})\n"
        source_msg = "Generated Locally"
    try:
        if not os.path.exists(TARGET_PATH): os.makedirs(TARGET_PATH)
        with open(full_path, 'w', encoding='utf-8') as f: f.write(lua_content)
        lbl_status_msg.configure(text=f"Success! {source_msg}", text_color=COLOR_ACCENT)
        app.after(0, lambda: entry_file.delete(0, 'end'))
        app.after(500, refresh_library_ui)
    except Exception as e:
        lbl_status_msg.configure(text=f"Write Error: {e}", text_color="#ff5555")

def load_image_from_url(url):
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            return ctk.CTkImage(light_image=image, dark_image=image, size=(120, 56))
    except: pass
    return None

def fetch_game_info_thread(file_list, token):
    for filename in file_list:
        if token != loading_token: return
        app_id = filename.replace(".lua", "")
        if not app_id.isdigit(): continue
        name = f"AppID: {app_id}"
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=US&l=english"
            r = requests.get(url, timeout=2)
            d = r.json()
            if d and d[str(app_id)]['success']: name = d[str(app_id)]['data']['name']
        except: pass
        if token != loading_token: return
        img_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"
        ctk_img = load_image_from_url(img_url)
        if token != loading_token: return
        app.after(0, lambda n=name, i=ctk_img, f=filename, aid=app_id: create_library_item(n, i, f, aid))

def delete_library_item(filename, widget_frame):
    full_path = os.path.join(TARGET_PATH, filename)
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            widget_frame.destroy()
            lbl_status_msg.configure(text=f"Deleted {filename}", text_color=COLOR_DELETE)
        else:
            widget_frame.destroy()
            lbl_status_msg.configure(text=f"File already gone: {filename}", text_color="#ffaa00")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def create_library_item(name, image, filename, app_id):
    item_frame = ctk.CTkFrame(library_scroll, fg_color="#222", corner_radius=8)
    item_frame.pack(fill="x", pady=4, padx=5)
    if image:
        lbl_img = ctk.CTkLabel(item_frame, text="", image=image)
        lbl_img.pack(side="left", padx=5, pady=5)
    else:
        lbl_img = ctk.CTkLabel(item_frame, text="No Image", width=120, height=56, fg_color="black", corner_radius=5)
        lbl_img.pack(side="left", padx=5, pady=5)
    info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
    info_frame.pack(side="left", fill="both", expand=True, padx=10)
    lbl_name = ctk.CTkLabel(info_frame, text=name, font=("Segoe UI", 14, "bold"), anchor="w", text_color="white")
    lbl_name.pack(fill="x", pady=(5,0))
    lbl_id = ctk.CTkLabel(info_frame, text=f"ID: {app_id} | File: {filename}", font=("Segoe UI", 11), text_color="gray", anchor="w")
    lbl_id.pack(fill="x")
    btn_del = ctk.CTkButton(item_frame, text="Delete 🗑️", width=100, height=35, fg_color=COLOR_DELETE, hover_color=COLOR_DEL_HOVER, text_color="white", font=("Segoe UI", 12, "bold"), command=lambda: delete_library_item(filename, item_frame))
    btn_del.pack(side="right", padx=10)

def refresh_library_ui():
    global loading_token
    loading_token += 1
    current_token = loading_token
    for widget in library_scroll.winfo_children(): widget.destroy()
    if not os.path.exists(TARGET_PATH): os.makedirs(TARGET_PATH)
    files = [f for f in os.listdir(TARGET_PATH) if f.endswith(".lua")]
    if not files:
        lbl_empty = ctk.CTkLabel(library_scroll, text="No Lua files found in folder.", text_color="gray")
        lbl_empty.pack(pady=20)
        return
    threading.Thread(target=fetch_game_info_thread, args=(files, current_token), daemon=True).start()

def restart_steam_logic():
    try:
        btn_restart.configure(state="disabled")
        lbl_status_msg.configure(text="Stopping Steam...", text_color="#ffaa00")
        subprocess.call("taskkill /F /IM steam.exe", shell=True)
        time.sleep(2)
        if os.path.exists(STEAM_EXE):
            lbl_status_msg.configure(text="Starting Steam...", text_color=COLOR_ACCENT)
            subprocess.Popen([STEAM_EXE])
            lbl_status_msg.configure(text="Steam Restarted Successfully", text_color=COLOR_ACCENT)
        else:
            lbl_status_msg.configure(text="Steam path not found", text_color="#ff5555")
    except Exception as e:
        lbl_status_msg.configure(text=f"Error: {e}", text_color="#ff5555")
    finally:
        btn_restart.configure(state="normal")

def btn_restart_click():
    threading.Thread(target=restart_steam_logic, daemon=True).start()

def open_steamdb(): webbrowser.open("https://steamdb.info/")

app = ctk.CTk()
app.title("Steam Fox") 
app.geometry("750x650") 
app.configure(fg_color=COLOR_BG)
app.resizable(True, True) 

try:
    myappid = 'steam-fox.tool.manager.v1.5.0' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app.iconbitmap(ICON_NAME)
except: pass

header_frame = ctk.CTkFrame(app, fg_color="transparent")
header_frame.pack(pady=(15, 5), padx=20, fill="x")
lbl_logo = ctk.CTkLabel(header_frame, text="Steam Fox", font=("Segoe UI", 24, "bold"), text_color="white")
lbl_logo.pack(side="left")
lbl_ver = ctk.CTkLabel(header_frame, text=" v1.5 ", fg_color="#113311", text_color=COLOR_ACCENT, corner_radius=5, font=("Arial", 11, "bold"))
lbl_ver.pack(side="left", padx=10)
btn_web = ctk.CTkButton(header_frame, text="Open SteamDB 🌐", command=open_steamdb, width=100, height=25, fg_color="#222", hover_color="#333")
btn_web.pack(side="right")

tab_view = ctk.CTkTabview(app, width=700, height=450, corner_radius=15, fg_color=COLOR_CARD)
tab_view.pack(pady=10, padx=20, fill="both", expand=True)
tab_home = tab_view.add("  Home & Downloader  ")
tab_library = tab_view.add("  Library Manager  ")

lbl_sub = ctk.CTkLabel(tab_home, text="Enter Steam App ID or Search Game", font=("Segoe UI", 13), text_color=COLOR_TEXT_GRAY)
lbl_sub.pack(pady=(15, 5))
input_frame = ctk.CTkFrame(tab_home, fg_color="transparent")
input_frame.pack(pady=5, padx=20, fill="x")
btn_search = ctk.CTkButton(input_frame, text="🔍 Search", command=start_search_main, width=80, height=45, fg_color="#333", hover_color="#444", border_width=1, border_color=COLOR_ACCENT)
btn_search.pack(side="left", padx=(0, 10))
entry_file = ctk.CTkEntry(input_frame, placeholder_text="App ID or Name", height=45, corner_radius=8, border_color=COLOR_ACCENT, border_width=1, fg_color="#121212", text_color="white", font=("Segoe UI", 14))
entry_file.pack(side="left", fill="x", expand=True)
search_results_frame = ctk.CTkScrollableFrame(tab_home, height=100, fg_color="#222", corner_radius=10)

ctk.CTkFrame(tab_home, height=2, fg_color="#333").pack(fill="x", padx=40, pady=20)
lbl_status_msg.pack(side="left", padx=10)


app.mainloop()
