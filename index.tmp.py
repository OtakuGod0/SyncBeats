import yt_dlp
import json
import os
import hashlib

# Define global options
ydl_opts = {
    'outtmpl': '%(title)s.%(ext)s',  # Save file with video title
    'ffmpeg_location': r'C:\Users\admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.0.2-full_build\bin'
}

# Download function
def download(video_url, download_path, format="audio"):
    ydl_opts['outtmpl'] = os.path.join(download_path, '%(title)s.%(ext)s')

    if format == "audio":
        ydl_opts['format'] = 'bestaudio/best'  # Download the best audio quality
        ydl_opts['postprocessors'] = [{  # Post-processing steps
            'key': 'FFmpegExtractAudio',  # Extract audio from video
            'preferredcodec': 'mp3',  # Convert audio to MP3 format
            'preferredquality': '192',  # Set the audio quality
        }]
    elif format == "video":
        ydl_opts['format'] = 'bestvideo'
    else:
        print(f"Incorrect format: {format}. Enter 'audio' or 'video'.")
        exit()

    # Download the video
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

# Save playlist info
def save_playlist_info(playlist_url, file_name):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract info from the YouTube playlist
        info = ydl.extract_info(playlist_url, download=False)
        info = filter_titles_and_ids(info)
        # Save to file
        with open(file_name, 'w') as f:
            json.dump(info, f, indent=4)

# Filter titles and IDs
def filter_titles_and_ids(playlist_info):
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

# Create hash for playlist change check
def hash_playlist(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
        sha256.update(file_content.encode('utf-8'))

    return sha256.hexdigest()

# Synchronize the playlist
def sync_playlist(playlist_url, sync_file_path, sync_file_path_yt):
    if not os.path.exists(sync_file_path):
        save_playlist_info(playlist_url, sync_file_path)

        with open(sync_file_path, 'r') as file:
            fp = json.load(file)
            title = fp['PlaylistTitle']

            if not os.path.exists(title):
                os.mkdir(title)

            # Download each video using the ID
            for video in fp.get('videos', []):
                video_url = f'https://www.youtube.com/watch?v={video["id"]}'
                download(video_url, download_path=title, format='audio')
        return

    # Sync current playlist info
    save_playlist_info(playlist_url, sync_file_path_yt)

    if hash_playlist(sync_file_path) != hash_playlist(sync_file_path_yt):
        with open(sync_file_path, 'r') as file1, open(sync_file_path_yt, 'r') as file2:
            fp1 = json.load(file1)
            fp2 = json.load(file2)
            title = fp1['PlaylistTitle']

            fp1_videos = {video['id'] for video in fp1['videos']}
            fp2_videos = {video['id'] for video in fp2['videos']}

            not_synced_videos = fp2_videos - fp1_videos

            for video_id in not_synced_videos:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                download(video_url, title)

# Main function to execute the synchronization
def main():
    playlist_url = 'https://youtube.com/playlist?list=PLAU44P-DKz39QYgl7VW4NGgYLLlIF-Unc&si=bL8FExaIPqkVdxNP'
    sync_file_path = 'config/Playlistconfig.json'
    sync_file_path_yt = 'config/PlaylistconfigYT.json'
    
    sync_playlist(playlist_url, sync_file_path, sync_file_path_yt)

# Run the main function
if __name__ == '__main__':
    main()
