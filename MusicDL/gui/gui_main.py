# The file will be explicitly rewritten to center all sidebar and main page content as described in the instructions above. All layout will use customtkinter and be visually balanced and modern.

import customtkinter as ctk
import os
from PIL import Image, ImageTk, ImageDraw
import threading
import tkinter as tk
from downloader.youtube_downloader import download_youtube
from downloader.spotify_downloader import download_spotify
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import ID3, TIT2, TPE1, APIC
import pygame

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_ACCENT = "#1DB954"  # Spotify green for accent

# --- UNIFIED COLOR PALETTE & THEME LOGIC ---
# Define color palettes for light and dark mode
LIGHT_PALETTE = {
    'bg': '#f4f6fb',
    'card': '#fff',
    'card_alt': '#f8fafc',
    'sidebar': '#232946',
    'sidebar_text': '#fff',
    'header': '#232946',
    'accent': '#1DB954',
    'accent_hover': '#1ed760',
    'text': '#232946',
    'text_secondary': '#5c5c5c',
    'border': '#e9ecef',
    'player_bar': '#232946',
    'player_text': '#fff',
    'player_subtext': '#b3b3b3',
}
DARK_PALETTE = {
    'bg': '#181a20',
    'card': '#232946',
    'card_alt': '#232946',
    'sidebar': '#10121a',
    'sidebar_text': '#fff',
    'header': '#fff',
    'accent': '#1DB954',
    'accent_hover': '#1ed760',
    'text': '#fff',
    'text_secondary': '#b3b3b3',
    'border': '#232946',
    'player_bar': '#10121a',
    'player_text': '#fff',
    'player_subtext': '#b3b3b3',
}
# Global palette reference
PALETTE = LIGHT_PALETTE.copy()

# --- ENSURE SINGLE, CORRECT set_theme DEFINITION ---
# Place the correct set_theme definition after the palette definitions. Remove any duplicate or old set_theme definitions.
# The correct set_theme should update PALETTE, call ctk.set_appearance_mode, and refresh all frames.

def set_theme(mode):
    global PALETTE
    if mode == 'dark':
        PALETTE = DARK_PALETTE.copy()
        ctk.set_appearance_mode('dark')
    else:
        PALETTE = LIGHT_PALETTE.copy()
        ctk.set_appearance_mode('light')
    # Refresh all frames if app is running
    app = ctk._get_appearance_mode_callback().__self__ if hasattr(ctk, '_get_appearance_mode_callback') else None
    if app and hasattr(app, 'frames'):
        for frame in app.frames.values():
            if hasattr(frame, 'refresh_theme'):
                frame.refresh_theme()

# Tooltip helper (moved to top for Sidebar use)
class CreateToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind('<Enter>', self.enter)
        self.widget.bind('<Leave>', self.leave)
    def enter(self, event=None):
        self.showtip()
    def leave(self, event=None):
        self.hidetip()
    def showtip(self):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox('insert') if hasattr(self.widget, 'bbox') else (0,0,0,0)
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f'+{x}+{y}')
        label = tk.Label(tw, text=self.text, justify='left', background='#ffffe0', relief='solid', borderwidth=1, font=('Segoe UI', 10, 'normal'))
        label.pack(ipadx=1)
    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class MusicDLApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MusicDL - Creative Edition")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(bg="#f4f6fb")
        self.iconify = False
        self.download_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'downloads'))
        self.frames = {}
        self.sidebar = Sidebar(self, self.show_frame)
        self.sidebar.pack(side="left", fill="y")
        self.container = ctk.CTkFrame(self, fg_color="#f4f6fb")
        self.container.pack(side="right", fill="both", expand=True)
        for F in (LandingPage, DownloadPage, HistoryPage, SettingsPage, AboutPage, PlayerPage, ConvertPage):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.show_frame("LandingPage")
        self.toast = Toast(self)

    def show_frame(self, page_name):
        for f in self.frames.values():
            f.place_forget()
        self.frames[page_name].place(relx=0, rely=0, relwidth=1, relheight=1)
        if hasattr(self.frames[page_name], "on_show"): self.frames[page_name].on_show()

    def show_toast(self, message, success=True):
        self.toast.show(message, success)

# --- SIDEBAR THEME REFACTOR ---
class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, show_frame):
        super().__init__(parent, width=80, fg_color=PALETTE['sidebar'])
        self.show_frame = show_frame
        self.expanded = False
        self.expanded_width = 220
        self.collapsed_width = 80
        self.current_width = self.collapsed_width
        self.configure(width=self.current_width, fg_color=PALETTE['sidebar'])
        # Container for vertical centering
        self.container = ctk.CTkFrame(self, fg_color=PALETTE['sidebar'])
        self.container.pack(expand=True, fill="y")
        self.toggle_btn = ctk.CTkButton(self.container, text="☰", width=60, height=60, fg_color=PALETTE['sidebar'], hover_color=PALETTE['accent'], corner_radius=30, command=self.toggle_sidebar, font=("Segoe UI", 22, "bold"))
        self.toggle_btn.pack(pady=(18, 10))
        self.logo = ctk.CTkLabel(self.container, text="🎵", font=("Segoe UI", 32, "bold"), text_color=PALETTE['accent'])
        self.logo.pack(pady=(0, 10))
        self.buttons = []
        self.button_labels = []
        nav = [
            ("Home", "LandingPage", "🏠"),
            ("Download", "DownloadPage", "⬇️"),
            ("Convert", "ConvertPage", "🔄"),
            ("Player", "PlayerPage", "🎧"),
            ("History", "HistoryPage", "🕑"),
            ("Settings", "SettingsPage", "⚙️"),
            ("About", "AboutPage", "ℹ️"),
        ]
        for text, page, icon in nav:
            btn_frame = ctk.CTkFrame(self.container, fg_color=PALETTE['sidebar'])
            btn_frame.pack(fill="x", pady=2)
            btn = ctk.CTkButton(btn_frame, text=icon, width=60, height=60, fg_color=PALETTE['sidebar'], hover_color=PALETTE['accent'], corner_radius=30, command=lambda p=page: show_frame(p), font=("Segoe UI", 22, "bold"))
            btn.pack(side="left", padx=(10,0))
            lbl = ctk.CTkLabel(btn_frame, text=text, font=("Segoe UI", 16, "bold"), text_color=PALETTE['sidebar_text'])
            lbl.pack(side="left", padx=10)
            self.buttons.append((btn, btn_frame))
            self.button_labels.append(lbl)
        self.update_sidebar()

    def toggle_sidebar(self):
        self.expanded = not self.expanded
        target_width = self.expanded_width if self.expanded else self.collapsed_width
        self.configure(width=target_width)
        self.current_width = target_width
        self.update_sidebar()

    def update_sidebar(self):
        for lbl in self.button_labels:
            lbl.pack_forget()
        if self.expanded:
            for i, (btn, frame) in enumerate(self.buttons):
                self.button_labels[i].pack(side="left", padx=10)
        # Tooltips for collapsed mode
        for i, (btn, frame) in enumerate(self.buttons):
            if not self.expanded:
                btn.tooltip = CreateToolTip(btn, self.button_labels[i].cget("text"))
            else:
                if hasattr(btn, 'tooltip'):
                    btn.tooltip.hidetip()
                    del btn.tooltip

    def refresh_theme(self):
        self.configure(fg_color=PALETTE['sidebar'])
        self.container.configure(fg_color=PALETTE['sidebar'])
        self.toggle_btn.configure(fg_color=PALETTE['sidebar'], hover_color=PALETTE['accent'])
        self.logo.configure(text_color=PALETTE['accent'])
        for i, (btn, frame) in enumerate(self.buttons):
            btn.configure(fg_color=PALETTE['sidebar'], hover_color=PALETTE['accent'])
            frame.configure(fg_color=PALETTE['sidebar'])
            self.button_labels[i].configure(text_color=PALETTE['sidebar_text'])

