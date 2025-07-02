import yt_dlp
import os
import subprocess
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import ID3, APIC, error as ID3Error
import re

def tag_audio_file(filepath, metadata, audio_format):
    try:
        if audio_format == 'mp3':
            audio = EasyID3(filepath)
            if 'title' in metadata:
                audio['title'] = metadata['title']
            if 'artist' in metadata:
                audio['artist'] = metadata['artist']
            if 'album' in metadata:
                audio['album'] = metadata['album']
            if 'date' in metadata:
                audio['date'] = metadata['date']
            if 'genre' in metadata:
                audio['genre'] = metadata['genre']
            if 'tracknumber' in metadata:
                audio['tracknumber'] = str(metadata['tracknumber'])
            audio.save()
            # Add cover art if present
            if 'cover_art' in metadata and metadata['cover_art']:
                try:
                    id3 = ID3(filepath)
                    cover_data = metadata['cover_art']
                    if isinstance(cover_data, str):
                        with open(cover_data, 'rb') as imgf:
                            cover_data = imgf.read()
                    id3.add(APIC(
                        encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_data
                    ))
                    id3.save()
                except ID3Error:
                    pass
        elif audio_format == 'flac':
            audio = FLAC(filepath)
            for k, v in metadata.items():
                if k != 'cover_art':
                    audio[k] = v
            if 'cover_art' in metadata and metadata['cover_art']:
                from mutagen.flac import Picture
                pic = Picture()
                cover_data = metadata['cover_art']
                if isinstance(cover_data, str):
                    with open(cover_data, 'rb') as imgf:
                        cover_data = imgf.read()
                pic.data = cover_data
                pic.type = 3
                pic.mime = 'image/jpeg'
                audio.add_picture(pic)
            audio.save()
        elif audio_format == 'm4a':
            audio = MP4(filepath)
            if 'title' in metadata:
                audio['nam'] = [metadata['title']]
            if 'artist' in metadata:
                audio['ART'] = [metadata['artist']]
            if 'album' in metadata:
                audio['alb'] = [metadata['album']]
            if 'date' in metadata:
                audio['day'] = [metadata['date']]
            if 'genre' in metadata:
                audio['gen'] = [metadata['genre']]
            if 'tracknumber' in metadata:
                audio['trkn'] = [(int(metadata['tracknumber']), 0)]
            if 'cover_art' in metadata and metadata['cover_art']:
                cover_data = metadata['cover_art']
                if isinstance(cover_data, str):
                    with open(cover_data, 'rb') as imgf:
                        cover_data = imgf.read()
                audio['covr'] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
            audio.save()
        elif audio_format == 'opus':
            audio = OggVorbis(filepath)
            for k, v in metadata.items():
                if k != 'cover_art':
                    audio[k] = v
            audio.save()
    except Exception:
        pass  # Tagging is best-effort

def normalize_filename(artist, title):
    base = f"{artist} - {title}"
    base = re.sub(r'\([^)]*\)', '', base)
    base = re.sub(r'[^a-zA-Z0-9]+', '', base).lower()
    return base

def file_exists(download_dir, artist, title, audio_format):
    norm = normalize_filename(artist, title)
    for file in os.listdir(download_dir):
        if file.lower().endswith('.' + audio_format):
            name = os.path.splitext(file)[0]
            name = re.sub(r'\([^)]*\)', '', name)
            name = re.sub(r'[^a-zA-Z0-9]+', '', name).lower()
            if name == norm:
                return True
    return False

def download_youtube(link, mode, status_callback, download_dir=None, audio_format='mp3', metadata=None):
    out_dir = download_dir or os.path.join(os.path.dirname(__file__), '..', 'downloads')
    os.makedirs(out_dir, exist_ok=True)
    # Duplicate check if metadata is available
    if metadata and 'artist' in metadata and 'title' in metadata:
        if file_exists(out_dir, metadata['artist'], metadata['title'], audio_format):
            status_callback(f"Skipped (already exists): {metadata['artist']} - {metadata['title']}")
            return True
    ydl_opts = {
        'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'progress_hooks': [lambda d: status_callback(d.get('status', ''))],
        'keepvideo': False,
        'keepaudio': False,
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
            result = ydl.download([link])
        # Tag the file if metadata is provided
        if mode == 'audio' and audio_format != 'original' and metadata:
            for file in os.listdir(out_dir):
                if file.lower().endswith('.' + audio_format):
                    tag_audio_file(os.path.join(out_dir, file), metadata, audio_format)
        # Manual cleanup: remove any leftover .webm files
        for file in os.listdir(out_dir):
            if file.lower().endswith('.webm'):
                try:
                    os.remove(os.path.join(out_dir, file))
                except Exception:
                    pass
        return True
    except Exception as e:
        status_callback(f'yt-dlp error: {e}')
        return False 