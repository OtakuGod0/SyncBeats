from googleapiclient.discovery import build
import sys; sys.path.append('.') # appending root directory
import os
from utils.download_yt import download
import re
from config.api import youtube_api as api_key # youtube api 
from config.FTPServerConfig import *
from config.config import default_format
import json

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


def getSyncDetails(): 
    try: 
        with open('config/sync_details.json', 'r') as fp: 
            sync_details = json.load(fp)
    # handling no config file
    except FileNotFoundError: 
        with open('config/sync_details.json', 'w') as fp: 
            json.dump({}, fp, indent=4)
            
    # getting playlist and sync directory path from user if not in config file
    if 'sync_playlist_id' not in sync_details.keys(): 
        sync_details['sync_playlist_id'] = input("Enter playlist id to sync: ")
    
    if 'sync_directory_path' not in sync_details.keys(): 
        sync_details['sync_directory_path'] = input("Enter directory path to sync youtube video: ")
        
    if 'sync_mobile_directory_path' not in sync_details.keys(): 
        sync_details['sync_mobile_directory_path'] = input("Enter Mobile sync directory: ")
    
    # saving configuration 
    with open('config/sync_details.json', 'w') as fp: 
        json.dump(sync_details, fp)
        
    return sync_details['sync_playlist_id'], sync_details['sync_directory_path'], sync_details['sync_mobile_directory_path']