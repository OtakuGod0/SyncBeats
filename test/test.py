import yt_dlp
import json

def get_video_info(url):
    # Configure yt-dlp options
    ydl_opts = {
        'format': 'best',  # Specify the format of the video to download, 'best' will get the highest quality available
        'noplaylist': True,  # Only download the video, not the playlist
        'quiet': True,  # Suppress output except for errors
        'dump_single_json': True  # Output video information in JSON format
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract video information
        video_info = ydl.extract_info(url, download=False)
    
    return video_info

# Example usage
video_url = "https://youtu.be/J8Icb6cL0GU?list=PLMGtL2BtbQo76UvooT0ee-AaYD5mq8Kmc"
info = get_video_info(video_url)

# Print the extracted video information
with open("test.json", "w") as fp: 
    json.dump(info, fp)
