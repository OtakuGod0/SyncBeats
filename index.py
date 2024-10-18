import os
import platform
import sys
import json
from utils.sync import YTLocalMobileSync

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

def scheduleAtStartUp(): 
    # The path to the Python executable and the script to run
    python_executable = sys.executable

    # Get the path of the current script
    script_to_run = os.path.abspath(__file__)

    if platform.system() == 'Windows':
        # Windows Task Scheduler command
        task_name = "SyncBeats"

        # Check if the task exists
        check_task = os.system(f"schtasks /query /tn {task_name} >nul 2>&1")
        
        if check_task == 0:
            print(f"Task '{task_name}' already exists. No action needed.")
        else:
            # Create the task if it doesn't exist
            os.system(f"schtasks /create /tn {task_name} /tr \"{python_executable} {script_to_run}\" /sc onstart /rl highest /f")
            print(f"Task '{task_name}' has been scheduled to run {script_to_run} at startup on Windows.")

    elif platform.system() == 'Linux':
        # Linux cron job
        cron_job = f"@reboot {python_executable} {script_to_run}\n"

        # Check if the cron job already exists
        current_cron = os.popen('crontab -l').read()

        if cron_job.strip() in current_cron:
            print(f"Cron job for '{script_to_run}' already exists. No action needed.")
        else:
            # Add the cron job if it doesn't exist
            os.system(f"(crontab -l; echo '{cron_job}') | crontab -")
            print(f"Scheduled script '{script_to_run}' to run at startup using cron on Linux.")
    else:
        print("Unsupported operating system.")

if __name__ == '__main__': 
    print("Scheduling task at startup")
    scheduleAtStartUp()
    
    # syncing playlist every min
    sync_playlist_id, sync_directory_path, sync_mobile_directory_path = getSyncDetails()
    
    YTLocalMobileSync(sync_playlist_id, sync_directory_path, sync_mobile_directory_path)
     