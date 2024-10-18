from googleapiclient.discovery import build
import sys; sys.path.append('.') # appending root directory
import os
from utils.download_yt import download
import argparse
import re
from config.api import youtube_api as api_key # youtube api 
import ftplib
from config.FTPServerConfig import *
from utils.mobile_transfer import upload_to_mobile
import time
from config.config import default_format

# Function to get videos from a playlist or from a video ID
def getYTVideos(youtube_id):
    """
    Get videos from a YouTube playlist or details from a video ID.

    Args:
        youtube_id (str): The YouTube playlist ID or video ID.

    Returns:
        dict: A dictionary of video titles and their corresponding links.
    """

    def get_id_type(youtube_id):
        # Check if the ID starts with 'PL' indicating a playlist ID
        if youtube_id.startswith('PL'):
            return 'playlist'
        
        # Check if the ID length is 11 characters and consists of alphanumeric characters
        elif len(youtube_id) == 11 and youtube_id.isalnum():
            return 'video'
        
        else:
            print("Invalid YouTube ID format.")
            return None

    # Determine if the ID is a playlist or video
    id_type = get_id_type(youtube_id)

    # Exit if ID type is not valid
    if id_type is None:
        print("Invalid ID provided.")
        return {}

    # Build the YouTube API client
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    videos = {}

    if id_type == 'playlist':
        request = youtube.playlistItems().list(
            part='snippet',
            playlistId=youtube_id,
            maxResults=50  # You can change this to fetch more results per request
        )
        
        while request:
            response = request.execute()

            for item in response['items']:
                video_id = item['snippet']['resourceId']['videoId']
                video_title = item['snippet']['title']
                video_link = f'https://www.youtube.com/watch?v={video_id}'
                
                videos.update({video_title: video_link})

            # Check if there's a next page
            request = youtube.playlistItems().list_next(request, response)

    elif id_type == 'video':
        # If it's a video ID, get its details
        request = youtube.videos().list(
            part='snippet',
            id=youtube_id
        )
        response = request.execute()

        if response.get('items'):
            video_id = response['items'][0]['id']
            video_title = response['items'][0]['snippet']['title']
            video_link = f'https://www.youtube.com/watch?v={video_id}'
            videos[video_title] = video_link
        else:
            print(f"Video ID {youtube_id} is not valid.")

    return videos

