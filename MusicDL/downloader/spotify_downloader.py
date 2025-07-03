import os
import json
import requests
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from downloader.youtube_downloader import download_youtube, tag_audio_file, validate_metadata, clean_metadata_value
from downloader.utils import search_youtube
import time
import logging

# Set up logging for metadata operations
logger = logging.getLogger(__name__)

def get_spotify_client():
    cred_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'spotify_credentials.json')
    with open(cred_path, 'r') as f:
        creds = json.load(f)
    return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=creds['client_id'],
        client_secret=creds['client_secret']
    ))

def extract_spotify_metadata(track):
    """Extract and validate metadata from Spotify track"""
    try:
        if not track:
            logger.warning("Empty track data received")
            return {'title': 'Unknown Title', 'artist': 'Unknown Artist'}
        
        # Extract basic metadata
        title = clean_metadata_value(track.get('name', ''))
        if not title:
            title = 'Unknown Title'
            logger.warning("No title found in track, using default")
        
        # Extract artist (handle multiple artists)
        artists = track.get('artists', [])
        if not artists:
            artist = 'Unknown Artist'
            logger.warning("No artist found in track, using default")
        else:
            # Use primary artist, but note if there are multiple
            artist = clean_metadata_value(artists[0].get('name', ''))
            if not artist:
                artist = 'Unknown Artist'
                logger.warning("No artist name found, using default")
            
            # If multiple artists, append them to title or artist
            if len(artists) > 1:
                additional_artists = [a.get('name', '') for a in artists[1:] if a.get('name')]
                if additional_artists:
                    # Add featuring to title
                    feat_artists = ', '.join(additional_artists)
                    title = f"{title} (feat. {feat_artists})"
        
        # Extract album information (allow blank)
        album_info = track.get('album', {})
        album = clean_metadata_value(album_info.get('name', ''))
        
        # Extract release date (allow blank)
        date = ''
        if 'release_date' in album_info:
            release_date = album_info['release_date']
            if release_date:
                # Extract year from date (format: YYYY-MM-DD or YYYY)
                date = release_date[:4] if len(release_date) >= 4 else release_date
        
        # Extract genre (Spotify doesn't provide track-level genres, so we'll skip)
        genre = ''
        
        # Extract track number (allow default)
        tracknumber = track.get('track_number', 1)
        if not isinstance(tracknumber, int) or tracknumber < 1:
            tracknumber = 1
        
        # Fetch cover art (allow failure)
        cover_art = None
        if album_info.get('images'):
            try:
                # Use highest quality image
                cover_url = album_info['images'][0]['url']
                resp = requests.get(cover_url, timeout=10)
                if resp.status_code == 200:
                    cover_art = resp.content
                    logger.info(f"Successfully downloaded cover art for {title}")
                else:
                    logger.warning(f"Failed to download cover art: HTTP {resp.status_code}")
            except Exception as e:
                logger.warning(f"Failed to download cover art: {e}")
        
        # Create metadata dictionary
        metadata = {
            'title': title,
            'artist': artist,
            'album': album,
            'date': date,
            'genre': genre,
            'tracknumber': tracknumber,
            'cover_art': cover_art
        }
        
        # Validate the metadata (will use defaults if needed)
        validated_metadata = validate_metadata(metadata)
        if not validated_metadata:
            logger.warning(f"Metadata validation failed for track: {title}, using defaults")
            return {'title': title, 'artist': artist}
        
        logger.info(f"Extracted Spotify metadata: {validated_metadata}")
        return validated_metadata
        
    except Exception as e:
        logger.error(f"Failed to extract Spotify metadata: {e}")
        return {'title': 'Unknown Title', 'artist': 'Unknown Artist'}

def download_spotify(link, mode, status_callback, download_dir=None, audio_format='mp3'):
    sp = get_spotify_client()
    tracks = []
    
    try:
        if 'track' in link:
            track = sp.track(link)
            if track:
                tracks = [track]
            else:
                status_callback('Invalid Spotify track link')
                return False

        elif 'album' in link:
            album = sp.album_tracks(link)
            if album and 'items' in album:
                tracks = album['items']
            else:
                status_callback('Invalid Spotify album link')
                return False

        elif 'playlist' in link:
            results = sp.playlist_tracks(link, limit=100)
            if results and 'items' in results:
                tracks.extend([item['track'] for item in results['items'] if item.get('track')])
                while results.get('next'):
                    results = sp.next(results)
                    tracks.extend([item['track'] for item in results['items'] if item.get('track')])
            else:
                status_callback('Invalid Spotify playlist link')
                return False
        else:
            status_callback('Invalid Spotify link')
            return False
        
        if not tracks:
            status_callback('No tracks found in Spotify link')
            return False
            
        logger.info(f"Found {len(tracks)} tracks to download")
        
    except Exception as e:
        logger.error(f"Failed to fetch Spotify tracks: {e}")
        status_callback(f'Spotify API error: {e}')
        return False

    success_count = 0
    for idx, t in enumerate(tracks, 1):
        if not t:  # Sometimes 'None' can be in the playlist
            logger.warning(f"Skipping None track at index {idx}")
            continue
        
        # Extract and validate metadata (will use defaults if extraction fails)
        metadata = extract_spotify_metadata(t)
        if not metadata:
            logger.warning(f"Using default metadata for track {idx}")
            metadata = {'title': f'Track {idx}', 'artist': 'Unknown Artist'}
        
        title = metadata['title']
        artist = metadata['artist']
        
        # Duplicate check via callback
        if hasattr(status_callback, '__call__'):
            if status_callback(('check_duplicate', artist, title)):
                logger.info(f"Skipping duplicate: {artist} - {title}")
                continue
        
        # Search YouTube for the track
        query = f"{title} {artist} audio"
        yt_url = search_youtube(query)
        
        if yt_url:
            status_callback(f"Downloading: {title} by {artist}")
            success = download_youtube(yt_url, mode, status_callback, download_dir, audio_format, metadata)
            
            if success:
                # Wait for file to be fully available before next track and tag only the correct file
                if download_dir:
                    expected_filename = f"{artist} - {title}.{audio_format}"
                    file_path = os.path.join(download_dir, expected_filename)
                    if os.path.exists(file_path):
                        for _ in range(10):
                            try:
                                with open(file_path, 'ab') as f:
                                    pass
                                break
                            except OSError:
                                time.sleep(1)
                        
                        # Tag the file with the correct metadata (if not already embedded by postprocessor)
                        if tag_audio_file(file_path, metadata, audio_format):
                            success_count += 1
                            logger.info(f"Successfully downloaded and tagged: {title} by {artist}")
                        else:
                            logger.warning(f"Failed to tag: {title} by {artist}")
                    else:
                        logger.warning(f"Expected file not found: {expected_filename}")
                else:
                    success_count += 1
            else:
                logger.error(f"Failed to download: {title} by {artist}")
        else:
            status_callback(f"YouTube search failed for: {title} by {artist}")
            logger.warning(f"No YouTube URL found for: {title} by {artist}")

    logger.info(f"Downloaded {success_count} out of {len(tracks)} tracks")
    return success_count > 0 