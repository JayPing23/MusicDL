import yt_dlp
import os
import subprocess
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import ID3, APIC, error as ID3Error
import re
import time
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, ID3NoHeaderError

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
    progress_event_received = {'flag': False}
    def wrapped_status_callback(d):
        if isinstance(d, dict) and d.get('status') == 'downloading':
            progress_event_received['flag'] = True
        status_callback(d)
    # Use artist and title in the output filename for uniqueness
    ydl_opts = {
        'outtmpl': os.path.join(out_dir, '%(artist)s - %(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [wrapped_status_callback],
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
        # If no progress event was received, warn the GUI
        if not progress_event_received['flag']:
            status_callback('Warning: No progress events received from yt-dlp. Progress bar may not update.')
        # Tag only the file that was just created
        if mode == 'audio' and audio_format != 'original' and metadata and 'artist' in metadata and 'title' in metadata:
            expected_filename = f"{metadata['artist']} - {metadata['title']}.{audio_format}"
            file_path = os.path.join(out_dir, expected_filename)
            if os.path.exists(file_path):
                for _ in range(10):  # Try for up to 10 seconds
                    try:
                        with open(file_path, 'ab') as f:
                            pass
                        break
                    except OSError:
                        time.sleep(1)
                tag_audio_file(file_path, metadata, audio_format)
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

if __name__ == '__main__':
    import sys
    import glob
    import requests
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    import json

    if '--clear-metadata' in sys.argv:
        downloads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'downloads'))
        files = glob.glob(os.path.join(downloads_dir, '*.mp3'))
        print(f"Found {len(files)} mp3 files in downloads.")
        for file_path in files:
            try:
                # Remove all ID3 tags
                try:
                    audio = ID3(file_path)
                    audio.delete()
                    print(f"Cleared metadata: {os.path.basename(file_path)}")
                except ID3NoHeaderError:
                    print(f"No metadata to clear: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error clearing {os.path.basename(file_path)}: {e}")
        sys.exit(0)

    # Load Spotify credentials
    cred_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'spotify_credentials.json')
    with open(cred_path, 'r') as f:
        creds = json.load(f)
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=creds['client_id'],
        client_secret=creds['client_secret']
    ))

    downloads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'downloads'))
    files = glob.glob(os.path.join(downloads_dir, '*.mp3'))
    print(f"Found {len(files)} mp3 files in downloads.")

    for file_path in files:
        filename = os.path.basename(file_path)
        # Try to parse artist and title from filename: 'Artist - Title.mp3'
        if ' - ' in filename:
            artist, title = filename.rsplit('.mp3', 1)[0].split(' - ', 1)
        else:
            print(f"Skipping (cannot parse): {filename}")
            continue
        # Search Spotify for track
        query = f"track:{title} artist:{artist}"
        results = sp.search(q=query, type='track', limit=1)
        if results['tracks']['items']:
            t = results['tracks']['items'][0]
            album = t['album']['name']
            date = t['album']['release_date']
            genre = ''  # Spotify API does not provide genre per track
            tracknumber = t['track_number']
            # Fetch cover art
            cover_art = None
            if t['album']['images']:
                cover_url = t['album']['images'][0]['url']
                try:
                    resp = requests.get(cover_url)
                    if resp.status_code == 200:
                        cover_art = resp.content
                except Exception:
                    cover_art = None
            metadata = {'title': title, 'artist': artist, 'album': album, 'date': date, 'genre': genre, 'tracknumber': tracknumber, 'cover_art': cover_art}
            tag_audio_file(file_path, metadata, 'mp3')
            print(f"Tagged: {filename}")
        else:
            print(f"No Spotify match for: {filename}") 