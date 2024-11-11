from utils.sync import YTLocalMobileSync
from utils.global_utils import getSyncDetails

if __name__ == '__main__': 
    # syncing playlist every min
    sync_playlist_id, sync_directory_path, sync_mobile_directory_path = getSyncDetails()
    
    YTLocalMobileSync(sync_playlist_id, sync_directory_path, sync_mobile_directory_path)
     