from fastapi import FastAPI, Request, Form, BackgroundTasks, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import yt_dlp
import uuid
from typing import Dict
import threading
import time
import logging
import shutil
import zipfile
import traceback
import tempfile
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

musicdlWeb = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'downloads')
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

IN_PROGRESS_DIR = os.path.join(DOWNLOADS_DIR, 'in_progress')
os.makedirs(IN_PROGRESS_DIR, exist_ok=True)

musicdlWeb.mount('/static', StaticFiles(directory=os.path.join(BASE_DIR, 'static')), name='static')
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, 'templates'))

logging.basicConfig(level=logging.INFO)

# In-memory set to track files being downloaded/converted
in_progress_files = set()

def cleanup_downloads_periodically():
    while True:
        try:
            for f in os.listdir(DOWNLOADS_DIR):
                file_path = os.path.join(DOWNLOADS_DIR, f)
                if os.path.isfile(file_path) and file_path not in in_progress_files:
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

# Per-file delayed cleanup
cleanup_timers = {}
def schedule_file_cleanup(filepath, delay=1800):
    def delete_file():
        try:
            if os.path.exists(filepath) and filepath not in in_progress_files:
                os.remove(filepath)
                print(f"[CLEANUP] Deleted: {filepath}")
        except Exception as e:
            print(f"[CLEANUP ERROR] Could not delete {filepath}: {e}")
    def timer_func():
        time.sleep(delay)
        delete_file()
    t = threading.Thread(target=timer_func, daemon=True)
    t.start()
    cleanup_timers[filepath] = t

def yt_dlp_progress_hook(task_id, current_track=None, total_tracks=None, current_title=None):
    def hook(d):
        prog = download_progress.get(task_id, {})
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
            downloaded = d.get('downloaded_bytes', 0)
            percent = int(downloaded / total * 100) if total else 0
            prog.update({
                'status': 'downloading',
                'filename': d.get('filename', ''),
                'percent': percent,
                'downloaded': downloaded,
                'total': total,
                'details': d.get('info_dict', {}).get('title', ''),
                'format': d.get('info_dict', {}).get('ext', ''),
            })
            if current_track is not None and total_tracks is not None:
                prog['current_track'] = current_track
                prog['total_tracks'] = total_tracks
                prog['current_title'] = current_title
            download_progress[task_id] = prog
        elif d['status'] == 'finished':
            prog.update({
                'status': 'finished',
                'filename': d.get('filename', ''),
                'details': d.get('info_dict', {}).get('title', ''),
                'format': d.get('info_dict', {}).get('ext', ''),
            })
            download_progress[task_id] = prog
    return hook

@musicdlWeb.get('/', response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse('index.html', {"request": request})

def tag_audio_file(filepath, metadata, audio_format):
    try:
        if audio_format == 'mp3':
            audio = EasyID3(filepath)
            if 'title' in metadata: audio['title'] = metadata['title']
            if 'artist' in metadata: audio['artist'] = metadata['artist']
            if 'album' in metadata: audio['album'] = metadata['album']
            if 'date' in metadata: audio['date'] = metadata['date']
            if 'genre' in metadata: audio['genre'] = metadata['genre']
            audio.save()
        elif audio_format == 'flac':
            audio = FLAC(filepath)
            for k, v in metadata.items():
                audio[k] = v
            audio.save()
        elif audio_format == 'm4a':
            audio = MP4(filepath)
            if 'title' in metadata: audio['nam'] = [metadata['title']]
            if 'artist' in metadata: audio['ART'] = [metadata['artist']]
            if 'album' in metadata: audio['alb'] = [metadata['album']]
            if 'date' in metadata: audio['day'] = [metadata['date']]
            if 'genre' in metadata: audio['gen'] = [metadata['genre']]
            audio.save()
        elif audio_format == 'ogg':
            audio = OggVorbis(filepath)
            for k, v in metadata.items():
                audio[k] = v
            audio.save()
        return True
    except Exception as e:
        print(f"[TAGGING ERROR] {filepath}: {e}")
        return False

def wait_for_file_release(filepath, timeout=10):
    """Wait until the file is not locked (up to timeout seconds)."""
    import time
    for _ in range(timeout * 2):
        try:
            with open(filepath, 'ab'):
                return True
        except OSError:
            time.sleep(0.5)
    return False

@musicdlWeb.post('/download')
def download(request: Request, youtube_url: str = Form(...), format: str = Form('mp3'), download_type: str = Form('single')):
    import traceback
    import subprocess
    task_id = str(uuid.uuid4())
    download_progress[task_id] = {'status': 'queued'}
    try:
        outtmpl = os.path.join(IN_PROGRESS_DIR, '%(playlist_index)s-%(title)s-%(id)s.%(ext)s')
        ydl_opts = {
            'format': 'bestaudio/best' if format != 'mp4' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
            'outtmpl': outtmpl,
            'noplaylist': download_type == 'single',
            'quiet': True,
            'nooverwrites': True,
            'nopart': True,
        }
        if format in ['mp3', 'm4a', 'flac', 'wav', 'opus', 'ogg', 'aac']:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
                'preferredquality': '192',
            }]
        download_progress[task_id] = {'status': 'downloading', 'percent': 0}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            entries = info['entries'] if 'entries' in info else [info]
            converted_files = []
            for idx, entry in enumerate(entries):
                base = os.path.splitext(ydl.prepare_filename(entry))[0]
                in_progress_name = f"{base}.{format}"
                final_name = os.path.join(DOWNLOADS_DIR, os.path.basename(in_progress_name))
                in_progress_path = os.path.join(IN_PROGRESS_DIR, os.path.basename(in_progress_name))
                if not os.path.exists(in_progress_path):
                    continue
                in_progress_files.add(final_name)
                if not wait_for_file_release(in_progress_path):
                    print(f"[ERROR] File is locked and cannot be accessed: {in_progress_path}")
                    in_progress_files.remove(final_name)
                    continue
                # Move file from in_progress to downloads
                try:
                    shutil.move(in_progress_path, final_name)
                except Exception as e:
                    print(f"[MOVE ERROR] Could not move {in_progress_path} to {final_name}: {e}")
                    in_progress_files.remove(final_name)
                    continue
                metadata = {
                    'title': entry.get('title', ''),
                    'artist': entry.get('uploader', ''),
                    'album': entry.get('album', ''),
                    'date': entry.get('upload_date', ''),
                    'genre': entry.get('genre', '')
                }
                tag_audio_file(final_name, metadata, format)
                converted_files.append(final_name)
                # Schedule cleanup for this file
                schedule_file_cleanup(final_name, delay=1800)
                in_progress_files.remove(final_name)
                download_progress[task_id] = {
                    'status': 'downloading',
                    'percent': int((idx+1)/len(entries)*100),
                    'current_track': idx+1,
                    'total_tracks': len(entries),
                    'current_title': entry.get('title', '')
                }
            # Create ZIP if playlist
            zip_url = None
            if len(converted_files) > 1:
                zip_name = f"playlist_{task_id}.zip"
                zip_path = os.path.join(DOWNLOADS_DIR, zip_name)
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for f in converted_files:
                        zipf.write(f, arcname=os.path.basename(f))
                zip_url = f"/files/{zip_name}"
                # Schedule cleanup for ZIP
                schedule_file_cleanup(zip_path, delay=1800)
            download_progress[task_id] = {
                'status': 'done',
                'downloaded_files': [os.path.basename(f) for f in converted_files],
                'zip_url': zip_url,
                'is_playlist': len(converted_files) > 1
            }
            print(f"[SUCCESS] Downloaded and converted: {converted_files}")
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[DOWNLOAD/CONVERT ERROR] {e}\n{tb}")
        download_progress[task_id] = {
            'status': 'error',
            'error': f"{e}\n{tb}"
        }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JSONResponse({'task_id': task_id})
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
    if prog.get('status') in ('finished', 'done') and prog.get('downloaded_files'):
        # For single file, provide direct link
        if not prog.get('is_playlist') and prog['downloaded_files']:
            file_url = f"/files/{prog['downloaded_files'][0]}"
    prog['file_url'] = file_url
    # For playlist, provide zip_url and individual file links
    return JSONResponse(prog)

