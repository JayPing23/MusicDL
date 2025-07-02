import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from threading import Thread
from downloader.youtube_downloader import download_youtube
from downloader.spotify_downloader import download_spotify
import os

class MusicDLApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('MusicDL - GUI Edition')
        self.geometry('600x500')
        self.resizable(False, False)
        self.create_widgets()

    def create_widgets(self):
        # Link input
        tk.Label(self, text='Paste YouTube/Spotify links (one per line):').pack(anchor='w', padx=10, pady=(10,0))
        self.link_text = scrolledtext.ScrolledText(self, height=7, width=70)
        self.link_text.pack(padx=10, pady=5)

        # Load from file
        tk.Button(self, text='Load from .txt file', command=self.load_links_from_file).pack(anchor='w', padx=10, pady=(0,10))

        # Download mode
        self.mode = tk.StringVar(value='audio')
        mode_frame = tk.Frame(self)
        tk.Label(mode_frame, text='Download mode:').pack(side='left')
        tk.Radiobutton(mode_frame, text='Audio (MP3 320kbps)', variable=self.mode, value='audio').pack(side='left')
        tk.Radiobutton(mode_frame, text='Full Video', variable=self.mode, value='video').pack(side='left')
        mode_frame.pack(anchor='w', padx=10, pady=5)

        # Download button
        tk.Button(self, text='Download', command=self.start_download).pack(pady=10)

        # Status area
        tk.Label(self, text='Status:').pack(anchor='w', padx=10)
        self.status_area = scrolledtext.ScrolledText(self, height=10, width=70, state='disabled')
        self.status_area.pack(padx=10, pady=5)

        # Progress bar (simple text for now)
        self.progress_var = tk.StringVar(value='Idle')
        self.progress_label = tk.Label(self, textvariable=self.progress_var)
        self.progress_label.pack(pady=(0,10))

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
        for idx, link in enumerate(links, 1):
            self.set_progress(f'Downloading {idx}/{len(links)}')
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
        self.set_progress('All downloads finished.')

    def set_status(self, msg):
        self.status_area.config(state='normal')
        self.status_area.insert('end', msg + '\n')
        self.status_area.see('end')
        self.status_area.config(state='disabled')

    def log_status(self, msg):
        self.set_status(msg)

    def set_progress(self, msg):
        self.progress_var.set(msg)

if __name__ == '__main__':
    app = MusicDLApp()
    app.mainloop() 