# --- LANDING PAGE THEME REFACTOR ---
class LandingPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=PALETTE['bg'])
        center_frame = ctk.CTkFrame(self, fg_color=PALETTE['bg'])
        center_frame.pack(expand=True, fill='both')
        self.icon = ctk.CTkLabel(center_frame, text="▶️", font=("Segoe UI", 120, "bold"), text_color=PALETTE['accent'])
        self.icon.pack(pady=(0, 20), anchor='center')
        self.title = ctk.CTkLabel(center_frame, text="MUSICDL", font=("Segoe UI", 44, "bold"), text_color=PALETTE['header'])
        self.title.pack(pady=(0, 10), anchor='center')
        self.subtitle = ctk.CTkLabel(center_frame, text="Your Creative Music Downloader", font=("Segoe UI", 20), text_color=PALETTE['text'])
        self.subtitle.pack(pady=(0, 40), anchor='center')
        self.start_btn = ctk.CTkButton(center_frame, text="Start Downloading", fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'], font=("Segoe UI", 22, "bold"), corner_radius=30, width=260, height=60, command=lambda: controller.show_frame("DownloadPage"))
        self.start_btn.pack(anchor='center')
        self.info = ctk.CTkLabel(center_frame, text="Paste links, download, and manage your music with style!", font=("Segoe UI", 16), text_color=PALETTE['text_secondary'])
        self.info.pack(pady=(40, 0), anchor='center')
        self.center_frame = center_frame

    def refresh_theme(self):
        self.configure(fg_color=PALETTE['bg'])
        self.center_frame.configure(fg_color=PALETTE['bg'])
        self.icon.configure(text_color=PALETTE['accent'])
        self.title.configure(text_color=PALETTE['header'])
        self.subtitle.configure(text_color=PALETTE['text'])
        self.start_btn.configure(fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'])
        self.info.configure(text_color=PALETTE['text_secondary'])

# --- DOWNLOAD PAGE THEME REFACTOR ---
AUDIO_FORMATS = ["mp3", "m4a", "flac", "wav", "opus", "ogg", "aac"]
class DownloadPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=PALETTE['bg'])
        self.controller = controller
        center_frame = ctk.CTkFrame(self, fg_color=PALETTE['bg'])
        center_frame.pack(expand=True, fill='both')
        self.header = ctk.CTkLabel(center_frame, text="Download Music", font=("Segoe UI", 32, "bold"), text_color=PALETTE['accent'])
        self.header.pack(pady=(30, 10), anchor='center')
        self.link_entry = ctk.CTkEntry(center_frame, placeholder_text="Paste YouTube/Spotify link here...", width=500, height=40, font=("Segoe UI", 16))
        self.link_entry.pack(pady=10, anchor='center')
        # Add format dropdown
        self.format_var = ctk.StringVar(value=AUDIO_FORMATS[0])
        self.format_menu = ctk.CTkOptionMenu(center_frame, values=AUDIO_FORMATS, variable=self.format_var, width=180, font=("Segoe UI", 14))
        self.format_menu.pack(pady=8)
        self.add_btn = ctk.CTkButton(center_frame, text="Add to Queue", fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'], font=("Segoe UI", 16, "bold"), corner_radius=20, width=180, height=40, command=self.add_to_queue)
        self.add_btn.pack(pady=(0, 10), anchor='center')
        self.queue_frame = ctk.CTkFrame(center_frame, fg_color=PALETTE['card'], corner_radius=20)
        self.queue_frame.pack(pady=10, padx=40, fill="x")
        self.queue = []
        self.queue_labels = []
        self.download_btn = ctk.CTkButton(center_frame, text="⬇ Download All", fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'], font=("Segoe UI", 18, "bold"), corner_radius=30, width=220, height=50, command=self.download_all)
        self.download_btn.pack(pady=20, anchor='center')
        self.progress_bar = ctk.CTkProgressBar(center_frame, width=500, height=20, corner_radius=10, progress_color=PALETTE['accent'])
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(10, 0), anchor='center')
        self.status_label = ctk.CTkLabel(center_frame, text="", font=("Segoe UI", 16), text_color=PALETTE['text'])
        self.status_label.pack(pady=(10, 0), anchor='center')
        self.fab = ctk.CTkButton(center_frame, text="+", fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'], font=("Segoe UI", 32, "bold"), corner_radius=40, width=80, height=80, command=self.show_add_dialog)
        self.fab.place(relx=0.92, rely=0.85)
        self.center_frame = center_frame

    def refresh_theme(self):
        self.configure(fg_color=PALETTE['bg'])
        self.center_frame.configure(fg_color=PALETTE['bg'])
        self.header.configure(text_color=PALETTE['accent'])
        self.add_btn.configure(fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'])
        self.queue_frame.configure(fg_color=PALETTE['card'])
        self.download_btn.configure(fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'])
        self.progress_bar.configure(progress_color=PALETTE['accent'])
        self.status_label.configure(text_color=PALETTE['text'])
        self.fab.configure(fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'])
        for lbl in self.queue_labels:
            lbl.configure(text_color=PALETTE['text'])

    def add_to_queue(self):
        link = self.link_entry.get().strip()
        fmt = self.format_var.get()
        if link:
            self.queue.append((link, fmt))
            lbl = ctk.CTkLabel(self.queue_frame, text=f"{link} [{fmt}]", font=("Segoe UI", 14), text_color=PALETTE['text'], anchor="w")
            lbl.pack(fill="x", padx=10, pady=4)
            self.queue_labels.append(lbl)
            self.link_entry.delete(0, "end")
            self.controller.show_toast("Added to queue!", success=True)

    def download_all(self):
        if not self.queue:
            self.controller.show_toast("Queue is empty!", success=False)
            return
        self.status_label.configure(text="Starting downloads...")
        self.progress_bar.set(0)
        self.update_idletasks()
        total = len(self.queue)
        completed = 0
        def status_callback(msg):
            if isinstance(msg, str):
                self.status_label.configure(text=msg)
            elif isinstance(msg, dict) and 'downloaded_bytes' in msg and 'total_bytes' in msg:
                percent = msg['downloaded_bytes'] / max(1, msg['total_bytes'])
                self.progress_bar.set(percent)
                self.status_label.configure(text=f"Downloading: {int(percent*100)}%")
            self.update_idletasks()
        def do_download():
            nonlocal completed
            for i, (link, fmt) in enumerate(self.queue):
                self.status_label.configure(text=f"Processing {i+1}/{total}")
                self.progress_bar.set(i/total)
                self.update_idletasks()
                if 'spotify.com' in link:
                    download_spotify(link, 'audio', status_callback, self.controller.download_dir, fmt)
                else:
                    download_youtube(link, 'audio', status_callback, self.controller.download_dir, fmt)
                completed += 1
                self.progress_bar.set(completed/total)
                self.status_label.configure(text=f"Completed {completed}/{total}")
                self.queue_labels[i].destroy()
            self.queue.clear()
            self.queue_labels.clear()
            self.status_label.configure(text="All downloads finished!")
            self.controller.show_toast("All downloads finished!", success=True)
        threading.Thread(target=do_download, daemon=True).start()

    def show_add_dialog(self):
        # Floating action button: show a dialog to add a link
        import tkinter.simpledialog
        link = tkinter.simpledialog.askstring("Add Link", "Paste YouTube/Spotify link:")
        if link:
            self.link_entry.delete(0, "end")
            self.link_entry.insert(0, link)
            self.add_to_queue()

class HistoryPage(ctk.CTkFrame):
    SUPPORTED_EXTS = ('.mp3', '.m4a', '.flac', '.wav', '.opus')
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=PALETTE['bg'])
        self.controller = controller
        center_frame = ctk.CTkFrame(self, fg_color=PALETTE['bg'])
        center_frame.pack(expand=True, fill='both')
        self.header = ctk.CTkLabel(center_frame, text="Download History", font=("Segoe UI", 32, "bold"), text_color=PALETTE['accent'])
        self.header.pack(pady=(30, 10), anchor='center')
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(center_frame, placeholder_text="Search downloads...", width=400, height=36, font=("Segoe UI", 14), textvariable=self.search_var)
        self.search_entry.pack(pady=10, anchor='center')
        self.search_entry.bind('<KeyRelease>', lambda e: self.populate_history())
        self.list_frame = ctk.CTkScrollableFrame(center_frame, fg_color=PALETTE['card'], corner_radius=20)
        self.list_frame.pack(pady=10, padx=40, fill="both", expand=True)
        self.center_frame = center_frame
        self.populate_history()

    def refresh_theme(self):
        self.configure(fg_color=PALETTE['bg'])
        self.center_frame.configure(fg_color=PALETTE['bg'])
        self.header.configure(text_color=PALETTE['accent'])
        self.search_entry.configure(fg_color=PALETTE['card'], text_color=PALETTE['text'])
        self.list_frame.configure(fg_color=PALETTE['card'])
        self.populate_history()

    def populate_history(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        downloads_dir = self.controller.download_dir
        files = [f for f in os.listdir(downloads_dir) if f.lower().endswith(self.SUPPORTED_EXTS)]
        query = self.search_var.get().lower()
        # Header row
        header = ctk.CTkFrame(self.list_frame, fg_color=PALETTE['card'])
        header.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkLabel(header, text="", width=50, fg_color=PALETTE['card']).pack(side="left")
        ctk.CTkLabel(header, text="Title", font=("Segoe UI", 15, "bold"), anchor="w", text_color=PALETTE['header'], fg_color=PALETTE['card']).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(header, text="Artist", font=("Segoe UI", 15, "bold"), anchor="w", text_color=PALETTE['header'], fg_color=PALETTE['card']).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(header, text="Format", font=("Segoe UI", 15, "bold"), anchor="w", text_color=PALETTE['header'], fg_color=PALETTE['card']).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(header, text="Actions", font=("Segoe UI", 15, "bold"), anchor="w", text_color=PALETTE['header'], fg_color=PALETTE['card']).pack(side="left", fill="x", expand=True)
        for i, file in enumerate(files):
            if query and query not in file.lower():
                continue
            file_path = os.path.join(downloads_dir, file)
            ext = os.path.splitext(file)[1].lower()
            title, artist, cover_img = file, '', None
            try:
                if ext == '.mp3':
                    audio = MP3(file_path, ID3=ID3)
                    title = audio.tags.get('TIT2', title)
                    artist = audio.tags.get('TPE1', artist)
                    if isinstance(title, TIT2):
                        title = title.text[0]
                    if isinstance(artist, TPE1):
                        artist = artist.text[0]
                    if 'APIC:' in audio.tags:
                        apic = audio.tags['APIC:']
                        from io import BytesIO
                        from PIL import Image
                        img = Image.open(BytesIO(apic.data)).resize((40, 40))
                        cover_img = ctk.CTkImage(light_image=img, size=(40, 40))
                elif ext == '.flac':
                    audio = FLAC(file_path)
                    title = audio.get('title', [title])[0]
                    artist = audio.get('artist', [artist])[0]
                    if audio.pictures:
                        from PIL import Image
                        from io import BytesIO
                        img = Image.open(BytesIO(audio.pictures[0].data)).resize((40, 40))
                        cover_img = ctk.CTkImage(light_image=img, size=(40, 40))
                elif ext in ('.m4a', '.mp4'):
                    audio = MP4(file_path)
                    title = audio.tags.get('\u0000nam', [title])[0]
                    artist = audio.tags.get('\u0000ART', [artist])[0]
                    if 'covr' in audio:
                        from PIL import Image
                        from io import BytesIO
                        img = Image.open(BytesIO(audio['covr'][0])).resize((40, 40))
                        cover_img = ctk.CTkImage(light_image=img, size=(40, 40))
                elif ext == '.opus':
                    audio = OggVorbis(file_path)
                    title = audio.get('title', [title])[0]
                    artist = audio.get('artist', [artist])[0]
            except Exception:
                pass
            # Alternating row color
            row_color = PALETTE['card_alt'] if i % 2 == 0 else PALETTE['card']
            row = ctk.CTkFrame(self.list_frame, fg_color=row_color, corner_radius=12, height=56)
            row.pack(fill="x", padx=10, pady=2)
            # Cover art
            if cover_img:
                icon = ctk.CTkLabel(row, image=cover_img, text="", width=50, fg_color=row_color)
            else:
                icon = ctk.CTkLabel(row, text="🎵", font=("Segoe UI", 24), width=50, fg_color=row_color, text_color=PALETTE['header'])
            icon.pack(side="left", pady=8)
            # Title
            title_lbl = ctk.CTkLabel(row, text=f"{title}", font=("Segoe UI", 14, "bold"), text_color=PALETTE['text'], width=220, anchor="w", fg_color=row_color)
            title_lbl.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=8)
            # Artist
            artist_lbl = ctk.CTkLabel(row, text=f"{artist}", font=("Segoe UI", 13), text_color=PALETTE['text'], width=140, anchor="w", fg_color=row_color)
            artist_lbl.pack(side="left", fill="x", expand=True, pady=8)
            # Format
            fmt_lbl = ctk.CTkLabel(row, text=ext[1:].upper(), font=("Segoe UI", 13), text_color=PALETTE['text'], width=70, anchor="w", fg_color=row_color)
            fmt_lbl.pack(side="left", fill="x", expand=True, pady=8)
            # Actions (play, open, delete)
            actions = ctk.CTkFrame(row, fg_color=row_color)
            actions.pack(side="left", fill="x", expand=True, padx=0, pady=8)
            play_btn = ctk.CTkButton(actions, text="▶", width=36, height=36, fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'], corner_radius=18, font=("Segoe UI", 16), command=lambda f=file_path: self.controller.frames['PlayerPage'].add_to_queue_and_play(f))
            play_btn.pack(side="left", padx=6)
            open_frame = ctk.CTkFrame(actions, fg_color='transparent', border_width=1, border_color=PALETTE['accent'], corner_radius=22)
            open_frame.pack(side="left", padx=8)
            open_btn = ctk.CTkButton(open_frame, text="📂", width=44, height=44, fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'], corner_radius=22, font=("Segoe UI", 20), text_color="#fff", command=lambda f=file_path: os.startfile(f))
            open_btn.pack()
            CreateToolTip(open_btn, text="Open file location")
            del_frame = ctk.CTkFrame(actions, fg_color='transparent', border_width=1, border_color="#ff4d4f", corner_radius=22)
            del_frame.pack(side="left", padx=8)
            del_btn = ctk.CTkButton(del_frame, text="❌", width=44, height=44, fg_color="#ff4d4f", hover_color="#ff7875", corner_radius=22, font=("Segoe UI", 20), text_color="#fff", command=lambda f=file_path: self.delete_file(f))
            del_btn.pack()
            CreateToolTip(del_btn, text="Delete this file")

    def delete_file(self, file_path):
        try:
            os.remove(file_path)
            self.populate_history()
            self.controller.show_toast("File deleted!", success=True)
        except Exception as e:
            self.controller.show_toast(f"Delete failed: {e}", success=False)

    def on_show(self):
        self.populate_history()

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=PALETTE['bg'])
        self.controller = controller
        self.header = ctk.CTkLabel(self, text="Settings", font=("Segoe UI", 32, "bold"), text_color=PALETTE['accent'])
        self.header.pack(pady=(30, 10))
        self.theme_switch = ctk.CTkSwitch(self, text="Dark Mode", command=self.toggle_theme, font=("Segoe UI", 16))
        self.theme_switch.pack(pady=10)
        self.format_label = ctk.CTkLabel(self, text="Output Format:", font=("Segoe UI", 16), text_color=PALETTE['text'])
        self.format_label.pack(pady=(20, 0))
        self.format_menu = ctk.CTkOptionMenu(self, values=["mp3", "opus", "m4a", "flac", "wav", "original"], width=180, font=("Segoe UI", 14))
        self.format_menu.pack(pady=8)
        self.folder_label = ctk.CTkLabel(self, text="Download Folder:", font=("Segoe UI", 16), text_color=PALETTE['text'])
        self.folder_label.pack(pady=(20, 0))
        self.folder_btn = ctk.CTkButton(self, text="Choose Folder", fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'], font=("Segoe UI", 14), corner_radius=18, command=self.choose_folder)
        self.folder_btn.pack(pady=8)
        self.folder_path = ctk.CTkLabel(self, text=self.controller.download_dir, font=("Segoe UI", 12), text_color=PALETTE['text_secondary'])
        self.folder_path.pack(pady=(0, 10))

    def refresh_theme(self):
        self.configure(fg_color=PALETTE['bg'])
        self.header.configure(text_color=PALETTE['accent'])
        self.format_label.configure(text_color=PALETTE['text'])
        self.folder_label.configure(text_color=PALETTE['text'])
        self.folder_btn.configure(fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'])
        self.folder_path.configure(text_color=PALETTE['text_secondary'])

    def toggle_theme(self):
        mode = 'dark' if self.theme_switch.get() else 'light'
        set_theme(mode)

    def choose_folder(self):
        import tkinter.filedialog
        folder = tkinter.filedialog.askdirectory()
        if folder:
            self.controller.download_dir = folder
            self.folder_path.configure(text=folder)
            self.controller.show_toast("Download folder updated!", success=True)

# --- ABOUT PAGE THEME REFACTOR ---
class AboutPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=PALETTE['bg'])
        self.controller = controller
        self.header = ctk.CTkLabel(self, text="About MusicDL", font=("Segoe UI", 32, "bold"), text_color=PALETTE['accent'])
        self.header.pack(pady=(30, 10))
        self.info = ctk.CTkLabel(self, text="A creative, modern music downloader.\nBuilt with Python and customtkinter.\nInspired by mobile app design.", font=("Segoe UI", 18), text_color=PALETTE['text'], justify="center")
        self.info.pack(pady=30)
        # Load and display circular profile image using CTkImage
        img_path = os.path.join(os.path.dirname(__file__), 'resources', 'ARAGON, DANIELLE JOHN P. 2X2 1X1WNT RECOPY NONT.JPG')
        size = 120
        try:
            img = Image.open(img_path).convert("RGBA").resize((size, size), Image.LANCZOS)
            mask = Image.new('L', (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)
            img.putalpha(mask)
            self.profile_img = ctk.CTkImage(light_image=img, size=(size, size))
            self.avatar = ctk.CTkLabel(self, image=self.profile_img, text="", fg_color=PALETTE['bg'])
            self.avatar.pack(pady=10)
        except Exception as e:
            self.avatar = ctk.CTkLabel(self, text="👤", font=("Segoe UI", 80), fg_color=PALETTE['bg'], text_color=PALETTE['header'])
            self.avatar.pack(pady=10)
        self.credits = ctk.CTkLabel(self, text="Developed by Danielle Aragon", font=("Segoe UI", 14), text_color=PALETTE['text_secondary'])
        self.credits.pack(pady=10)

    def refresh_theme(self):
        self.configure(fg_color=PALETTE['bg'])
        self.header.configure(text_color=PALETTE['accent'])
        self.info.configure(text_color=PALETTE['text'])
        self.avatar.configure(fg_color=PALETTE['bg'], text_color=PALETTE['header'])
        self.credits.configure(text_color=PALETTE['text_secondary'])

# --- TOAST THEME REFACTOR ---
class Toast(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=PALETTE['header'])
        self.label = ctk.CTkLabel(self, text="", font=("Segoe UI", 16), text_color=PALETTE['player_text'])
        self.label.pack(padx=20, pady=10)
        self.place_forget()
        self.after_id = None

    def show(self, message, success=True):
        self.label.configure(text=message, text_color=PALETTE['player_text'] if success else "#ff4d4f")
        self.configure(fg_color=PALETTE['header'])
        self.place(relx=0.5, rely=0.05, anchor="n")
        if self.after_id: self.after_cancel(self.after_id)
        self.after_id = self.after(2200, self.place_forget)

    def refresh_theme(self):
        self.configure(fg_color=PALETTE['header'])
        self.label.configure(text_color=PALETTE['player_text'])

# --- AUDIO PLAYBACK WITH PYGAME.MIXER ---
pygame.mixer.init()

class PlayerPage(ctk.CTkFrame):
    SUPPORTED_EXTS = ('.mp3', '.m4a', '.flac', '.wav', '.opus')
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=PALETTE['bg'])
        self.controller = controller
        self.queue = []
        self.queue_index = 0
        self.current_file = None
        self.current_cover = None
        self.current_title = ""
        self.current_artist = ""
        # Centered player panel
        self.center_panel = ctk.CTkFrame(self, fg_color='transparent')
        self.center_panel.place(relx=0.5, rely=0.5, anchor="center")
        self._init_player_panel()

    def refresh_theme(self):
        self.configure(fg_color=PALETTE['bg'])
        self.center_panel.configure(fg_color=PALETTE['bg'])
        self.cover_frame.configure(fg_color=PALETTE['player_bar'], border_color=PALETTE['accent'])
        self.cover_label.configure(fg_color=PALETTE['player_bar'], text_color=PALETTE['player_text'])
        self.song_title.configure(text_color=PALETTE['player_text'])
        self.song_artist.configure(text_color=PALETTE['player_subtext'])
        self.prev_btn.configure(fg_color=PALETTE['player_bar'], hover_color=PALETTE['border'])
        self.play_btn.configure(fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'])
        self.next_btn.configure(fg_color=PALETTE['player_bar'], hover_color=PALETTE['border'])
        self.seek_bar.configure(progress_color=PALETTE['accent'])
        self.elapsed_label.configure(text_color=PALETTE['player_text'])
        self.duration_label.configure(text_color=PALETTE['player_text'])
        self._seek_time_label.configure(text_color=PALETTE['accent'], fg_color=PALETTE['card'])
        self.volume_slider.configure(progress_color=PALETTE['accent'])
        self.queue_btn.configure(fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'])
        # Update all frames/labels in the queue dialog and other nested widgets if needed

    def _init_player_panel(self):
        # Cover art with border
        self.cover_frame = ctk.CTkFrame(self.center_panel, fg_color=PALETTE['player_bar'], border_width=3, border_color=PALETTE['accent'], corner_radius=16, width=116, height=116)
        self.cover_frame.pack(pady=(0, 18))
        self.cover_label = ctk.CTkLabel(self.cover_frame, text="🎵", width=110, height=110, font=("Segoe UI", 54), fg_color=PALETTE['player_bar'], text_color=PALETTE['player_text'], corner_radius=13)
        self.cover_label.place(relx=0.5, rely=0.5, anchor="center")
        # Song info
        self.song_title = ctk.CTkLabel(self.center_panel, text="No track selected", font=("Segoe UI", 22, "bold"), text_color=PALETTE['player_text'], anchor="center")
        self.song_title.pack(pady=(0, 2))
        self.song_artist = ctk.CTkLabel(self.center_panel, text="", font=("Segoe UI", 16), text_color=PALETTE['player_subtext'], anchor="center")
        self.song_artist.pack(pady=(0, 18))
        # Controls row
        controls_row = ctk.CTkFrame(self.center_panel, fg_color='transparent')
        controls_row.pack(pady=(0, 18))
        self.prev_btn = ctk.CTkButton(controls_row, text="⏮", width=48, height=48, fg_color=PALETTE['player_bar'], hover_color=PALETTE['border'], font=("Segoe UI", 22), corner_radius=24, command=self._prev_track)
        self.prev_btn.pack(side="left", padx=10)
        CreateToolTip(self.prev_btn, text="Previous track")
        self.play_btn = ctk.CTkButton(controls_row, text="▶", width=64, height=64, fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'], font=("Segoe UI", 28, "bold"), corner_radius=32, command=self._toggle_play)
        self.play_btn.pack(side="left", padx=10)
        CreateToolTip(self.play_btn, text="Play/Pause")
        self.next_btn = ctk.CTkButton(controls_row, text="⏭", width=48, height=48, fg_color=PALETTE['player_bar'], hover_color=PALETTE['border'], font=("Segoe UI", 22), corner_radius=24, command=self._next_track)
        self.next_btn.pack(side="left", padx=10)
        CreateToolTip(self.next_btn, text="Next track")
        # Seek bar (stub)
        progress_row = ctk.CTkFrame(self.center_panel, fg_color='transparent')
        progress_row.pack(pady=(0, 10), fill='x')
        self.elapsed_label = ctk.CTkLabel(progress_row, text="0:00", font=("Segoe UI", 14), text_color=PALETTE['player_text'])
        self.elapsed_label.pack(side="left", padx=(0, 8))
        self.seek_bar = ctk.CTkProgressBar(progress_row, width=320, height=10, corner_radius=5, progress_color=PALETTE['accent'])
        self.seek_bar.pack(side="left", fill='x', expand=True)
        self.duration_label = ctk.CTkLabel(progress_row, text="0:00", font=("Segoe UI", 14), text_color=PALETTE['player_text'])
        self.duration_label.pack(side="left", padx=(8, 0))
        # Floating time label for seek preview
        self._seek_time_label = ctk.CTkLabel(self.center_panel, text="", font=("Segoe UI", 13, "bold"), text_color=PALETTE['accent'], fg_color=PALETTE['card'], corner_radius=8)
        self._seek_time_label.place_forget()
        # Volume slider (stub)
        vol_row = ctk.CTkFrame(self.center_panel, fg_color='transparent')
        vol_row.pack(pady=(0, 18))
        ctk.CTkLabel(vol_row, text="🔊", font=("Segoe UI", 16), text_color=PALETTE['player_text']).pack(side="left", padx=(0, 6))
        self.volume_slider = ctk.CTkSlider(vol_row, from_=0, to=100, width=120, height=16, number_of_steps=20, progress_color=PALETTE['accent'], command=self._set_volume)
        self.volume_slider.pack(side="left")
        self.volume_slider.set(80)
        CreateToolTip(self.volume_slider, text="Volume")
        # Queue button
        self.queue_btn = ctk.CTkButton(self.center_panel, text="Manage Queue", fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'], font=("Segoe UI", 16, "bold"), corner_radius=20, width=160, height=44, command=self.open_queue_dialog)
        self.queue_btn.pack(pady=(0, 0))
        CreateToolTip(self.queue_btn, text="Pick and arrange tracks to play")
        # --- LIVE & SEEKABLE PROGRESS BAR FOR PLAYER ---
        # 1. Use a timer to update the progress bar with current playback position.
        # 2. Show elapsed and total time next to the bar.
        # 3. Allow user to drag/click the progress bar to seek.
        # 4. Add comments for maintainability.
        self.seek_bar.bind('<Button-1>', self._on_seek_click)
        self.seek_bar.bind('<B1-Motion>', self._on_seek_drag)
        self.seek_bar.bind('<ButtonRelease-1>', self._on_seek_release)
        self._seek_dragging = False

    def open_queue_dialog(self):
        # Customtkinter modal for queue selection and arrangement
        dialog = ctk.CTkToplevel(self)
        dialog.title("Select and Arrange Queue")
        dialog.geometry("520x600")
        dialog.grab_set()
        dialog.configure(fg_color=PALETTE['bg'])
        # Scrollable frame for tracks
        scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color=PALETTE['bg'], width=480, height=400, corner_radius=16)
        scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)
        # Gather metadata for all files
        downloads_dir = self.controller.download_dir
        files = [f for f in os.listdir(downloads_dir) if f.lower().endswith(self.SUPPORTED_EXTS)]
        self.track_widgets = []
        tracks = []
        for idx, file in enumerate(files):
            file_path = os.path.join(downloads_dir, file)
            ext = os.path.splitext(file)[1].lower()
            title, artist, cover_img = file, '', None
            try:
                if ext == '.mp3':
                    audio = MP3(file_path, ID3=ID3)
                    title = audio.tags.get('TIT2', title)
                    artist = audio.tags.get('TPE1', artist)
                    if isinstance(title, TIT2):
                        title = title.text[0]
                    if isinstance(artist, TPE1):
                        artist = artist.text[0]
                    if 'APIC:' in audio.tags:
                        apic = audio.tags['APIC:']
                        from io import BytesIO
                        from PIL import Image
                        img = Image.open(BytesIO(apic.data)).resize((48, 48))
                        cover_img = ctk.CTkImage(light_image=img, size=(48, 48))
                elif ext == '.flac':
                    audio = FLAC(file_path)
                    title = audio.get('title', [title])[0]
                    artist = audio.get('artist', [artist])[0]
                    if audio.pictures:
                        from PIL import Image
                        from io import BytesIO
                        img = Image.open(BytesIO(audio.pictures[0].data)).resize((48, 48))
                        cover_img = ctk.CTkImage(light_image=img, size=(48, 48))
                elif ext in ('.m4a', '.mp4'):
                    audio = MP4(file_path)
                    title = audio.tags.get('\u0000nam', [title])[0]
                    artist = audio.tags.get('\u0000ART', [artist])[0]
                    if 'covr' in audio:
                        from PIL import Image
                        from io import BytesIO
                        img = Image.open(BytesIO(audio['covr'][0])).resize((48, 48))
                        cover_img = ctk.CTkImage(light_image=img, size=(48, 48))
                elif ext == '.opus':
                    audio = OggVorbis(file_path)
                    title = audio.get('title', [title])[0]
                    artist = audio.get('artist', [artist])[0]
            except Exception:
                pass
            tracks.append((file_path, title, artist, cover_img))
        # Track selection and arrangement widgets
        self.selected_indices = set()
        for i, (file_path, title, artist, cover_img) in enumerate(tracks):
            row = ctk.CTkFrame(scroll_frame, fg_color=PALETTE['card'], corner_radius=12)
            row.pack(fill="x", pady=6, padx=4)
            # Checkbox for selection
            var = tk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(row, variable=var, fg_color=PALETTE['accent'], border_color=PALETTE['border'])
            cb.pack(side="left", padx=6)
            # Cover art
            if cover_img:
                icon = ctk.CTkLabel(row, image=cover_img, text="", width=48)
            else:
                icon = ctk.CTkLabel(row, text="🎵", font=("Segoe UI", 24), width=48, text_color=PALETTE['header'])
            icon.pack(side="left", padx=6)
            # Title/artist
            info_frame = ctk.CTkFrame(row, fg_color=PALETTE['card'])
            info_frame.pack(side="left", fill="x", expand=True)
            title_lbl = ctk.CTkLabel(info_frame, text=title, font=("Segoe UI", 14, "bold"), text_color=PALETTE['text'], anchor="w")
            title_lbl.pack(anchor="w")
            artist_lbl = ctk.CTkLabel(info_frame, text=artist, font=("Segoe UI", 12), text_color=PALETTE['text_secondary'], anchor="w")
            artist_lbl.pack(anchor="w")
            # Up/Down buttons
            up_btn = ctk.CTkButton(row, text="↑", width=32, height=32, fg_color=PALETTE['card'], hover_color=PALETTE['border'], font=("Segoe UI", 16), corner_radius=16)
            up_btn.pack(side="right", padx=2)
            down_btn = ctk.CTkButton(row, text="↓", width=32, height=32, fg_color=PALETTE['card'], hover_color=PALETTE['border'], font=("Segoe UI", 16), corner_radius=16)
            down_btn.pack(side="right", padx=2)
            self.track_widgets.append((row, var, up_btn, down_btn))
        # Up/Down logic
        def move_row(i, direction):
            if direction == 'up' and i > 0:
                self.track_widgets[i][0].pack_forget()
                self.track_widgets[i][0].pack(before=self.track_widgets[i-1][0])
                self.track_widgets[i], self.track_widgets[i-1] = self.track_widgets[i-1], self.track_widgets[i]
            elif direction == 'down' and i < len(self.track_widgets)-1:
                self.track_widgets[i][0].pack_forget()
                self.track_widgets[i][0].pack(after=self.track_widgets[i+1][0])
                self.track_widgets[i], self.track_widgets[i+1] = self.track_widgets[i+1], self.track_widgets[i]
        for idx, (row, var, up_btn, down_btn) in enumerate(self.track_widgets):
            up_btn.configure(command=lambda i=idx: move_row(i, 'up'))
            down_btn.configure(command=lambda i=idx: move_row(i, 'down'))
        # Confirm/cancel buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color=PALETTE['bg'])
        btn_frame.pack(fill="x", pady=10)
        def confirm():
            # Get selected and arranged tracks
            new_queue = []
            for row, var, up_btn, down_btn in self.track_widgets:
                if var.get():
                    idx = self.track_widgets.index((row, var, up_btn, down_btn))
                    new_queue.append(tracks[idx])
            self.queue = new_queue
            self.queue_index = 0
            if self.queue:
                self._load_track(self.queue[0])
            dialog.destroy()
        set_btn = ctk.CTkButton(btn_frame, text="Set Queue", fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'], font=("Segoe UI", 16, "bold"), corner_radius=18, command=confirm)
        set_btn.pack(side="right", padx=12)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", fg_color=PALETTE['card'], hover_color=PALETTE['border'], font=("Segoe UI", 16), corner_radius=18, command=dialog.destroy)
        cancel_btn.pack(side="right", padx=12)

    def _load_track(self, track):
        file_path, title, artist, cover_img = track
        self.current_file = file_path
        self.current_title = title
        self.current_artist = artist
        self.current_cover = cover_img
        # Update player bar widgets
        if cover_img:
            self.cover_label.configure(image=cover_img, text="")
        else:
            self.cover_label.configure(image=None, text="🎵")
        self.song_title.configure(text=title)
        self.song_artist.configure(text=artist)
        self.play_btn.configure(text="⏸")
        # After loading and playing:
        from mutagen import File as MutagenFile
        try:
            audio = MutagenFile(file_path)
            self._current_duration = int(audio.info.length)
        except Exception:
            self._current_duration = 0
        # Set volume slider to current mixer volume
        current_vol = int(pygame.mixer.music.get_volume() * 100)
        self.volume_slider.set(current_vol)
        self._update_progress()

    def _toggle_play(self):
        if hasattr(self, 'is_playing') and self.is_playing:
            self.pause_audio()
        elif self.current_file:
            if pygame.mixer.music.get_busy():
                self.resume_audio()
            else:
                self.play_audio(self.current_file)

    def _prev_track(self):
        if self.queue and self.queue_index > 0:
            self.queue_index -= 1
            self._load_track(self.queue[self.queue_index])
            self.play_audio(self.queue[self.queue_index][0])

    def _next_track(self):
        if self.queue and self.queue_index < len(self.queue)-1:
            self.queue_index += 1
            self._load_track(self.queue[self.queue_index])
            self.play_audio(self.queue[self.queue_index][0])

    def _set_volume(self, value):
        # Set pygame mixer volume (0.0 to 1.0)
        pygame.mixer.music.set_volume(float(value) / 100)

    def _update_progress(self):
        if self.current_file and pygame.mixer.music.get_busy() and not self._seek_dragging:
            pos_ms = pygame.mixer.music.get_pos()
            pos_sec = max(0, pos_ms // 1000)
            duration = getattr(self, '_current_duration', 0)
            if duration > 0:
                self.seek_bar.set(pos_sec / duration)
                self.elapsed_label.configure(text=f"{pos_sec//60}:{pos_sec%60:02d}")
                self.duration_label.configure(text=f"{duration//60}:{duration%60:02d}")
        self.after(200, self._update_progress)

    def play_audio(self, file_path):
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.is_playing = True
            self.play_btn.configure(text="⏸")
            # After loading and playing:
            from mutagen import File as MutagenFile
            try:
                audio = MutagenFile(file_path)
                self._current_duration = int(audio.info.length)
            except Exception:
                self._current_duration = 0
            self._update_progress()
        except Exception as e:
            self.controller.show_toast(f"Playback error: {e}", success=False)
            self.is_playing = False
            self.play_btn.configure(text="▶")

    def pause_audio(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_btn.configure(text="▶")

    def resume_audio(self):
        pygame.mixer.music.unpause()
        self.is_playing = True
        self.play_btn.configure(text="⏸")

    def stop_audio(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.play_btn.configure(text="▶")

    def add_to_queue_and_play(self, file_path):
        # Set queue to just this file and play it
        ext = os.path.splitext(file_path)[1].lower()
        title, artist, cover_img = os.path.basename(file_path), '', None
        try:
            if ext == '.mp3':
                audio = MP3(file_path, ID3=ID3)
                title = audio.tags.get('TIT2', title)
                artist = audio.tags.get('TPE1', artist)
                if isinstance(title, TIT2):
                    title = title.text[0]
                if isinstance(artist, TPE1):
                    artist = artist.text[0]
                if 'APIC:' in audio.tags:
                    apic = audio.tags['APIC:']
                    from io import BytesIO
                    from PIL import Image
                    img = Image.open(BytesIO(apic.data)).resize((110, 110))
                    cover_img = ctk.CTkImage(light_image=img, size=(110, 110))
            elif ext == '.flac':
                audio = FLAC(file_path)
                title = audio.get('title', [title])[0]
                artist = audio.get('artist', [artist])[0]
                if audio.pictures:
                    from PIL import Image
                    from io import BytesIO
                    img = Image.open(BytesIO(audio.pictures[0].data)).resize((110, 110))
                    cover_img = ctk.CTkImage(light_image=img, size=(110, 110))
            elif ext in ('.m4a', '.mp4'):
                audio = MP4(file_path)
                title = audio.tags.get('\u0000nam', [title])[0]
                artist = audio.tags.get('\u0000ART', [artist])[0]
                if 'covr' in audio:
                    from PIL import Image
                    from io import BytesIO
                    img = Image.open(BytesIO(audio['covr'][0])).resize((110, 110))
                    cover_img = ctk.CTkImage(light_image=img, size=(110, 110))
            elif ext == '.opus':
                audio = OggVorbis(file_path)
                title = audio.get('title', [title])[0]
                artist = audio.get('artist', [artist])[0]
        except Exception:
            pass
        self.queue = [(file_path, title, artist, cover_img)]
        self.queue_index = 0
        self._load_track(self.queue[0])
        self.play_audio(file_path)

    def _on_seek_click(self, event):
        self._seek_dragging = True
        self.seek_bar.configure(progress_color="#1ed760")  # Lighter accent while dragging
        self._show_seek_time_label(event)
        self._seek_to_event(event)
    def _on_seek_drag(self, event):
        self._show_seek_time_label(event)
        self._seek_to_event(event)
    def _on_seek_release(self, event):
        self.seek_bar.configure(progress_color=PALETTE['accent'])
        self._seek_time_label.place_forget()
        self._seek_to_event(event, do_seek=True)
        self._seek_dragging = False
    def _show_seek_time_label(self, event):
        bar = self.seek_bar
        x = event.x
        width = bar.winfo_width()
        rel = min(max(x / width, 0), 1)
        duration = getattr(self, '_current_duration', 0)
        seek_sec = int(rel * duration)
        label_text = f"{seek_sec//60}:{seek_sec%60:02d}"
        self._seek_time_label.configure(text=label_text)
        # Place label above the bar at the mouse x position
        bar_x = bar.winfo_rootx() - self.center_panel.winfo_rootx()
        self._seek_time_label.place(x=bar_x + x - 20, y=bar.winfo_y() - 28)
    def _seek_to_event(self, event, do_seek=False):
        bar = self.seek_bar
        x = event.x
        width = bar.winfo_width()
        rel = min(max(x / width, 0), 1)
        bar.set(rel)
        if do_seek and self.current_file and hasattr(self, '_current_duration'):
            seek_sec = int(rel * self._current_duration)
            pygame.mixer.music.play(start=seek_sec)
            self.is_playing = True
            self.play_btn.configure(text="⏸")

class ConvertPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=PALETTE['bg'])
        self.controller = controller
        center_frame = ctk.CTkFrame(self, fg_color=PALETTE['bg'])
        center_frame.pack(expand=True, fill='both')
        self.header = ctk.CTkLabel(center_frame, text="Convert Audio Files", font=("Segoe UI", 32, "bold"), text_color=PALETTE['accent'])
        self.header.pack(pady=(30, 10), anchor='center')
        self.file_list = []
        self.file_label = ctk.CTkLabel(center_frame, text="No files selected", font=("Segoe UI", 14), text_color=PALETTE['text'])
        self.file_label.pack(pady=10, anchor='center')
        self.select_btn = ctk.CTkButton(center_frame, text="Select Files", fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'], font=("Segoe UI", 16, "bold"), corner_radius=20, width=180, height=40, command=self.select_files)
        self.select_btn.pack(pady=(0, 10), anchor='center')
        self.format_var = ctk.StringVar(value=AUDIO_FORMATS[0])
        self.format_menu = ctk.CTkOptionMenu(center_frame, values=AUDIO_FORMATS, variable=self.format_var, width=180, font=("Segoe UI", 14))
        self.format_menu.pack(pady=8)
        self.convert_btn = ctk.CTkButton(center_frame, text="Convert", fg_color=PALETTE['accent'], hover_color=PALETTE['accent_hover'], font=("Segoe UI", 18, "bold"), corner_radius=30, width=220, height=50, command=self.convert_files)
        self.convert_btn.pack(pady=20, anchor='center')
        self.progress_bar = ctk.CTkProgressBar(center_frame, width=500, height=20, corner_radius=10, progress_color=PALETTE['accent'])
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(10, 0), anchor='center')
        self.status_label = ctk.CTkLabel(center_frame, text="", font=("Segoe UI", 16), text_color=PALETTE['text'])
        self.status_label.pack(pady=(10, 0), anchor='center')
        self.center_frame = center_frame

    def select_files(self):
        import tkinter.filedialog
        files = tkinter.filedialog.askopenfilenames(title="Select audio files", filetypes=[("Audio Files", "*.mp3 *.m4a *.flac *.wav *.opus *.ogg *.aac")])
        if files:
            self.file_list = list(files)
            self.file_label.configure(text=f"{len(self.file_list)} file(s) selected")
        else:
            self.file_list = []
            self.file_label.configure(text="No files selected")

    def convert_files(self):
        import subprocess
        if not self.file_list:
            self.status_label.configure(text="No files selected!")
            return
        fmt = self.format_var.get()
        total = len(self.file_list)
        self.progress_bar.set(0)
        self.status_label.configure(text="Starting conversion...")
        self.update_idletasks()
        def do_convert():
            completed = 0
            for file in self.file_list:
                out_dir = self.controller.download_dir
                base = os.path.splitext(os.path.basename(file))[0]
                out_file = os.path.join(out_dir, f"{base}.{fmt}")
                try:
                    subprocess.run(["ffmpeg", "-y", "-i", file, out_file], check=True)
                    completed += 1
                    self.progress_bar.set(completed/total)
                    self.status_label.configure(text=f"Converted {completed}/{total}")
                except Exception as e:
                    self.status_label.configure(text=f"Error: {e}")
                self.update_idletasks()
            self.status_label.configure(text="All conversions finished!")
            self.file_label.configure(text="No files selected")
            self.file_list = []
        import threading
        threading.Thread(target=do_convert, daemon=True).start()

if __name__ == "__main__":
    app = MusicDLApp()
    app.mainloop() 