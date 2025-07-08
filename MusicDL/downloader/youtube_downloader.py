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
import logging

# Set up logging for metadata operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_metadata_value(value):
    """Clean and validate metadata values to prevent duplicates and ensure accuracy"""
    if not value:
        return None
    # Remove extra whitespace and normalize
    cleaned = str(value).strip()
    # Remove common problematic characters that can cause duplicates
    cleaned = re.sub(r'[<>:"/\\|?*]', '', cleaned)
    # Limit length to prevent overly long metadata
    if len(cleaned) > 200:
        cleaned = cleaned[:200]
    return cleaned if cleaned else None

def validate_metadata(metadata):
    """Validate metadata to ensure required fields are present and accurate"""
    required_fields = ['title', 'artist']
    validated = {}
    
    # Allow blank/empty metadata - just clean what we have
    for field in required_fields:
        if field not in metadata or not metadata[field]:
            # Use filename or default values instead of rejecting
            if field == 'title':
                validated[field] = 'Unknown Title'
            elif field == 'artist':
                validated[field] = 'Unknown Artist'
            logger.warning(f"Missing {field}, using default value")
        else:
            validated[field] = clean_metadata_value(metadata[field])
    
    # Clean all other metadata values (allow blank/empty)
    for key, value in metadata.items():
        if key not in validated:  # Don't overwrite already processed required fields
            cleaned_value = clean_metadata_value(value)
            if cleaned_value:  # Only add non-empty values
                validated[key] = cleaned_value
    
    # Ensure title and artist are not too similar (potential duplicates)
    if 'title' in validated and 'artist' in validated:
        title_norm = re.sub(r'[^a-zA-Z0-9]', '', validated['title'].lower())
        artist_norm = re.sub(r'[^a-zA-Z0-9]', '', validated['artist'].lower())
        if title_norm == artist_norm and title_norm not in ['unknown', '']:
            logger.warning(f"Title and artist are identical: {validated['title']}")
            # Don't reject, just log the warning
    
    return validated

def tag_audio_file(filepath, metadata, audio_format):
    """Tag audio file with validated metadata"""
    try:
        # Validate metadata before tagging
        validated_metadata = validate_metadata(metadata)
        if not validated_metadata:
            logger.error(f"Invalid metadata for {filepath}")
            return False
            
        logger.info(f"Tagging {filepath} with metadata: {validated_metadata}")
        
        if audio_format == 'mp3':
            audio = EasyID3(filepath)
            if 'title' in validated_metadata:
                audio['title'] = validated_metadata['title']
            if 'artist' in validated_metadata:
                audio['artist'] = validated_metadata['artist']
            if 'album' in validated_metadata:
                audio['album'] = validated_metadata['album']
            if 'date' in validated_metadata:
                audio['date'] = validated_metadata['date']
            if 'genre' in validated_metadata:
                audio['genre'] = validated_metadata['genre']
            if 'tracknumber' in validated_metadata:
                audio['tracknumber'] = str(validated_metadata['tracknumber'])
            audio.save()
            # Add cover art if present
            if 'cover_art' in validated_metadata and validated_metadata['cover_art']:
                try:
                    id3 = ID3(filepath)
                    cover_data = validated_metadata['cover_art']
                    if isinstance(cover_data, str):
                        with open(cover_data, 'rb') as imgf:
                            cover_data = imgf.read()
                    id3.add(APIC(
                        encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_data
                    ))
                    id3.save()
                except ID3Error:
                    logger.warning(f"Failed to add cover art to {filepath}")
        elif audio_format == 'flac':
            audio = FLAC(filepath)
            for k, v in validated_metadata.items():
                if k != 'cover_art':
                    audio[k] = v
            if 'cover_art' in validated_metadata and validated_metadata['cover_art']:
                from mutagen.flac import Picture
                pic = Picture()
                cover_data = validated_metadata['cover_art']
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
            if 'title' in validated_metadata:
                audio['nam'] = [validated_metadata['title']]
            if 'artist' in validated_metadata:
                audio['ART'] = [validated_metadata['artist']]
            if 'album' in validated_metadata:
                audio['alb'] = [validated_metadata['album']]
            if 'date' in validated_metadata:
                audio['day'] = [validated_metadata['date']]
            if 'genre' in validated_metadata:
                audio['gen'] = [validated_metadata['genre']]
            if 'tracknumber' in validated_metadata:
                audio['trkn'] = [(int(validated_metadata['tracknumber']), 0)]
            if 'cover_art' in validated_metadata and validated_metadata['cover_art']:
                cover_data = validated_metadata['cover_art']
                if isinstance(cover_data, str):
                    with open(cover_data, 'rb') as imgf:
                        cover_data = imgf.read()
                audio['covr'] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
            audio.save()
        elif audio_format == 'opus':
            audio = OggVorbis(filepath)
            for k, v in validated_metadata.items():
                if k != 'cover_art':
                    audio[k] = v
            audio.save()
        
        logger.info(f"Successfully tagged {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to tag {filepath}: {e}")
        return False