# validating youtube playlist or youtube video id 
def validate_youtube_playlist_or_video_id(youtube_id):
    """
    Validate a YouTube playlist ID or video ID.

    Args:
        youtube_id (str): The YouTube playlist ID or video ID to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    # Build the YouTube API client
    youtube = build("youtube", "v3", developerKey=api_key)

    try:
        # First, check if it is a valid playlist ID
        request = youtube.playlists().list(
            part="snippet",
            id=youtube_id
        )
        response = request.execute()

        # Check if any items were returned (valid playlist ID)
        if response.get("items"):
            print(f"Playlist ID {youtube_id} is valid.")
            return True
        else:
            print(f"Playlist ID {youtube_id} is not valid. Checking if it's a video ID...")

            # If it's not a valid playlist ID, check if it's a video ID
            request = youtube.videos().list(
                part="snippet",
                id=youtube_id
            )
            response = request.execute()

            # Check if any items were returned (valid video ID)
            if response.get("items"):
                print(f"Video ID {youtube_id} is valid.")
                return True
            else:
                print(f"Video ID {youtube_id} is not valid.")
                return False

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    
def getLocalMusics(sync_dict): 
    # initalize empty list to store musics name
    musics = []
    
    # Walk through the directory tree
    for _, _,  filenames in os.walk(sync_dict):
        # List files in the current directory
        for filename in filenames:
            musics.append(filename)
    
    return musics

# normalizing 
def normalize_title(titles): # to handle youtube api sending weird title str for special character bug
    def normalize(title): 
        # spliting any extensions if available 
        title = os.path.splitext(title)[0]
        # Convert to lowercase
        title = title.lower()
        # Replace special characters and extra spaces
        title = re.sub(r'[^\w\s]', '', title)  # Remove special characters
        title = re.sub(r'\s+', ' ', title)     # Replace multiple spaces with a single space
        title = title.strip()                   # Trim leading/trailing spaces
        return title
    
    # normalizing only keys if dict
    # empty dict to return 
    normalized_titles = {}
    if isinstance(titles, dict): 
        for key, value in titles.items(): 
            normalized_titles.update({normalize(key): value})
        
        return normalized_titles
    
    # if other then dict
    if not isinstance(titles, list): 
        titles = list(titles)

    for title in titles: 
        normalized_titles.update({normalize(title): title})
    
    return normalized_titles

def YTSync(playlist_id, sync_dict):  
    sync_dict = os.path.abspath(os.path.expanduser(sync_dict))
    if not os.path.exists(sync_dict): 
        os.makedirs(sync_dict)
        
    # Get the videos from the playlist
    YTvideos = normalize_title(getYTVideos(playlist_id))
    
    # Get local videos
    localMusics = normalize_title(getLocalMusics(sync_dict))
    
    # videos in remote only 
    remoteOnly = set(YTvideos.keys()) - set(localMusics.keys())

    for video in remoteOnly: 
        url = YTvideos[video]
        download(url, sync_dict)
        
    # bidirectional syncing
    localOnly = set(localMusics.keys()) - set(YTvideos.keys())
    
    for video in localOnly: 
        print("removing files from local which is not in remote")
        os.remove(os.path.join(sync_dict, localMusics[video]))
        
def mobileSync(localDict, mobileDict, ftp=None):
    localDict = os.path.abspath(os.path.expanduser(localDict))  # Expand path symbols

    # Connect to the FTP server if no connection is provided
    ftpNotGivenFlag = False
    if ftp is None:
        ftp = ftplib.FTP()
        try: 
            ftp.connect(mobile_ip, mobile_port)
            ftp.login(username, password)  # Login with username and password
            ftpNotGivenFlag = True
        except ftplib.all_errors as e: 
            print("Error connecting to FTP server (mobile):", e)        
            return  # Exit the function instead of the entire program

    # List directory contents (files and folders)
    try:
        remoteContents = ftp.nlst(mobileDict)  # List names in the remote directory
    except ftplib.error_perm as e:
        print(f"Error retrieving contents from {mobileDict}: {e}")
        return

    localContents = os.listdir(localDict)
    localContentsOnly = set(localContents) - set(remoteContents)

    for content in localContentsOnly: 
        upload_to_mobile(os.path.join(localDict, content), mobileDict)
    
    # bidirectional syncing
    remoteContentsOnly = set(remoteContents) - set(localContents)
    for content in remoteContentsOnly: 
        print(f"removing {content} in mobile for bidirectional sync")
        ftp.delete(os.path.join(mobileDict, content))

    # List only directories
    directories = [name for name in localContents if os.path.isdir(os.path.join(localDict, name))]

    # Syncing contents of nested directories 
    for directory in directories: 
        mobileSync(os.path.join(localDict, directory), os.path.join(mobileDict, directory), ftp)

    # Quit FTP connection if it was created within this function
    if ftpNotGivenFlag: 
        ftp.quit()

def YTLocalMobileSync(playlist_id, local_dict, mobile_dict): 
    local_dict = os.path.abspath(os.path.expanduser(local_dict))
    if not os.path.exists(local_dict): 
        os.makedirs(local_dict)
    
    # ftp object to connect to mobile (to avoid multiple connect)
    ftp = ftplib.FTP()
    try: 
        ftp.connect(mobile_ip, mobile_port)
        ftp.login(username, password)  # Login with username and password
        
        # ensuring if local and mobile dict are in sync first
        print("Ensuring mobile and local Dict are in sync")
        mobileSync(local_dict, mobile_dict, ftp)  
        
    except ftplib.all_errors as e: 
        print("Error connecting to FTP server (mobile): skipping mobile sync", e)        
    
    # constantly syncing (refreshing in each 60s)
    try: 
        while True: 
            # Get the videos from the playlist
            YTvideos = normalize_title(getYTVideos(playlist_id))
            
            # Get local videos
            localMusics = normalize_title(getLocalMusics(local_dict))
            
            # videos in remote only 
            remoteOnly = set(YTvideos.keys()) - set(localMusics.keys())

            for video in remoteOnly: 
                print(f"{video} added to playlist syncing into local and mobile")
                
                url = YTvideos[video]
                
                # downloading from yt and extracting title of video 
                title, ext = download(url, local_dict)
                
                # uploading to mobile
                upload_file = os.path.join(local_dict, f"{title}.{ext}") 
                
                try: 
                    print("uploading to mobile")
                    upload_to_mobile(upload_file, mobile_dict)
                except ftplib.all_errors as e: 
                    print("Error connecting to ftp server")
                    print("Skipping upload to mobile")
                    
            # bidirectional syncing
            localOnly = set(localMusics.keys()) - set(YTvideos.keys())
            
            for video in localOnly: 
                print(f"removing {video} from local which is not in remote")
                os.remove(os.path.join(local_dict, localMusics[video]))
                try: 
                    print(f"removing {video} from mobile which is not local")
                    ftp.delete(os.path.join(mobile_dict, localMusics[video]))
                except ftplib.all_errors: 
                    print(f"Error deleting {video} from mobile skipping it")
                

            # sleeping
            print("Playlist mobile and local are in sync")
            print("Sleeping for 1 min")
            time.sleep(60)
                
    except KeyboardInterrupt: 
        print("YT playlist, local and mobile sync stopped")
        exit(0)
            
if __name__ == "__main__": 
    parser = argparse.ArgumentParser()
    
    # arguments
    parser.add_argument('playlist_id', help = "id of playlist")
    parser.add_argument('sync_dict', help = 'Directory to be synced')
    parser.add_argument('mobileDict', help = 'Directory of mobile to sync')

    args = parser.parse_args()
    
    YTLocalMobileSync(args.playlist_id, args.sync_dict, args.mobileDict)