
import yt_dlp
import json
import os
import hashlib 

class SyncBeats:
    def __init__(self, playlist_url):
        self.playlist_config_file_path = 'config/Playlistconfig.json'
        self.playlist_config_file_path_yt = 'config/PlaylistconfigYT.json'
        self.playlist_url = playlist_url
        self.ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',  # Save file with video title # hard coded needds to be fixed later
            # hard coded needs to be fixed later
            'ffmpeg_location': r'C:\Users\admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.0.2-full_build\bin'
        }
        self.syncPlaylist(self.playlist_config_file_path, self.playlist_config_file_path_yt)
        
        
    def download(self, video_url, download_path, format = "audio"):
        self.ydl_opts['outtmpl'] = os.path.join(download_path, '%(title)s.%(ext)s')
        
        if format == "audio":
            self.ydl_opts['format'] = 'bestaudio/best' # Download the best audio quality
            self.ydl_opts['postprocessors'] = [{  # Post-processing steps
                'key': 'FFmpegExtractAudio',  # Extract audio from video
                'preferredcodec': 'mp3',  # Convert audio to MP3 format
                'preferredquality': '192',  # Set the audio quality
            }]
        
        elif format == "video": 
            self.ydl_opts['format'] = 'best' 
        
        else: 
            print(format)
            print("Incorrect format enter audio or video")
            exit()
        # Download the video and convert to MP3
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            ydl.download([video_url])

    def save_playlist_info(self, fileName):
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            # Extract info from ytplaylist using yt_dlp
            info = ydl.extract_info(self.playlist_url, download=False)
            info = self.filter_titles_and_ids(info)
            # saving to file
            with open(fileName, 'w') as f:
                json.dump(info, f, indent=4)
    
    def filter_titles_and_ids(self, playlist_info):
    # Extract the title and URL of each video in the playlist
        filtered_info = {
            'PlaylistTitle': playlist_info.get('title'),
            'playlistId': playlist_info.get('id'),
            'videos': [
                {
                    'title': entry['title'], 
                    'id': entry.get('id', None)
                }
                for entry in playlist_info.get('entries', [])
            ]
        }
        filtered_info['videos'] = sorted(filtered_info['videos'], key=lambda x: x['title'])
    
        return filtered_info
    
    def hashPlaylist(self, file_path):
        # Create a SHA-256 hash object
        sha256 = hashlib.sha256()

        # Open the file and read its content
        with open(file_path, 'r', encoding='utf-8') as file:
            # Read the content of the file
            file_content = file.read()

            # Update the hash object with the bytes of the text
            sha256.update(file_content.encode('utf-8'))

        # Get the hexadecimal representation of the hash
        hash_hex = sha256.hexdigest()

        return hash_hex
    
    def syncPlaylist(self, sync_file_path, sync_file_path_yt):     
        if not os.path.exists(sync_file_path):
            #saving playlist info 
            self.save_playlist_info(sync_file_path)
    
            with open(sync_file_path, 'r') as file:
                fp = json.load(file)
                title = fp['PlaylistTitle']
                
                if not os.path.exists(title):
                    #makign dir by playlist title
                    os.mkdir(title)
                
                # iterating over config file and downloading each video using id 
                for video in fp.get('videos', []):
                    video_url = f'https://www.youtube.com/watch?v={video["id"]}'
                    self.download(video_url, download_path = title, format = 'audio')
                    
                return # return after downloading all video 
        
        #sync yt current playlist info
        self.save_playlist_info(sync_file_path_yt)
        if self.hashPlaylist(sync_file_path) != self.hashPlaylist(sync_file_path_yt): 
            with open(sync_file_path, 'r') as file1, open(sync_file_path_yt, 'r') as file2: 
                title = fp1['PlaylistTitle']
                fp1, fp2 = json.open(file1), json.open(file2)
                fp1_videos = {video['id'] for video in fp1['videos']}
                fp2_videos = {video['id'] for video in fp2['videos']}
                
                not_synced_videos = fp2_videos - fp1_videos
                
                for video_id in not_synced_videos: 
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    self.download(video_url, title)
                    
                
        

 
url = 'https://youtube.com/playlist?list=PLAU44P-DKz39QYgl7VW4NGgYLLlIF-Unc&si=bL8FExaIPqkVdxNP'  

Download = SyncBeats(url)