@musicdlWeb.get('/files', response_class=HTMLResponse)
def list_files(request: Request):
    files = [f for f in os.listdir(DOWNLOADS_DIR) if f.lower().endswith(('.mp3', '.mp4'))]
    # Exclude in-progress files
    files = [f for f in files if os.path.join(DOWNLOADS_DIR, f) not in in_progress_files]
    return templates.TemplateResponse('files.html', {"request": request, "files": files})

@musicdlWeb.get('/files/{filename}')
def serve_file(filename: str):
    file_path = os.path.join(DOWNLOADS_DIR, filename)
    # Do not serve in-progress files
    if file_path in in_progress_files:
        return HTMLResponse("File is still being processed. Please try again later.", status_code=423)
    if os.path.exists(file_path):
        ext = os.path.splitext(filename)[1].lower()
        media_type = 'audio/mpeg' if ext == '.mp3' else 'video/mp4' if ext == '.mp4' else 'application/octet-stream'
        return FileResponse(file_path, media_type=media_type, filename=filename)
    return HTMLResponse("File not found", status_code=404)

ALLOWED_FORMATS = ("mp3", "m4a", "flac", "wav", "opus", "ogg", "aac")

@musicdlWeb.get('/convert', response_class=HTMLResponse)
def convert_page(request: Request):
    return templates.TemplateResponse('convert.html', {"request": request, "formats": ALLOWED_FORMATS})

@musicdlWeb.post('/convert')
async def convert_files(request: Request, files: list[UploadFile] = File(...), format: str = Form(...)):
    converted_files = []
    for file in files:
        input_path = os.path.join(DOWNLOADS_DIR, file.filename)
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        base = os.path.splitext(file.filename)[0]
        output_path = os.path.join(DOWNLOADS_DIR, f"{base}.{format}")
        # Convert with ffmpeg
        import subprocess
        try:
            subprocess.run(["ffmpeg", "-y", "-i", input_path, output_path], check=True)
            # Wait for file release after conversion
            if not wait_for_file_release(output_path):
                print(f"[ERROR] Converted file is locked and cannot be accessed: {output_path}")
                continue
            converted_files.append(f"/files/{base}.{format}")
            print(f"[SUCCESS] Converted: {output_path}")
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[CONVERT ERROR] {e}\n{tb}")
        # Remove the uploaded file after conversion
        try:
            os.remove(input_path)
        except Exception:
            pass
    # Cleanup non-converted files
    cleanup_downloads(DOWNLOADS_DIR, allowed_exts=tuple(f".{fmt}" for fmt in ALLOWED_FORMATS))
    return templates.TemplateResponse('convert_done.html', {"request": request, "files": converted_files}) 