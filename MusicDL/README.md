# MusicDL (GUI Edition)

A modern desktop app to download music from YouTube and Spotify links.

## Features
- Paste YouTube or Spotify links (track, album, playlist)
- Download as MP3 (320kbps) or full video
- Batch download, progress/status in GUI
- No command line needed

## Important Note About Spotify Playlists
🚫 **You cannot access certain official Spotify playlists via the API unless:**
- You own the playlist
- It's a user-generated public playlist
- It's not part of Spotify's curated or region-locked playlists (like Today's Top Hits)

Spotify restricts access to some playlists via their Web API (even though they're visible on the website/app). If you get a 404 or missing tracks, this is likely the reason.

## Setup
1. Install Python 3.8+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install [ffmpeg](https://ffmpeg.org/download.html) and add it to your PATH
4. [Create a Spotify app](https://developer.spotify.com/dashboard/) and fill in `config/spotify_credentials.json`:
   ```json
   {
     "client_id": "YOUR_CLIENT_ID",
     "client_secret": "YOUR_CLIENT_SECRET"
   }
   ```

## Usage
- Run the app:
  ```bash
  python main.py
  ```
- Or double-click `main.py` (Windows/Mac)

All downloads are saved to the `downloads/` folder. 