def normalize_filename(artist, title):
    """Improved filename normalization for better duplicate detection"""
    if not artist or not title:
        return None
    
    # Clean and normalize both artist and title
    artist_clean = clean_metadata_value(artist)
    title_clean = clean_metadata_value(title)
    
    if not artist_clean or not title_clean:
        return None
    
    base = f"{artist_clean} - {title_clean}"
    # Remove common patterns that don't affect uniqueness
    base = re.sub(r'\([^)]*\)', '', base)  # Remove parentheses content
    base = re.sub(r'\[[^\]]*\]', '', base)  # Remove bracket content
    base = re.sub(r'feat\.?|ft\.?|featuring', '', base, flags=re.IGNORECASE)  # Remove featuring
    base = re.sub(r'[^a-zA-Z0-9\s]+', '', base)  # Keep only alphanumeric and spaces
    base = re.sub(r'\s+', ' ', base).strip()  # Normalize whitespace
    return base.lower()

def file_exists(download_dir, artist, title, audio_format):
    """Improved duplicate detection with better normalization"""
    norm = normalize_filename(artist, title)
    if not norm:
        return False
    
    for file in os.listdir(download_dir):
        if file.lower().endswith('.' + audio_format):
            name = os.path.splitext(file)[0]
            name_norm = normalize_filename(name.split(' - ')[0] if ' - ' in name else '', 
                                         name.split(' - ')[1] if ' - ' in name else name)
            if name_norm and name_norm == norm:
                logger.info(f"Duplicate detected: {artist} - {title}")
                return True
    return False

