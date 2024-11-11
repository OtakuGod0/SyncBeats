from rich.progress import Progress
import yt_dlp

# Initialize the rich progress bar
progress = Progress()

url = "https://www.youtube.com/watch?v=0bfk90rWV9U&list=RDat93FMsH3fY&index=2"

def progress_hook(d):
    if d['status'] == 'downloading':
        task_id = d['info_dict'].get('task_id')  # Unique task ID for each download
        if task_id:
            progress.update(task_id, completed=d['downloaded_bytes'], total=d.get('total_bytes', 0))
    elif d['status'] == 'finished':
        print("Download complete!")

# yt-dlp options with progress hook
ydl_opts = {
    'format': 'best',
    'noplaylist': True,
    'quiet': True,
    'progress_hooks': [progress_hook],
}

# Use yt-dlp with the custom progress bar
with progress:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        task_id = progress.add_task(f'{info['title']}\n', total=info.get('filesize', 0))
        info['task_id'] = task_id  # Attach task ID for use in the hook
        ydl.download([url])
        print(task_id)