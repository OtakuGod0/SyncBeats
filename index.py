
import yt_dlp
import json
import os
import hashlib 

class SyncBeats:
    def __init__(self, playlist_url, download_path):
        self.playlist_url = playlist_url
        self.download_path = download_path
        
        # Making the Download path if not exists 
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        
        self.ydl_opts = {
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),  # Save file with video title # hard coded needds to be fixed later
            'noplaylist': False,  # Process the entire playlist
            # hard coded needs to be fixed later
            'ffmpeg_location': r'C:\Users\admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.0.2-full_build\bin'
        }
        
    def download(self, format = "audio"):
        if format == "audio":
            self.ydl_opts['format'] = 'bestaudio/best' # Download the best audio quality
            self.ydl_opts['postprocessors'] = [{  # Post-processing steps
                'key': 'FFmpegExtractAudio',  # Extract audio from video
                'preferredcodec': 'mp3',  # Convert audio to MP3 format
                'preferredquality': '192',  # Set the audio quality
            }]
        
        if format == "video": 
            self.ydl_opts['format'] = 'best' 
        
        else: 
            print("Incorrect format enter audio or video")
            exit()
        # Download the video and convert to MP3
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            ydl.download([self.playlist_url])

    def save_playlist_info(self, fileName = "config/output.json"):
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            # Extract info from ytplaylist using yt_dlp
            info = ydl.extract_info(self.playlist_url, download=False)
            
            # saving to file
            with open(fileName, 'w') as f:
                json.dump(info, f, indent=4)
    
    def hashPlaylist(self, file):
        # Create a SHA-256 hash object
        sha256 = hashlib.sha256()
        
        # Update the hash object with the bytes of the text
        sha256.update(file.encode('utf-8'))
        
        # Get the hexadecimal representation of the hash
        hash_hex = sha256.hexdigest()
        
        return hash_hex

 
url = 'https://youtube.com/playlist?list=PLAU44P-DKz39QYgl7VW4NGgYLLlIF-Unc&si=bL8FExaIPqkVdxNP'  
downloadPath = 'Beats'             
                
Download = SyncBeats(url, downloadPath)
Download.download()