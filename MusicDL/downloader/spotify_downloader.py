import os
import json
import requests
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from downloader.youtube_downloader import download_youtube
from downloader.utils import search_youtube

def get_spotify_client():
    cred_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'spotify_credentials.json')
    with open(cred_path, 'r') as f:
        creds = json.load(f)
    return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=creds['client_id'],
        client_secret=creds['client_secret']
    ))

def download_spotify(link, mode, status_callback, download_dir=None, audio_format='mp3'):
    sp = get_spotify_client()
    tracks = []

    if 'track' in link:
        track = sp.track(link)
        tracks = [track]

    elif 'album' in link:
        album = sp.album_tracks(link)
        tracks = album['items']

    elif 'playlist' in link:
        results = sp.playlist_tracks(link, limit=100)
        tracks.extend([item['track'] for item in results['items']])
        while results['next']:
            results = sp.next(results)
            tracks.extend([item['track'] for item in results['items']])
    else:
        status_callback('Invalid Spotify link')
        return False

    for idx, t in enumerate(tracks, 1):
        if not t:  # Sometimes 'None' can be in the playlist
            continue
        title = t['name']
        artist = t['artists'][0]['name']
        album = t['album']['name'] if 'album' in t and t['album'] else ''
        date = t['album']['release_date'] if 'album' in t and t['album'] and 'release_date' in t['album'] else ''
        genre = t['album']['genres'][0] if 'album' in t and t['album'] and 'genres' in t['album'] and t['album']['genres'] else ''
        tracknumber = t['track_number'] if 'track_number' in t else idx
        # Fetch cover art if available
        cover_art = None
        if 'album' in t and t['album'] and 'images' in t['album'] and t['album']['images']:
            cover_url = t['album']['images'][0]['url']
            try:
                resp = requests.get(cover_url)
                if resp.status_code == 200:
                    cover_art = resp.content
            except Exception:
                cover_art = None
        metadata = {'title': title, 'artist': artist, 'album': album, 'date': date, 'genre': genre, 'tracknumber': tracknumber, 'cover_art': cover_art}
        # Duplicate check via callback
        if hasattr(status_callback, '__call__'):
            if status_callback(('check_duplicate', artist, title)):
                continue
        query = f"{title} {artist} audio"
        yt_url = search_youtube(query)
        if yt_url:
            status_callback(f"Downloading: {title} by {artist}")
            download_youtube(yt_url, mode, status_callback, download_dir, audio_format, metadata)
        else:
            status_callback(f"YouTube search failed for: {title} by {artist}")

    return True 