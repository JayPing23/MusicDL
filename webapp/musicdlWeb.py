from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import yt_dlp
import uuid
from typing import Dict
import threading
import time
import logging

musicdlWeb = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'downloads')
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

musicdlWeb.mount('/static', StaticFiles(directory=os.path.join(BASE_DIR, 'static')), name='static')
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, 'templates'))

logging.basicConfig(level=logging.INFO)

def cleanup_downloads_periodically():
    while True:
        try:
            for f in os.listdir(DOWNLOADS_DIR):
                file_path = os.path.join(DOWNLOADS_DIR, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            logging.info("[Cleanup] Downloads folder cleared.")
        except Exception as e:
            logging.error(f"[Cleanup] Error clearing downloads: {e}")
        time.sleep(1800)  # 30 minutes

# Start the cleanup thread when the app launches
cleanup_thread = threading.Thread(target=cleanup_downloads_periodically, daemon=True)
cleanup_thread.start()

# In-memory progress tracking
download_progress: Dict[str, dict] = {}

def yt_dlp_progress_hook(task_id):
    def hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
            downloaded = d.get('downloaded_bytes', 0)
            percent = int(downloaded / total * 100) if total else 0
            download_progress[task_id] = {
                'status': 'downloading',
                'filename': d.get('filename', ''),
                'percent': percent,
                'downloaded': downloaded,
                'total': total,
                'details': d.get('info_dict', {}).get('title', ''),
                'format': d.get('info_dict', {}).get('ext', '')
            }
        elif d['status'] == 'finished':
            download_progress[task_id] = {
                'status': 'finished',
                'filename': d.get('filename', ''),
                'details': d.get('info_dict', {}).get('title', ''),
                'format': d.get('info_dict', {}).get('ext', '')
            }
    return hook

@musicdlWeb.get('/', response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse('index.html', {"request": request})

@musicdlWeb.post('/download')
def download(request: Request, youtube_url: str = Form(...), format: str = Form('mp3'), background_tasks: BackgroundTasks = None):
    task_id = str(uuid.uuid4())
    download_progress[task_id] = {'status': 'queued'}
    def run_yt_dlp(url, task_id, format):
        try:
            if format == 'mp3':
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(DOWNLOADS_DIR, '%(title)s.%(ext)s'),
                    'noplaylist': False,
                    'extractaudio': True,
                    'audioformat': 'mp3',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [yt_dlp_progress_hook(task_id)],
                    'quiet': True,
                }
            elif format == 'mp4':
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
                    'outtmpl': os.path.join(DOWNLOADS_DIR, '%(title)s.%(ext)s'),
                    'noplaylist': False,
                    'progress_hooks': [yt_dlp_progress_hook(task_id)],
                    'quiet': True,
                }
            else:
                raise Exception('Unsupported format')
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            download_progress[task_id] = {'status': 'done'}
        except Exception as e:
            download_progress[task_id] = {
                'status': 'error',
                'error': str(e)
            }
    if background_tasks:
        background_tasks.add_task(run_yt_dlp, youtube_url, task_id, format)
    else:
        run_yt_dlp(youtube_url, task_id, format)
    return RedirectResponse(f'/progress/{task_id}', status_code=303)

@musicdlWeb.get('/progress/{task_id}', response_class=HTMLResponse)
def progress_page(request: Request, task_id: str):
    prog = download_progress.get(task_id, {})
    file_url = None
    if prog.get('status') in ('finished', 'done') and prog.get('filename'):
        filename = os.path.basename(prog['filename'])
        file_url = f'/files/{filename}'
    return templates.TemplateResponse('progress.html', {"request": request, "task_id": task_id, "file_url": file_url})

@musicdlWeb.get('/progress/{task_id}/status')
def progress_status(task_id: str):
    prog = download_progress.get(task_id, {'status': 'unknown'})
    file_url = None
    if prog.get('status') in ('finished', 'done') and prog.get('filename'):
        filename = os.path.basename(prog['filename'])
        file_url = f'/files/{filename}'
    prog['file_url'] = file_url
    return JSONResponse(prog)

@musicdlWeb.get('/files', response_class=HTMLResponse)
def list_files(request: Request):
    files = [f for f in os.listdir(DOWNLOADS_DIR) if f.lower().endswith(('.mp3', '.mp4'))]
    return templates.TemplateResponse('files.html', {"request": request, "files": files})

@musicdlWeb.get('/files/{filename}')
def serve_file(filename: str):
    file_path = os.path.join(DOWNLOADS_DIR, filename)
    if os.path.exists(file_path):
        ext = os.path.splitext(filename)[1].lower()
        media_type = 'audio/mpeg' if ext == '.mp3' else 'video/mp4' if ext == '.mp4' else 'application/octet-stream'
        return FileResponse(file_path, media_type=media_type, filename=filename)
    return HTMLResponse("File not found", status_code=404) 