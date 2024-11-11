import time
from multiprocessing import Process, Queue
from rich.columns import Columns
from rich.live import Live
from rich.panel import Panel
from rich.console import Console
import random

def left_worker(queue, panel_name): 
    i = 0
    while True: 
        queue.put((f'Working left {i}', panel_name))
        i += 1  # Increment counter for updates
        time.sleep(random.uniform(0, 1))

def right_worker(queue, panel_name): 
    i = 0
    while True: 
        queue.put((f'Working right {i}', panel_name))
        i += 1  # Increment counter for updates
        time.sleep(random.uniform(0, 1))

def main(): 
    queue = Queue()
    console = Console()
    
    panels = {
        "left_panel": Panel("waiting", title="Left Panel", border_style = 'cyan'),
        "right_panel": Panel("waiting", title="Right Panel", border_style='magenta')
    }
    
    left_process = Process(target=left_worker, args=(queue, 'left_panel'))
    right_process = Process(target=right_worker, args=(queue, 'right_panel'))  # Fixed typo here
    
    left_process.start()
    right_process.start()
    
    with Live(Columns([panels["left_panel"], panels["right_panel"]], expand=True), console=console, refresh_per_second=4) as live:
        while True:
            msg, panel_name = queue.get()  # Continuously get messages from queue
            # Update the corresponding panel with the new message
            panels[panel_name] = Panel(msg, title="Left Panel" if panel_name == "left_panel" else "Right Panel", border_style = 'cyan' if panel_name == 'left_panel' else 'magenta')
            
            # Refresh the display with updated panels
            live.update(Columns([panels["left_panel"], panels["right_panel"]], expand=True))

if __name__ == '__main__': 
    main()
