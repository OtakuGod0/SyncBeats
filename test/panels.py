from rich.panel import Panel
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
import sys; sys.path.append('.')
import os
from time import sleep
from threading import Thread, Lock
from queue import Queue
from utils.global_utils import normalize_title, getLocalMusics, getYTVideos, getSyncDetails
from utils.download_yt import download
from rich.progress import Progress
import yt_dlp
from concurrent.futures import ThreadPoolExecutor

# Thread-safe update queue and lock
update_queue = Queue()
layout_lock = Lock()
        
def update_left_panel(playlist_id, sync_dict): 
    sync_dict = os.path.abspath(os.path.expanduser(sync_dict))
    if not os.path.exists(sync_dict): 
        os.makedirs(sync_dict)
        
    while True: 
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
        # Get the videos from the playlist
        YTvideos = normalize_title(getYTVideos(playlist_id))
        
        # Get local videos
        localMusics = normalize_title(getLocalMusics(sync_dict))
        
        # videos in remote only 
        remoteOnly = set(YTvideos.keys()) - set(localMusics.keys())
        
        content = ''
        for i, item in enumerate(remoteOnly): 
            content += f'{i+1}. {item}\n'
        
        # Send update to the queue
        update_queue.put(('left', content))
        sleep(1)

def update_right_panel(urls, queue): 
    # yt-dlp options with progress hook
    ydl_opts = {
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'progress_hooks': [progress_hook],
    }
    
    def progress_hook(d):
        task_id = d['info_dict'].get('task_id')  # Unique task ID for each download
        if d['status'] == 'downloading':
            if task_id:
                queue.put(('right', task_id, 'downloading', d['title']))
        elif d['status'] == 'finished':
            queue.put(('right', task_id, 'finished', d['title']))
    
    def download(url): 
        with Progress() as progress: 
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                task_id = progress.add_task(f'{info['title']}\n', total=info.get('filesize', 0))
                info['task_id'] = task_id  # Attach task ID for use in the hook
                ydl.download([url])
        
    with ThreadPoolExecutor(max_workers=4) as executor: 
        futures = list(executor.map(download, urls))
        
        # wait for each thread to complete
        for future in futures: 
            future.result()
    
def main(): 
    layout = Layout()
    console = Console()
    
    layout.split_row(
        Layout(Panel('loading...'), name='left_column', ratio=1),
        Layout(Panel('loading...'), name='right_column', ratio=1)
    )
    
    # Getting sync details
    sync_playlist_id, sync_directory_path, _ = getSyncDetails()
    
    # Threads for updating panels
    left_thread = Thread(target=update_left_panel, args=(sync_playlist_id, sync_directory_path,))
    right_thread = Thread(target=update_right_panel)
    
    left_thread.start()
    right_thread.start()

    # empty array to store task_id 
    task_ids = []
    
    with Live(layout, console=console, refresh_per_second=10):
        with Progress() as progress: 
            while True:
                try: 
                    panel_type = update_queue.queue[0][0]
                    with layout_lock:
                        if panel_type == 'left':
                            _, content = update_queue.get()
                            # Create a Text object for handling overflow
                            text_content = Text(content, overflow="scroll")
                            # Create a Panel with the Text object as content
                            panel = Panel(text_content, border_style='magenta', title='Musics to Sync', expand=True, height=10)
                            layout['left_column'].update(panel)
                        else:
                            _, task_id, status, title = update_queue.get()
                            
                            if task_id not in task_ids: 
                                progress.add_task(title, total = None, status = status, task_id = task_id)
                                task_ids.append(task_id)
                            
                            progress.update(task_id, status = status)
                            
                            panel = Panel(text_content, title='Downloading Musics', border_style='cyan', expand=True, height=10)
                            layout['right_column'].update(panel)
                            
                    update_queue.task_done()
                except KeyboardInterrupt:
                    print("Exiting program...")
                    exit(1)

main()
