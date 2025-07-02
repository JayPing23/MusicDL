import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
from threading import Thread
from downloader.youtube_downloader import download_youtube
from downloader.spotify_downloader import download_spotify
import os

# Color palettes
LIGHT_THEME = {
    'bg': '#f5f6fa',
    'fg': '#222f3e',
    'accent': '#54a0ff',
    'header_bg': '#222f3e',
    'header_fg': '#f5f6fa',
    'card_bg': '#ffffff',
    'button_bg': '#54a0ff',
    'button_fg': '#ffffff',
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
    'button_bg': '#18dcff',
    'button_fg': '#23272e',
    'entry_bg': '#353b48',
    'entry_fg': '#f5f6fa',
}

class MusicDLApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('MusicDL - GUI Edition')
        self.geometry('650x600')
        self.resizable(False, False)
        self.theme = 'light'
        self.colors = LIGHT_THEME.copy()
        self.configure(bg=self.colors['bg'])
        self.style = ttk.Style(self)
        self.set_theme(self.theme)
        self.create_widgets()

    def set_theme(self, theme):
        self.theme = theme
        self.colors = LIGHT_THEME.copy() if theme == 'light' else DARK_THEME.copy()
        self.configure(bg=self.colors['bg'])
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=self.colors['bg'])
        self.style.configure('Card.TFrame', background=self.colors['card_bg'], relief='raised', borderwidth=1)
        self.style.configure('Header.TLabel', background=self.colors['header_bg'], foreground=self.colors['header_fg'], font=('Segoe UI', 20, 'bold'))
        self.style.configure('TLabel', background=self.colors['card_bg'], foreground=self.colors['fg'], font=('Segoe UI', 11))
        self.style.configure('TButton', background=self.colors['button_bg'], foreground=self.colors['button_fg'], font=('Segoe UI', 11, 'bold'))
        self.style.map('TButton', background=[('active', self.colors['accent'])])
        self.style.configure('TRadiobutton', background=self.colors['card_bg'], foreground=self.colors['fg'], font=('Segoe UI', 11))
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
        # Header
        self.header_frame = tk.Frame(self, bg=self.colors['header_bg'], height=60)
        self.header_frame.pack(fill='x')
        self.header_label = tk.Label(self.header_frame, text='🎵 MusicDL', font=('Segoe UI', 22, 'bold'), bg=self.colors['header_bg'], fg=self.colors['header_fg'], pady=15)
        self.header_label.pack(side='left', padx=20)
        self.theme_btn = tk.Button(self.header_frame, text='🌙' if self.theme == 'light' else '☀️', command=self.toggle_theme, bg=self.colors['button_bg'], fg=self.colors['button_fg'], bd=0, font=('Segoe UI', 12, 'bold'), activebackground=self.colors['accent'])
        self.theme_btn.pack(side='right', padx=20)

        # Card-like main frame
        self.card_frame = tk.Frame(self, bg=self.colors['card_bg'], bd=2, relief='groove')
        self.card_frame.pack(padx=30, pady=30, fill='both', expand=True)

        # Link input
        self.link_label = tk.Label(self.card_frame, text='Paste YouTube/Spotify links (one per line):', bg=self.colors['card_bg'], fg=self.colors['fg'], font=('Segoe UI', 11, 'bold'))
        self.link_label.pack(anchor='w', padx=20, pady=(20,0))
        self.link_text = scrolledtext.ScrolledText(self.card_frame, height=6, width=65, font=('Segoe UI', 10), bg=self.colors['entry_bg'], fg=self.colors['entry_fg'], insertbackground=self.colors['fg'], bd=1, relief='solid', wrap='word')
        self.link_text.pack(padx=20, pady=5)

        # Load from file
        self.load_btn = tk.Button(self.card_frame, text='Load from .txt file', command=self.load_links_from_file, bg=self.colors['button_bg'], fg=self.colors['button_fg'], font=('Segoe UI', 10, 'bold'), bd=0, activebackground=self.colors['accent'])
        self.load_btn.pack(anchor='w', padx=20, pady=(0,10))

        # Download mode
        self.mode = tk.StringVar(value='audio')
        mode_frame = tk.Frame(self.card_frame, bg=self.colors['card_bg'])
        tk.Label(mode_frame, text='Download mode:', bg=self.colors['card_bg'], fg=self.colors['fg'], font=('Segoe UI', 11, 'bold')).pack(side='left')
        ttk.Radiobutton(mode_frame, text='Audio (MP3 320kbps)', variable=self.mode, value='audio', style='TRadiobutton').pack(side='left', padx=10)
        ttk.Radiobutton(mode_frame, text='Full Video', variable=self.mode, value='video', style='TRadiobutton').pack(side='left', padx=10)
        mode_frame.pack(anchor='w', padx=20, pady=5)

        # Download button
        self.download_btn = tk.Button(self.card_frame, text='⬇ Download', command=self.start_download, bg=self.colors['button_bg'], fg=self.colors['button_fg'], font=('Segoe UI', 12, 'bold'), bd=0, activebackground=self.colors['accent'])
        self.download_btn.pack(pady=10)

        # Status area
        self.status_label = tk.Label(self.card_frame, text='Status:', bg=self.colors['card_bg'], fg=self.colors['fg'], font=('Segoe UI', 11, 'bold'))
        self.status_label.pack(anchor='w', padx=20)
        self.status_area = scrolledtext.ScrolledText(self.card_frame, height=8, width=65, font=('Segoe UI', 10), bg=self.colors['entry_bg'], fg=self.colors['entry_fg'], insertbackground=self.colors['fg'], bd=1, relief='solid', wrap='word', state='disabled')
        self.status_area.pack(padx=20, pady=5)

        # Progress bar
        self.progress_label = tk.Label(self.card_frame, text='Progress:', bg=self.colors['card_bg'], fg=self.colors['fg'], font=('Segoe UI', 11, 'bold'))
        self.progress_label.pack(anchor='w', padx=20, pady=(10,0))
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.card_frame, variable=self.progress_var, maximum=100, style='TProgressbar', length=500)
        self.progress_bar.pack(padx=20, pady=(0,20))

    def load_links_from_file(self):
        file_path = filedialog.askopenfilename(filetypes=[('Text Files', '*.txt')])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                links = f.read()
            self.link_text.insert('1.0', links.strip() + '\n')

    def start_download(self):
        links = self.link_text.get('1.0', 'end').strip().split('\n')
        links = [l.strip() for l in links if l.strip()]
        if not links:
            messagebox.showerror('Error', 'Please enter at least one link.')
            return
        mode = self.mode.get()
        Thread(target=self.download_links, args=(links, mode), daemon=True).start()

    def download_links(self, links, mode):
        self.set_status('Starting downloads...')
        total = len(links)
        for idx, link in enumerate(links, 1):
            self.set_progress((idx-1)/total*100)
            try:
                if 'youtube.com' in link or 'youtu.be' in link:
                    result = download_youtube(link, mode, self.log_status)
                elif 'spotify.com' in link:
                    result = download_spotify(link, mode, self.log_status)
                else:
                    self.log_status(f'Invalid link: {link}')
                    continue
                if result:
                    self.log_status(f'Success: {link}')
                else:
                    self.log_status(f'Failed: {link}')
            except Exception as e:
                self.log_status(f'Error with {link}: {e}')
        self.set_progress(100)
        self.set_status('All downloads finished.')

    def set_status(self, msg):
        self.status_area.config(state='normal')
        self.status_area.insert('end', msg + '\n')
        self.status_area.see('end')
        self.status_area.config(state='disabled')

    def log_status(self, msg):
        self.set_status(msg)

    def set_progress(self, percent):
        self.progress_var.set(percent)

if __name__ == '__main__':
    app = MusicDLApp()
    app.mainloop() 