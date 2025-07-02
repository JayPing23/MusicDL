import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
from threading import Thread
from downloader.youtube_downloader import download_youtube
from downloader.spotify_downloader import download_spotify
import os
import re

# Modern color palettes
LIGHT_THEME = {
    'bg': '#f0f4f8',
    'fg': '#222f3e',
    'accent': '#5f27cd',
    'header_bg': '#341f97',
    'header_fg': '#f5f6fa',
    'card_bg': '#ffffff',
    'card_border': '#d1d8e0',
    'button_bg': '#5f27cd',
    'button_fg': '#ffffff',
    'button_hover': '#341f97',
    'entry_bg': '#f1f2f6',
    'entry_fg': '#222f3e',
}
DARK_THEME = {
    'bg': '#23272e',
    'fg': '#f5f6fa',
    'accent': '#18dcff',
    'header_bg': '#1e272e',
    'header_fg': '#18dcff',
    'card_bg': '#2d3436',
    'card_border': '#393e46',
    'button_bg': '#18dcff',
    'button_fg': '#23272e',
    'button_hover': '#00b8d4',
    'entry_bg': '#353b48',
    'entry_fg': '#f5f6fa',
}

class ModernButton(tk.Button):
    def __init__(self, *args, **kwargs):
        self.normal_bg = kwargs.pop('bg', '#5f27cd')
        self.hover_bg = kwargs.pop('hover_bg', '#341f97')
        super().__init__(*args, **kwargs)
        self.configure(bg=self.normal_bg, activebackground=self.hover_bg, relief='flat', bd=0, cursor='hand2')
        self.bind('<Enter>', lambda e: self.config(bg=self.hover_bg))
        self.bind('<Leave>', lambda e: self.config(bg=self.normal_bg))

class MusicDLApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('MusicDL - GUI Edition')
        self.geometry('900x750')
        self.minsize(650, 500)
        self.resizable(True, True)
        self.theme = 'light'
        self.colors = LIGHT_THEME.copy()
        self.download_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'downloads'))
        self.configure(bg=self.colors['bg'])
        self.style = ttk.Style(self)
        self.set_theme(self.theme)
        self.create_widgets()
        self.status_lines = {}  # Map from file key to line index in status area

    def set_theme(self, theme):
        self.theme = theme
        self.colors = LIGHT_THEME.copy() if theme == 'light' else DARK_THEME.copy()
        self.configure(bg=self.colors['bg'])
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=self.colors['bg'])
        self.style.configure('Card.TFrame', background=self.colors['card_bg'], relief='flat', borderwidth=0)
        self.style.configure('Header.TLabel', background=self.colors['header_bg'], foreground=self.colors['header_fg'], font=('Segoe UI', 26, 'bold'))
        self.style.configure('TLabel', background=self.colors['card_bg'], foreground=self.colors['fg'], font=('Segoe UI', 12))
        self.style.configure('TButton', background=self.colors['button_bg'], foreground=self.colors['button_fg'], font=('Segoe UI', 12, 'bold'))
        self.style.map('TButton', background=[('active', self.colors['accent'])])
        self.style.configure('TRadiobutton', background=self.colors['card_bg'], foreground=self.colors['fg'], font=('Segoe UI', 12))
        self.style.configure('TEntry', fieldbackground=self.colors['entry_bg'], foreground=self.colors['entry_fg'])
        self.style.configure('TProgressbar', background=self.colors['accent'], troughcolor=self.colors['entry_bg'])

    def toggle_theme(self):
        self.set_theme('dark' if self.theme == 'light' else 'light')
        self.update_colors()

    def update_colors(self):
        self.configure(bg=self.colors['bg'])
        self.header_frame.configure(bg=self.colors['header_bg'])
        self.header_label.configure(bg=self.colors['header_bg'], fg=self.colors['header_fg'])
        self.card_frame.configure(bg=self.colors['card_bg'])
        self.link_label.configure(bg=self.colors['card_bg'], fg=self.colors['fg'])
        self.status_label.configure(bg=self.colors['card_bg'], fg=self.colors['fg'])
        self.progress_label.configure(bg=self.colors['card_bg'], fg=self.colors['fg'])
        self.link_text.configure(bg=self.colors['entry_bg'], fg=self.colors['entry_fg'], insertbackground=self.colors['fg'])
        self.status_area.configure(bg=self.colors['entry_bg'], fg=self.colors['entry_fg'], insertbackground=self.colors['fg'])
        self.theme_btn.configure(bg=self.colors['button_bg'], fg=self.colors['button_fg'], activebackground=self.colors['accent'])
        self.load_btn.configure(bg=self.colors['button_bg'], fg=self.colors['button_fg'], activebackground=self.colors['accent'])
        self.download_btn.configure(bg=self.colors['button_bg'], fg=self.colors['button_fg'], activebackground=self.colors['accent'])

    def create_widgets(self):
        # Header with gradient effect
        self.header_frame = tk.Canvas(self, height=70, bg=self.colors['header_bg'], highlightthickness=0)
        self.header_frame.pack(fill='x')
        self.header_frame.create_rectangle(0, 0, 900, 70, fill=self.colors['header_bg'], outline='')
        self.header_label = tk.Label(self.header_frame, text='🎵 MusicDL', font=('Segoe UI', 28, 'bold'), bg=self.colors['header_bg'], fg=self.colors['header_fg'], pady=20)
        self.header_label.place(x=30, y=10)
        self.theme_btn = ModernButton(self.header_frame, text='🌙' if self.theme == 'light' else '☀️', command=self.toggle_theme, bg=self.colors['button_bg'], hover_bg=self.colors['button_hover'], fg=self.colors['button_fg'], font=('Segoe UI', 14, 'bold'))
        self.theme_btn.place(x=830, y=18)

        # Card-like main frame with rounded corners and shadow
        self.card_frame = tk.Frame(self, bg=self.colors['card_bg'], bd=0, highlightthickness=0)
        self.card_frame.pack(padx=40, pady=40, fill='both', expand=True)
        self.card_frame.grid_propagate(False)
        self.card_frame.update_idletasks()
        self.card_frame.config(highlightbackground=self.colors['card_border'], highlightcolor=self.colors['card_border'], highlightthickness=2)

        # Download folder selection
        folder_frame = tk.Frame(self.card_frame, bg=self.colors['card_bg'])
        folder_frame.pack(anchor='w', padx=24, pady=(18, 0))
        tk.Label(folder_frame, text='Download folder:', bg=self.colors['card_bg'], fg=self.colors['fg'], font=('Segoe UI', 11, 'bold')).pack(side='left')
        self.folder_path_var = tk.StringVar(value=self.download_dir)
        self.folder_path_label = tk.Label(folder_frame, textvariable=self.folder_path_var, bg=self.colors['card_bg'], fg=self.colors['accent'], font=('Segoe UI', 11, 'italic'))
        self.folder_path_label.pack(side='left', padx=(8, 0))
        self.folder_btn = ModernButton(folder_frame, text='📁 Browse', command=self.choose_folder, bg=self.colors['button_bg'], hover_bg=self.colors['button_hover'], fg=self.colors['button_fg'], font=('Segoe UI', 10, 'bold'))
        self.folder_btn.pack(side='left', padx=8)

        # Link input
        self.link_label = tk.Label(self.card_frame, text='Paste YouTube/Spotify links (one per line):', bg=self.colors['card_bg'], fg=self.colors['fg'], font=('Segoe UI', 12, 'bold'))
        self.link_label.pack(anchor='w', padx=24, pady=(22,0))
        self.link_text = scrolledtext.ScrolledText(self.card_frame, height=6, font=('Segoe UI', 11), bg=self.colors['entry_bg'], fg=self.colors['entry_fg'], insertbackground=self.colors['fg'], bd=1, relief='solid', wrap='word')
        self.link_text.pack(padx=24, pady=6, fill='both', expand=True)
        self.link_text.bind('<Control-v>', lambda e: (self.paste_links(), 'break'))

        # Load from file
        self.load_btn = ModernButton(self.card_frame, text='📄 Load from .txt', command=self.load_links_from_file, bg=self.colors['button_bg'], hover_bg=self.colors['button_hover'], fg=self.colors['button_fg'], font=('Segoe UI', 10, 'bold'))
        self.load_btn.pack(anchor='w', padx=24, pady=(0,12))

        # Download mode
        self.mode = tk.StringVar(value='audio')
        mode_frame = tk.Frame(self.card_frame, bg=self.colors['card_bg'])
        tk.Label(mode_frame, text='Download mode:', bg=self.colors['card_bg'], fg=self.colors['fg'], font=('Segoe UI', 12, 'bold')).pack(side='left')
        ttk.Radiobutton(mode_frame, text='Audio (MP3 320kbps)', variable=self.mode, value='audio', style='TRadiobutton').pack(side='left', padx=10)
        ttk.Radiobutton(mode_frame, text='Full Video', variable=self.mode, value='video', style='TRadiobutton').pack(side='left', padx=10)
        mode_frame.pack(anchor='w', padx=24, pady=6)

        # Audio format selection
        format_frame = tk.Frame(self.card_frame, bg=self.colors['card_bg'])
        format_frame.pack(anchor='w', padx=24, pady=(0, 12))
        tk.Label(format_frame, text='Audio format:', bg=self.colors['card_bg'], fg=self.colors['fg'], font=('Segoe UI', 11, 'bold')).pack(side='left')
        self.format_var = tk.StringVar(value='mp3')
        format_options = ['mp3', 'opus', 'm4a', 'flac', 'wav', 'original']
        self.format_menu = ttk.Combobox(format_frame, textvariable=self.format_var, values=format_options, state='readonly', width=10, font=('Segoe UI', 11))
        self.format_menu.pack(side='left', padx=8)

        # Download button
        self.download_btn = ModernButton(self.card_frame, text='⬇ Download', command=self.start_download, bg=self.colors['button_bg'], hover_bg=self.colors['button_hover'], fg=self.colors['button_fg'], font=('Segoe UI', 14, 'bold'))
        self.download_btn.pack(pady=12)

        # Status area
        self.status_label = tk.Label(self.card_frame, text='Status:', bg=self.colors['card_bg'], fg=self.colors['fg'], font=('Segoe UI', 12, 'bold'))
        self.status_label.pack(anchor='w', padx=24)
        self.status_area = scrolledtext.ScrolledText(self.card_frame, height=8, font=('Segoe UI', 11), bg=self.colors['entry_bg'], fg=self.colors['entry_fg'], insertbackground=self.colors['fg'], bd=1, relief='solid', wrap='word', state='disabled')
        self.status_area.pack(padx=24, pady=6, fill='both', expand=True)

        # Current file label
        self.current_file_var = tk.StringVar(value='')
        self.current_file_label = tk.Label(self.card_frame, textvariable=self.current_file_var, bg=self.colors['card_bg'], fg=self.colors['accent'], font=('Segoe UI', 13, 'bold'))
        self.current_file_label.pack(anchor='w', padx=24, pady=(5,0))

        # Per-link progress bar (animated)
        self.link_progress_label = tk.Label(self.card_frame, text='Current File Progress:', bg=self.colors['card_bg'], fg=self.colors['fg'], font=('Segoe UI', 11, 'bold'))
        self.link_progress_label.pack(anchor='w', padx=24, pady=(2,0))
        self.link_progress_var = tk.DoubleVar(value=0)
        self.link_progress_bar = ttk.Progressbar(self.card_frame, variable=self.link_progress_var, maximum=100, style='TProgressbar', length=700)
        self.link_progress_bar.pack(padx=24, pady=(0,2), fill='x', expand=False, ipady=6)
        self.link_progress_percent = tk.Label(self.card_frame, text='0%', bg=self.colors['card_bg'], fg=self.colors['accent'], font=('Segoe UI', 11, 'bold'))
        self.link_progress_percent.pack(anchor='w', padx=24, side='left')
        self.link_progress_textbar = tk.Label(self.card_frame, text='[          ]', bg=self.colors['card_bg'], fg=self.colors['accent'], font=('Consolas', 11, 'bold'))
        self.link_progress_textbar.pack(anchor='w', padx=120, side='left')

        # Overall progress bar (animated)
        self.progress_label = tk.Label(self.card_frame, text='Batch Progress:', bg=self.colors['card_bg'], fg=self.colors['fg'], font=('Segoe UI', 12, 'bold'))
        self.progress_label.pack(anchor='w', padx=24, pady=(10,0))
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.card_frame, variable=self.progress_var, maximum=100, style='TProgressbar', length=700)
        self.progress_bar.pack(padx=24, pady=(0,2), fill='x', expand=False, ipady=6)
        self.progress_percent = tk.Label(self.card_frame, text='0%', bg=self.colors['card_bg'], fg=self.colors['accent'], font=('Segoe UI', 11, 'bold'))
        self.progress_percent.pack(anchor='w', padx=24, side='left')
        self.progress_textbar = tk.Label(self.card_frame, text='[          ]', bg=self.colors['card_bg'], fg=self.colors['accent'], font=('Consolas', 11, 'bold'))
        self.progress_textbar.pack(anchor='w', padx=120, side='left')

    def load_links_from_file(self):
        file_path = filedialog.askopenfilename(filetypes=[('Text Files', '*.txt')])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                links = f.read().strip().splitlines()
            bulleted = '\n'.join(f'• {l.strip()}' for l in links if l.strip())
            self.link_text.insert('1.0', bulleted + '\n')

    def paste_links(self):
        try:
            clipboard = self.clipboard_get()
            links = clipboard.strip().splitlines()
            bulleted = '\n'.join(f'• {l.strip()}' for l in links if l.strip())
            self.link_text.insert('insert', bulleted + '\n')
        except Exception:
            pass

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_dir, title='Select Download Folder')
        if folder:
            self.download_dir = folder
            self.folder_path_var.set(folder)

    def start_download(self):
        # Remove bullets before processing
        links = self.link_text.get('1.0', 'end').strip().split('\n')
        links = [l.lstrip('•').strip() for l in links if l.strip()]
        if not links:
            messagebox.showerror('Error', 'Please enter at least one link.')
            return
        mode = self.mode.get()
        audio_format = self.format_var.get()
        self.download_btn.config(state='disabled')
        Thread(target=self.download_links, args=(links, mode, self.download_dir, audio_format), daemon=True).start()

    def normalize_filename(self, artist, title):
        # Remove non-alphanumeric, lower, and ignore anything in parentheses
        base = f"{artist} - {title}"
        base = re.sub(r'\([^)]*\)', '', base)  # Remove anything in parentheses
        base = re.sub(r'[^a-zA-Z0-9]+', '', base).lower()
        return base

    def file_exists(self, artist, title, audio_format):
        norm = self.normalize_filename(artist, title)
        for file in os.listdir(self.download_dir):
            if file.lower().endswith('.' + audio_format):
                name = os.path.splitext(file)[0]
                name = re.sub(r'\([^)]*\)', '', name)  # Remove anything in parentheses
                name = re.sub(r'[^a-zA-Z0-9]+', '', name).lower()
                if name == norm:
                    return True
        return False

    def download_links(self, links, mode, download_dir, audio_format):
        self.set_status('Starting downloads...')
        total = len(links)
        self.clear_complete_label()
        for idx, link in enumerate(links, 1):
            self.set_progress((idx-1)/total*100)
            self.set_link_progress(0)
            artist, title = None, None
            # Try to extract artist/title for duplicate check (Spotify links handled in downloader, YouTube from link text)
            if 'spotify.com' in link:
                # Will be handled in downloader, so skip here
                pass
            elif 'youtube.com' in link or 'youtu.be' in link:
                # Try to parse title from link (not always possible)
                # Optionally, could use yt-dlp to get metadata before download
                pass
            self.set_current_file(f"{os.path.basename(link) if 'youtube.com' in link or 'youtu.be' in link else link}")
            # For Spotify, pass a callback to skip duplicates in the downloader
            try:
                if 'youtube.com' in link or 'youtu.be' in link:
                    # For YouTube, skip duplicate check unless you want to fetch metadata first
                    result = download_youtube(link, mode, self.make_progress_callback(), download_dir, audio_format)
                elif 'spotify.com' in link:
                    result = download_spotify(link, mode, self.make_progress_callback_with_duplicate_check(audio_format), download_dir, audio_format)
                else:
                    self.log_status(f'Invalid link: {link}')
                    continue
                if result:
                    self.log_status(f'Success: {link}')
                else:
                    self.log_status(f'Failed: {link}')
            except Exception as e:
                self.log_status(f'Error with {link}: {e}')
            self.set_link_progress(100)
        self.set_progress(100)
        self.set_link_progress(0)
        self.set_current_file('')
        self.set_status('All downloads finished.')
        self.show_complete_label()
        self.download_btn.config(state='normal')
        self.status_area.see('end')
        self.bell()
        self.show_popup_complete()

    def show_complete_label(self):
        if not hasattr(self, 'complete_label'):
            self.complete_label = tk.Label(self.card_frame, text='✔ Downloads Complete!', bg=self.colors['card_bg'], fg='#27ae60', font=('Segoe UI', 14, 'bold'))
            self.complete_label.pack(pady=(0, 10))
        else:
            self.complete_label.config(text='✔ Downloads Complete!')
            self.complete_label.pack(pady=(0, 10))
        self.status_area.see('end')
        self.bell()  # Play a sound

    def clear_complete_label(self):
        if hasattr(self, 'complete_label'):
            self.complete_label.pack_forget()

    def make_progress_callback(self):
        def callback(msg):
            if isinstance(msg, dict):
                if msg.get('status') == 'downloading':
                    percent = msg.get('downloaded_bytes', 0) / max(msg.get('total_bytes', 1), 1) * 100 if msg.get('total_bytes') else 0
                    self.set_link_progress(percent)
            elif isinstance(msg, str):
                self.log_status(msg)
        return callback

    def make_progress_callback_with_duplicate_check(self, audio_format):
        def callback(msg):
            # msg can be dict (progress) or tuple ("check_duplicate", artist, title)
            if isinstance(msg, tuple) and msg[0] == 'check_duplicate':
                artist, title = msg[1], msg[2]
                if self.file_exists(artist, title, audio_format):
                    self.log_status(f"Skipped (already exists): {artist} - {title}")
                    return True  # Signal to skip
                return False
            return self.make_progress_callback()(msg)
        return callback

    def set_link_progress(self, percent):
        self.link_progress_var.set(percent)
        self.link_progress_percent.config(text=f'{int(percent)}%')
        self.link_progress_textbar.config(text=self.make_text_bar(percent))
        if percent == 0:
            self.link_progress_bar.config(mode='indeterminate')
            self.link_progress_bar.start(10)
        elif percent >= 100:
            self.link_progress_bar.stop()
            self.link_progress_bar.config(mode='determinate')
        else:
            self.link_progress_bar.config(mode='determinate')
            self.link_progress_bar.stop()

    def set_status(self, msg):
        # Deprecated: use log_status for all status updates
        pass

    def log_status(self, msg):
        # Only show high-level status: downloading, success, skipped, or error
        keywords = [
            'Downloading:', 'Success:', 'Skipped', 'Failed:', 'Error', 'already exists', 'YouTube search failed', 'yt-dlp error:'
        ]
        if not any(k in msg for k in keywords):
            return
        # Extract a file key (artist-title or link) from the message
        file_key = None
        for k in ['Downloading:', 'Success:', 'Skipped', 'Failed:', 'Error', 'already exists', 'YouTube search failed', 'yt-dlp error:']:
            if msg.startswith(k):
                file_key = msg[len(k):].strip()
                break
        if not file_key:
            file_key = msg
        # Update or add the line for this file
        self.status_area.config(state='normal')
        lines = self.status_area.get('1.0', 'end').splitlines()
        if file_key in self.status_lines:
            idx = self.status_lines[file_key]
            lines[idx] = msg
        else:
            idx = len(lines)
            lines.append(msg)
            self.status_lines[file_key] = idx
        # Rewrite the status area
        self.status_area.delete('1.0', 'end')
        self.status_area.insert('1.0', '\n'.join(lines) + '\n')
        self.status_area.see('end')
        self.status_area.config(state='disabled')

    def set_progress(self, percent):
        self.progress_var.set(percent)
        self.progress_percent.config(text=f'{int(percent)}%')
        self.progress_textbar.config(text=self.make_text_bar(percent))
        if percent == 0:
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
        elif percent >= 100:
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
        else:
            self.progress_bar.config(mode='determinate')
            self.progress_bar.stop()

    def set_current_file(self, filename):
        self.current_file_var.set(f"Now downloading: {filename}" if filename else "")

    def show_popup_complete(self):
        messagebox.showinfo('MusicDL', '✔ All downloads are complete!')

    def make_text_bar(self, percent, width=10):
        filled = int(width * percent // 100)
        return '[' + '█' * filled + ' ' * (width - filled) + f'] {int(percent)}%'

if __name__ == '__main__':
    app = MusicDLApp()
    app.mainloop() 