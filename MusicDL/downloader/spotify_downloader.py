import os
import json
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
        playlist = sp.playlist_tracks(link)
        tracks = [item['track'] for item in playlist['items']]
    else:
        status_callback('Invalid Spotify link')
        return False
    for t in tracks:
        title = t['name']
        artist = t['artists'][0]['name']
        query = f"{title} {artist} audio"
        yt_url = search_youtube(query)
        if yt_url:
            status_callback(f"Downloading: {title} by {artist}")
            download_youtube(yt_url, mode, status_callback, download_dir, audio_format)
        else:
            status_callback(f"YouTube search failed for: {title} by {artist}")
    return True 