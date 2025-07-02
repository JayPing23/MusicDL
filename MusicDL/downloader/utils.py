import yt_dlp

def search_youtube(query):
    ydl_opts = {'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if info['entries']:
                return f"https://www.youtube.com/watch?v={info['entries'][0]['id']}"
        except Exception:
            return None
    return None 