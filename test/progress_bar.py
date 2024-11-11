from rich.progress import Progress
from time import sleep 

with Progress() as progress: 
    task = progress.add_task('test', total = None)
    
    while True: 
        progress.update(task, completed=None)
        sleep(1)