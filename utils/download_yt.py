import yt_dlp 
import os 
import argparse
from config.config import default_format

import os
import yt_dlp

def download(urls, download_path, format=default_format, playlist=False):
    if not isinstance(urls, list): 
        urls = [urls]  # Convert to list if not already a list

    video_titles = []  # List to store video titles if downloading videos
    file_extensions = []  # List to store file extensions

    for url in urls: 
        # Setting up options for downloading
        ydl_opts = {
            'quiet': True,
            'outtmpl': os.path.join(os.path.abspath(os.path.expanduser(download_path)), '%(title)s.%(ext)s')
        }

        # Playlist download option
        if playlist: 
            ydl_opts['noplaylist'] = False

        # Setting format options based on input
        if format == "audio":
            ydl_opts['format'] = 'bestaudio/best'  # Download the best audio quality
            ydl_opts['postprocessors'] = [{  # Post-processing steps
                'key': 'FFmpegExtractAudio',  # Extract audio from video
                'preferredcodec': 'mp3',  # Convert audio to MP3 format
                'preferredquality': '192',  # Set the audio quality
            }]
        elif format == "video":
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best'
        else:
            print(f"Incorrect format: {format}. Enter 'audio' or 'video'.")
            return None

        # Downloading video 
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Extract information before downloading
                info_dict = ydl.extract_info(url, download=True)
                
                # Check if the URL is a playlist
                if 'entries' in info_dict:
                    return None  # Return None for playlists
                
                # If it's a single video, get the title and extension
                title = info_dict.get('title', 'No title found')  # Get title
                extension = info_dict.get('ext', 'unknown')  # Get file extension
                
                video_titles.append(title)  # Append the title to the list
                file_extensions.append(extension)  # Append the extension to the list
                
            except yt_dlp.utils.DownloadError:
                print("Best video quality not available, downloading any available format.")
                
                # Fallback to any available format if best quality is not available
                ydl_opts['format'] = 'worst'
                
                # Downloading 
                info_dict = ydl.extract_info(url, download=True)
                title = info_dict.get('title', 'No title found')  # Get title
                extension = info_dict.get('ext', 'unknown')  # Get file extension
                
                video_titles.append(title)  # Append the title to the list
                file_extensions.append(extension)  # Append the extension to the list

    # handling file_extension not changing to mp3 when audio format is given 
    if default_format == 'audio': 
        file_extensions[0] = 'mp3'
    
    # Return titles and extensions of downloaded videos
    return (video_titles[0], file_extensions[0]) if len(video_titles) > 0 else None

            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    # arguments
    parser.add_argument('url', nargs = '+', help = 'url of youtube video')
    parser.add_argument('-o', '--download_path', default = '.', help = 'Download location of video')
    parser.add_argument('-f', '--format', default = 'video', help = 'Format of yt_video')
    
    # parsing arguments
    args = parser.parse_args()
    
    download(args.url, args.download_path, format = args.format) # unpacking and passing key value pair
