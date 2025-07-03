import os
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, ID3NoHeaderError

def check_metadata(file_path):
    try:
        # Try to load ID3 tags
        audio = ID3(file_path)
        if audio:
            print(f"File: {os.path.basename(file_path)}")
            print(f"  Has ID3 tags: {len(audio)} tags")
            for key in audio.keys():
                print(f"    {key}: {audio[key]}")
            print()
            return True
        else:
            print(f"File: {os.path.basename(file_path)} - No ID3 tags found")
            return False
    except ID3NoHeaderError:
        print(f"File: {os.path.basename(file_path)} - No ID3 header")
        return False
    except Exception as e:
        print(f"File: {os.path.basename(file_path)} - Error: {e}")
        return False

# Check the specific file
downloads_dir = "MusicDL/downloads"
target_file = "＂Di Bale na＂ available sa sa spotify!! #shorts #indieartist #indierock.mp3"
file_path = os.path.join(downloads_dir, target_file)

if os.path.exists(file_path):
    print(f"Checking metadata for: {target_file}")
    print("=" * 50)
    check_metadata(file_path)
else:
    print(f"File not found: {target_file}")
    
    # List all files to find similar ones
    print("\nLooking for similar files:")
    for file in os.listdir(downloads_dir):
        if "di bale" in file.lower():
            print(f"Found: {file}")
            check_metadata(os.path.join(downloads_dir, file)) 