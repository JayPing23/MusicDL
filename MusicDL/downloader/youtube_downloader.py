import yt_dlp
import os
import subprocess

def download_youtube(link, mode, status_callback):
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'downloads')
    os.makedirs(out_dir, exist_ok=True)
    ydl_opts = {
        'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'progress_hooks': [lambda d: status_callback(d.get('status', ''))],
    }
    if mode == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        })
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return True
    except Exception as e:
        status_callback(f'yt-dlp error: {e}')
        return False 