# MusicDL

> **🎵 The Ultimate Music Downloader & Player — Modern, Fast, and Beautiful! 🎶**

**MusicDL** is your all-in-one desktop solution for building your dream music library. Effortlessly download tracks, albums, and playlists from YouTube and Spotify with a single click. Enjoy a sleek, mobile-inspired interface, vibrant dark mode, and a powerful built-in player — all designed for music lovers, by music lovers.

- **Paste any link.** Instantly grab music from YouTube or Spotify — tracks, albums, or playlists.
- **Batch download.** Queue up your favorite songs and let MusicDL handle the rest.
- **Modern, beautiful GUI.** Experience a visually stunning, responsive app with smooth navigation, tooltips, and a sidebar for quick access.
- **Built-in player.** Play your downloads with a gorgeous, centered player bar, live progress, cover art, and volume control.
- **Smart history.** Search, play, open, or delete your music — all from a polished history page.
- **Automatic tagging.** Every download is tagged with title, artist, album, and cover art for a perfect library.
- **No command line.** Everything is point-and-click, with clear feedback and a delightful user experience.

> **Transform your music experience. Download, play, and organize — all in one place, with style.**

---

## Features
- **Download from YouTube & Spotify:** Paste any YouTube or Spotify link (track, album, playlist) and download music as high-quality MP3 (320kbps) or full video.
- **Batch Download:** Add multiple links to a queue and download them all at once.
- **Modern GUI:** Responsive, mobile-inspired interface with dark mode, tooltips, and a sidebar for easy navigation.
- **Music Player:** Built-in player with queue, seekable progress bar, volume control, and cover art display.
- **Download History:** View, search, play, open, or delete previously downloaded tracks.
- **Metadata Handling:** Automatically tags downloaded files with title, artist, album, and cover art. Robust against missing or blank metadata.
- **Duplicate Detection:** Prevents duplicate downloads using smart filename and metadata checks.
- **Custom Download Folder:** Choose where your music is saved.

---

## GUI Overview
- **Sidebar:** Quick navigation (Home, Download, Player, History, Settings, About).
- **Download Page:** Paste links, manage queue, and monitor download progress.
- **Player Page:** Play music with a modern, centered player panel, live progress bar, and volume slider.
- **History Page:** Search, play, open, or delete downloaded tracks.
- **Settings:** Switch between light/dark mode, set output format, and choose download folder.
- **About:** App info and developer credits.

---

## Backend Overview
- **YouTube Downloads:** Uses `yt-dlp` for fast, reliable downloads and audio extraction.
- **Spotify Downloads:** Uses `spotipy` to fetch track/album/playlist info, then finds and downloads matching audio from YouTube.
- **Metadata Tagging:** Uses `mutagen` and `eyed3` to tag files with cleaned, validated metadata and cover art.
- **Audio Formats:** Supports MP3, FLAC, M4A, OPUS, WAV, and more.
- **Utilities:** Includes scripts for metadata checking and YouTube search.

---

## Setup
1. **Install Python 3.8+**
2. **Install dependencies:**
   ```bash
   pip install -r MusicDL/requirements.txt
   ```
3. **Install [ffmpeg](https://ffmpeg.org/download.html)** and add it to your PATH (required for audio conversion).
4. **Create a Spotify app:**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - Create an app and copy your `client_id` and `client_secret`.
   - Create a file at `MusicDL/config/spotify_credentials.json` (not included for security) with:
     ```json
     {
       "client_id": "YOUR_CLIENT_ID",
       "client_secret": "YOUR_CLIENT_SECRET"
     }
     ```

---

## Usage
- **Run the app:**
  ```bash
  python MusicDL/main.py
  ```
  Or double-click `main.py` (Windows/Mac).
- **Download music:** Paste links on the Download page, add to queue, and click Download All.
- **Play music:** Use the Player page to play, seek, and manage your queue.
- **View history:** See all downloads, search, play, open, or delete files.
- **Settings:** Change theme, output format, or download folder.

All downloads are saved to the `MusicDL/downloads/` folder by default.

---

## Dependencies
- `yt-dlp` — YouTube downloads
- `spotipy` — Spotify API
- `rich` — Console output (for scripts)
- `mutagen`, `eyed3` — Audio metadata tagging
- `customtkinter` — Modern GUI
- `pillow` — Image handling (cover art)
- `pygame` — Audio playback

---

## Security & Credentials
- **Never share your `spotify_credentials.json`!** This file is in `.gitignore` and must be created manually.
- If you accidentally commit credentials, [revoke/rotate them in Spotify](https://developer.spotify.com/dashboard/) and follow git history cleaning steps.

---

## Troubleshooting
- **Missing ffmpeg:** Make sure `ffmpeg` is installed and in your PATH.
- **Spotify errors:** Check your credentials and playlist privacy.
- **No audio playback:** Ensure `pygame` is installed and your system supports audio output.
- **Metadata issues:** Use `check_metadata.py` to inspect tags in your downloaded files.

---

## Credits
- Developed by Danielle Aragon
- Inspired by modern mobile app design

---

## License
MIT License
