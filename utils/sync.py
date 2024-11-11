from googleapiclient.discovery import build
import sys; sys.path.append('.') # appending root directory
import os
from utils.download_yt import download
import argparse
from config.api import youtube_api as api_key # youtube api 
import ftplib
from config.FTPServerConfig import *
from utils.mobile_transfer import upload_to_mobile
import time
from config.config import default_format
from utils.global_utils import normalize_title, getYTVideos, getLocalMusics

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