def extract_metadata_from_video(video_info):
    """Extract metadata from YouTube video information"""
    metadata = {}
    
    try:
        # Extract title and clean it
        if 'title' in video_info:
            title = video_info['title']
            # Remove common YouTube suffixes
            title = re.sub(r'\s*\(Official.*?\)', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\[Official.*?\]', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\(Lyrics.*?\)', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\[Lyrics.*?\]', '', title, flags=re.IGNORECASE)
            metadata['title'] = clean_metadata_value(title)
        
        # Extract artist from title or uploader
        if 'uploader' in video_info:
            metadata['artist'] = clean_metadata_value(video_info['uploader'])
        
        # Extract upload date
        if 'upload_date' in video_info:
            date_str = video_info['upload_date']
            if len(date_str) >= 4:
                metadata['date'] = date_str[:4]  # Just the year
        
        # Extract description for additional metadata
        if 'description' in video_info:
            desc = video_info['description']
            # Look for artist in description
            if not metadata.get('artist') and desc:
                # Common patterns in music video descriptions
                artist_patterns = [
                    r'Artist:\s*([^\n]+)',
                    r'Performed by:\s*([^\n]+)',
                    r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                ]
                for pattern in artist_patterns:
                    match = re.search(pattern, desc, re.IGNORECASE)
                    if match:
                        metadata['artist'] = clean_metadata_value(match.group(1))
                        break
        
        # Extract thumbnail as cover art
        if 'thumbnail' in video_info:
            try:
                import requests
                resp = requests.get(video_info['thumbnail'])
                if resp.status_code == 200:
                    metadata['cover_art'] = resp.content
            except Exception:
                pass
        
        logger.info(f"Extracted metadata: {metadata}")
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to extract metadata from video: {e}")
        return {}

def cleanup_downloads(download_dir, allowed_exts=(".mp3", ".mp4", ".m4a", ".flac", ".wav", ".opus", ".ogg", ".aac"), retries=3, delay=2):
    for attempt in range(retries):
        files_to_delete = [f for f in os.listdir(download_dir) if not f.lower().endswith(allowed_exts)]
        if not files_to_delete:
            break
        for f in files_to_delete:
            try:
                os.remove(os.path.join(download_dir, f))
            except Exception as e:
                if attempt == retries - 1:
                    print(f"Failed to delete {f} after {retries} attempts: {e}")
        time.sleep(delay)

def download_youtube(link, mode, status_callback, download_dir=None, target_format='mp3', metadata=None):
    out_dir = download_dir or os.path.join(os.path.dirname(__file__), '..', 'downloads')
    os.makedirs(out_dir, exist_ok=True)
    
    # Validate provided metadata
    if metadata:
        validated_metadata = validate_metadata(metadata)
        if not validated_metadata:
            logger.warning("Invalid provided metadata, will extract from video")
            metadata = None
    
    # Duplicate check if metadata is available
    if metadata and 'artist' in metadata and 'title' in metadata:
        if file_exists(out_dir, metadata['artist'], metadata['title'], target_format):
            status_callback(f"Skipped (already exists): {metadata['artist']} - {metadata['title']}")
            return True
    
    progress_event_received = {'flag': False}
    def wrapped_status_callback(d):
        if isinstance(d, dict) and d.get('status') == 'downloading':
            progress_event_received['flag'] = True
        status_callback(d)
    
    # Optimize yt-dlp options for direct conversion during download
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
        'noplaylist': False,
        'quiet': True,
    }
    postprocessors = []
    # Supported formats for direct yt-dlp conversion
    yt_dlp_formats = ['mp3', 'm4a', 'flac', 'wav', 'opus', 'ogg', 'aac']
    if target_format in yt_dlp_formats:
        postprocessors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': target_format,
            'preferredquality': '192',
        })
    ydl_opts['postprocessors'] = postprocessors
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info first for metadata
            if not metadata:
                try:
                    video_info = ydl.extract_info(link, download=False)
                    metadata = extract_metadata_from_video(video_info)
                except Exception as e:
                    logger.warning(f"Failed to extract video info: {e}")
                    metadata = {}
            
            # Ensure we have at least basic metadata for filename generation
            if not metadata or not metadata.get('title') or not metadata.get('artist'):
                logger.warning("Using fallback metadata for filename generation")
                # Extract basic info from yt-dlp for filename
                try:
                    video_info = ydl.extract_info(link, download=False)
                    fallback_title = video_info.get('title', 'Unknown Title')
                    fallback_artist = video_info.get('uploader', 'Unknown Artist')
                    if not metadata:
                        metadata = {}
                    metadata['title'] = metadata.get('title') or clean_metadata_value(fallback_title)
                    metadata['artist'] = metadata.get('artist') or clean_metadata_value(fallback_artist)
                except Exception as e:
                    logger.error(f"Failed to get fallback metadata: {e}")
                    # Use completely generic metadata
                    if not metadata:
                        metadata = {'title': 'Unknown Title', 'artist': 'Unknown Artist'}
            
            # Download and convert in one step
            logger.info(f"Starting download with conversion to {target_format}")
            result = ydl.download([link])
        
        # If no progress event was received, warn the GUI
        if not progress_event_received['flag']:
            status_callback('Warning: No progress events received from yt-dlp. Progress bar may not update.')
        
        # Tag the converted file with metadata (if not already embedded by postprocessor)
        if target_format != 'original' and metadata and 'artist' in metadata and 'title' in metadata:
            expected_filename = f"{metadata['artist']} - {metadata['title']}.{target_format}"
            file_path = os.path.join(out_dir, expected_filename)
            if os.path.exists(file_path):
                # Wait for file to be fully written
                for _ in range(10):  # Try for up to 10 seconds
                    try:
                        with open(file_path, 'ab') as f:
                            pass
                        break
                    except OSError:
                        time.sleep(1)
                
                # Tag with metadata (this will overwrite any basic metadata from postprocessor)
                if tag_audio_file(file_path, metadata, target_format):
                    logger.info(f"Successfully tagged converted file: {expected_filename}")
                else:
                    logger.warning(f"Failed to tag converted file: {expected_filename}")
        
        # Clean up only thumbnail files (no .webm files should exist since we convert during download)
        for file in os.listdir(out_dir):
            if file.lower().endswith(('.jpg', '.png', '.webp')):
                try:
                    os.remove(os.path.join(out_dir, file))
                except Exception:
                    pass
        
        # If the format is not natively supported, convert with ffmpeg
        if target_format not in yt_dlp_formats:
            # Find the downloaded file (assume only one new file)
            files = [f for f in os.listdir(out_dir) if f.lower().endswith(('.mp3', '.m4a', '.flac', '.wav', '.opus', '.ogg', '.aac'))]
            if files:
                src_file = os.path.join(out_dir, files[0])
                dest_file = os.path.splitext(src_file)[0] + f'.{target_format}'
                subprocess.run(['ffmpeg', '-y', '-i', src_file, dest_file])
                os.remove(src_file)
        
        # Delay and retry cleanup to avoid file-in-use errors
        cleanup_downloads(out_dir)
        return True
    except Exception as e:
        status_callback(f'yt-dlp error: {e}')
        logger.error(f"Download failed: {e}")
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