import yt_dlp
import os
import subprocess

def download_youtube(link, mode, status_callback, download_dir=None, audio_format='mp3'):
    out_dir = download_dir or os.path.join(os.path.dirname(__file__), '..', 'downloads')
    os.makedirs(out_dir, exist_ok=True)
    ydl_opts = {
        'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'progress_hooks': [lambda d: status_callback(d.get('status', ''))],
    }
    if mode == 'audio':
        if audio_format == 'original':
            ydl_opts['format'] = 'bestaudio/best'
        else:
            ydl_opts['format'] = 'bestaudio/best'
            postproc = {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': '0' if audio_format in ['flac', 'wav'] else '320',
            }
            ydl_opts['postprocessors'] = [postproc]
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return True
    except Exception as e:
        status_callback(f'yt-dlp error: {e}')
        return False 