# The file will be explicitly rewritten to center all sidebar and main page content as described in the instructions above. All layout will use customtkinter and be visually balanced and modern.

import customtkinter as ctk
import os
from PIL import Image, ImageTk, ImageDraw
import threading
import tkinter as tk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_ACCENT = "#1DB954"  # Spotify green for accent

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
        for F in (LandingPage, DownloadPage, HistoryPage, SettingsPage, AboutPage, PlayerPage):
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

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, show_frame):
        super().__init__(parent, width=80, fg_color="#232946")
        self.show_frame = show_frame
        self.expanded = False
        self.expanded_width = 220
        self.collapsed_width = 80
        self.current_width = self.collapsed_width
        self.configure(width=self.current_width)
        # Container for vertical centering
        self.container = ctk.CTkFrame(self, fg_color="#232946")
        self.container.pack(expand=True, fill="y")
        self.toggle_btn = ctk.CTkButton(self.container, text="☰", width=60, height=60, fg_color="#232946", hover_color=APP_ACCENT, corner_radius=30, command=self.toggle_sidebar, font=("Segoe UI", 22, "bold"))
        self.toggle_btn.pack(pady=(18, 10))
        self.logo = ctk.CTkLabel(self.container, text="🎵", font=("Segoe UI", 32, "bold"), text_color=APP_ACCENT)
        self.logo.pack(pady=(0, 10))
        self.buttons = []
        self.button_labels = []
        nav = [
            ("Home", "LandingPage", "🏠"),
            ("Download", "DownloadPage", "⬇️"),
            ("Player", "PlayerPage", "🎧"),
            ("History", "HistoryPage", "🕑"),
            ("Settings", "SettingsPage", "⚙️"),
            ("About", "AboutPage", "ℹ️"),
        ]
        for text, page, icon in nav:
            btn_frame = ctk.CTkFrame(self.container, fg_color="#232946")
            btn_frame.pack(fill="x", pady=2)
            btn = ctk.CTkButton(btn_frame, text=icon, width=60, height=60, fg_color="#232946", hover_color=APP_ACCENT, corner_radius=30, command=lambda p=page: show_frame(p), font=("Segoe UI", 22, "bold"))
            btn.pack(side="left", padx=(10,0))
            lbl = ctk.CTkLabel(btn_frame, text=text, font=("Segoe UI", 16, "bold"), text_color="#fff")
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

class LandingPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb")
        center_frame = ctk.CTkFrame(self, fg_color="#f4f6fb")
        center_frame.pack(expand=True, fill='both')
        self.icon = ctk.CTkLabel(center_frame, text="▶️", font=("Segoe UI", 120, "bold"), text_color=APP_ACCENT)
        self.icon.pack(pady=(0, 20), anchor='center')
        self.title = ctk.CTkLabel(center_frame, text="MUSICDL", font=("Segoe UI", 44, "bold"), text_color="#232946")
        self.title.pack(pady=(0, 10), anchor='center')
        self.subtitle = ctk.CTkLabel(center_frame, text="Your Creative Music Downloader", font=("Segoe UI", 20), text_color="#232946")
        self.subtitle.pack(pady=(0, 40), anchor='center')
        self.start_btn = ctk.CTkButton(center_frame, text="Start Downloading", fg_color=APP_ACCENT, hover_color="#1ed760", font=("Segoe UI", 22, "bold"), corner_radius=30, width=260, height=60, command=lambda: controller.show_frame("DownloadPage"))
        self.start_btn.pack(anchor='center')
        self.info = ctk.CTkLabel(center_frame, text="Paste links, download, and manage your music with style!", font=("Segoe UI", 16), text_color="#232946")
        self.info.pack(pady=(40, 0), anchor='center')

class DownloadPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb")
        self.controller = controller
        self.header = ctk.CTkLabel(self, text="Download Music", font=("Segoe UI", 32, "bold"), text_color=APP_ACCENT)
        self.header.pack(pady=(30, 10))
        self.link_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube/Spotify link here...", width=500, height=40, font=("Segoe UI", 16))
        self.link_entry.pack(pady=10)
        self.add_btn = ctk.CTkButton(self, text="Add to Queue", fg_color=APP_ACCENT, hover_color="#1ed760", font=("Segoe UI", 16, "bold"), corner_radius=20, width=180, height=40, command=self.add_to_queue)
        self.add_btn.pack(pady=(0, 10))
        self.queue_frame = ctk.CTkFrame(self, fg_color="#e9ecef", corner_radius=20)
        self.queue_frame.pack(pady=10, padx=40, fill="x")
        self.queue = []
        self.queue_labels = []
        self.download_btn = ctk.CTkButton(self, text="⬇ Download All", fg_color=APP_ACCENT, hover_color="#1ed760", font=("Segoe UI", 18, "bold"), corner_radius=30, width=220, height=50, command=self.download_all)
        self.download_btn.pack(pady=20)
        self.progress_bar = ctk.CTkProgressBar(self, width=500, height=20, corner_radius=10, progress_color=APP_ACCENT)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(10, 0))
        self.status_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 16), text_color="#232946")
        self.status_label.pack(pady=(10, 0))
        self.fab = ctk.CTkButton(self, text="+", fg_color=APP_ACCENT, hover_color="#1ed760", font=("Segoe UI", 32, "bold"), corner_radius=40, width=80, height=80, command=self.show_add_dialog)
        self.fab.place(relx=0.92, rely=0.85)

    def add_to_queue(self):
        link = self.link_entry.get().strip()
        if link:
            self.queue.append(link)
            lbl = ctk.CTkLabel(self.queue_frame, text=link, font=("Segoe UI", 14), text_color="#232946", anchor="w")
            lbl.pack(fill="x", padx=10, pady=4)
            self.queue_labels.append(lbl)
            self.link_entry.delete(0, "end")
            self.controller.show_toast("Added to queue!", success=True)

    def download_all(self):
        if not self.queue:
            self.controller.show_toast("Queue is empty!", success=False)
            return
        self.status_label.configure(text="Downloading...")
        self.progress_bar.set(0)
        self.update_idletasks()
        # Simulate download with animation
        import threading, time
        def animate():
            for i in range(1, 101):
                time.sleep(0.03)
                self.progress_bar.set(i/100)
            self.status_label.configure(text="Download complete!")
            self.controller.show_toast("All downloads finished!", success=True)
            self.queue.clear()
            for lbl in self.queue_labels:
                lbl.destroy()
            self.queue_labels.clear()
        threading.Thread(target=animate, daemon=True).start()

    def show_add_dialog(self):
        # Floating action button: show a dialog to add a link
        import tkinter.simpledialog
        link = tkinter.simpledialog.askstring("Add Link", "Paste YouTube/Spotify link:")
        if link:
            self.link_entry.delete(0, "end")
            self.link_entry.insert(0, link)
            self.add_to_queue()

class HistoryPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb")
        self.controller = controller
        self.header = ctk.CTkLabel(self, text="Download History", font=("Segoe UI", 32, "bold"), text_color=APP_ACCENT)
        self.header.pack(pady=(30, 10))
        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search downloads...", width=400, height=36, font=("Segoe UI", 14))
        self.search_entry.pack(pady=10)
        self.list_frame = ctk.CTkFrame(self, fg_color="#e9ecef", corner_radius=20)
        self.list_frame.pack(pady=10, padx=40, fill="both", expand=True)
        self.populate_history()

    def populate_history(self):
        # For demo, show placeholder items
        for i in range(8):
            row = ctk.CTkFrame(self.list_frame, fg_color="#fff", corner_radius=12)
            row.pack(fill="x", padx=10, pady=6)
            icon = ctk.CTkLabel(row, text="🎵", font=("Segoe UI", 24))
            icon.pack(side="left", padx=10)
            title = ctk.CTkLabel(row, text=f"Song {i+1}", font=("Segoe UI", 16, "bold"), text_color="#232946")
            title.pack(side="left", padx=(0, 10))
            artist = ctk.CTkLabel(row, text=f"Artist {i+1}", font=("Segoe UI", 14), text_color="#232946")
            artist.pack(side="left")
            play_btn = ctk.CTkButton(row, text="▶", width=36, height=36, fg_color=APP_ACCENT, corner_radius=18, font=("Segoe UI", 16), command=lambda: None)
            play_btn.pack(side="right", padx=6)
            open_btn = ctk.CTkButton(row, text="📂", width=36, height=36, fg_color="#e9ecef", corner_radius=18, font=("Segoe UI", 16), command=lambda: None)
            open_btn.pack(side="right", padx=6)
            del_btn = ctk.CTkButton(row, text="🗑", width=36, height=36, fg_color="#e9ecef", corner_radius=18, font=("Segoe UI", 16), command=lambda: None)
            del_btn.pack(side="right", padx=6)

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb")
        self.controller = controller
        self.header = ctk.CTkLabel(self, text="Settings", font=("Segoe UI", 32, "bold"), text_color=APP_ACCENT)
        self.header.pack(pady=(30, 10))
        self.theme_switch = ctk.CTkSwitch(self, text="Dark Mode", command=self.toggle_theme, font=("Segoe UI", 16))
        self.theme_switch.pack(pady=10)
        self.format_label = ctk.CTkLabel(self, text="Output Format:", font=("Segoe UI", 16), text_color="#232946")
        self.format_label.pack(pady=(20, 0))
        self.format_menu = ctk.CTkOptionMenu(self, values=["mp3", "opus", "m4a", "flac", "wav", "original"], width=180, font=("Segoe UI", 14))
        self.format_menu.pack(pady=8)
        self.folder_label = ctk.CTkLabel(self, text="Download Folder:", font=("Segoe UI", 16), text_color="#232946")
        self.folder_label.pack(pady=(20, 0))
        self.folder_btn = ctk.CTkButton(self, text="Choose Folder", fg_color=APP_ACCENT, hover_color="#1ed760", font=("Segoe UI", 14), corner_radius=18, command=self.choose_folder)
        self.folder_btn.pack(pady=8)
        self.folder_path = ctk.CTkLabel(self, text=self.controller.download_dir, font=("Segoe UI", 12), text_color="#232946")
        self.folder_path.pack(pady=(0, 10))

    def toggle_theme(self):
        mode = "dark" if ctk.get_appearance_mode() == "Light" else "light"
        ctk.set_appearance_mode(mode)

    def choose_folder(self):
        import tkinter.filedialog
        folder = tkinter.filedialog.askdirectory()
        if folder:
            self.controller.download_dir = folder
            self.folder_path.configure(text=folder)
            self.controller.show_toast("Download folder updated!", success=True)

class AboutPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb")
        self.controller = controller
        self.header = ctk.CTkLabel(self, text="About MusicDL", font=("Segoe UI", 32, "bold"), text_color=APP_ACCENT)
        self.header.pack(pady=(30, 10))
        self.info = ctk.CTkLabel(self, text="A creative, modern music downloader.\nBuilt with Python and customtkinter.\nInspired by mobile app design.", font=("Segoe UI", 18), text_color="#232946", justify="center")
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
            self.avatar = ctk.CTkLabel(self, image=self.profile_img, text="")
            self.avatar.pack(pady=10)
        except Exception as e:
            self.avatar = ctk.CTkLabel(self, text="👤", font=("Segoe UI", 80))
            self.avatar.pack(pady=10)
        self.credits = ctk.CTkLabel(self, text="Developed by Danielle Aragon", font=("Segoe UI", 14), text_color="#232946")
        self.credits.pack(pady=10)

class PlayerPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb")
        self.controller = controller
        self.header = ctk.CTkLabel(self, text="Music Player", font=("Segoe UI", 32, "bold"), text_color=APP_ACCENT)
        self.header.pack(pady=(30, 10))
        # Cover art
        self.cover_img = ctk.CTkLabel(self, text="🎵", font=("Segoe UI", 120))
        self.cover_img.pack(pady=10)
        # Song info
        self.song_title = ctk.CTkLabel(self, text="No song loaded", font=("Segoe UI", 22, "bold"), text_color="#232946")
        self.song_title.pack(pady=(10, 0))
        self.song_artist = ctk.CTkLabel(self, text="", font=("Segoe UI", 16), text_color="#232946")
        self.song_artist.pack(pady=(0, 20))
        # Controls
        controls = ctk.CTkFrame(self, fg_color="#f4f6fb")
        controls.pack(pady=10)
        self.prev_btn = ctk.CTkButton(controls, text="⏮", width=60, height=60, fg_color=APP_ACCENT, corner_radius=30, font=("Segoe UI", 22), command=self.prev_song)
        self.prev_btn.pack(side="left", padx=10)
        self.play_btn = ctk.CTkButton(controls, text="▶", width=80, height=80, fg_color=APP_ACCENT, corner_radius=40, font=("Segoe UI", 28), command=self.toggle_play)
        self.play_btn.pack(side="left", padx=10)
        self.next_btn = ctk.CTkButton(controls, text="⏭", width=60, height=60, fg_color=APP_ACCENT, corner_radius=30, font=("Segoe UI", 22), command=self.next_song)
        self.next_btn.pack(side="left", padx=10)
        # Seek bar
        self.seek_var = ctk.DoubleVar(value=0)
        self.seek_bar = ctk.CTkSlider(self, from_=0, to=100, variable=self.seek_var, width=400, command=self.seek)
        self.seek_bar.pack(pady=10)
        # Volume
        vol_frame = ctk.CTkFrame(self, fg_color="#f4f6fb")
        vol_frame.pack(pady=5)
        ctk.CTkLabel(vol_frame, text="🔊", font=("Segoe UI", 18)).pack(side="left")
        self.vol_var = ctk.DoubleVar(value=1.0)
        self.vol_slider = ctk.CTkSlider(vol_frame, from_=0, to=1, variable=self.vol_var, width=120, command=self.set_volume)
        self.vol_slider.pack(side="left", padx=8)
        # For demo, no real song loaded yet
    def prev_song(self):
        pass
    def next_song(self):
        pass
    def toggle_play(self):
        pass
    def seek(self, value):
        pass
    def set_volume(self, value):
        pass

class Toast(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#232946")
        self.label = ctk.CTkLabel(self, text="", font=("Segoe UI", 16), text_color="#fff")
        self.label.pack(padx=20, pady=10)
        self.place_forget()
        self.after_id = None
    def show(self, message, success=True):
        self.label.configure(text=message, text_color="#fff" if success else "#ff4d4f")
        self.place(relx=0.5, rely=0.05, anchor="n")
        if self.after_id: self.after_cancel(self.after_id)
        self.after_id = self.after(2200, self.place_forget)

if __name__ == "__main__":
    app = MusicDLApp()
    app.mainloop() 