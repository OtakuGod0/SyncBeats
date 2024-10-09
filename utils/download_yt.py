import yt_dlp 
import os 
import argparse

def download(urls, download_path, format='video', playlist = False):
    if not isinstance(urls, list): 
        urls = [urls] # changing to list if not a list
        
    for url in urls: 
        # Setting up options for downloading
        ydl_opts = {
            'quiet': True
        }
        
        # playlist download
        if playlist: 
            ydl_opts['noplaylist'] = False
        
        # expanding the filepath if ~ provided in input_file
        download_path = os.path.abspath(os.path.expanduser(download_path))
        ydl_opts['outtmpl'] = os.path.join(download_path, '%(title)s.%(ext)s')

    
        if format == "audio":
            ydl_opts['format'] = 'bestaudio/best'  # Download the best audio quality
            ydl_opts['postprocessors'] = [{  # Post-processing steps
                'key': 'FFmpegExtractAudio',  # Extract audio from video
                'preferredcodec': 'mp3',  # Convert audio to MP3 format
                'preferredquality': '192',  # Set the audio quality
            }]

        elif format == "video":
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best'

        else:
            print(f"Incorrect format: {format}. Enter 'audio' or 'video'.")
            exit()
                
        # downloading video 
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try: 
                ydl.download([url])        

            except yt_dlp.utils.DownloadError:
                print("Best video quality not available, downloading any available format.")
                
                # Fallback to any available format if best quality is not available
                ydl_opts['format'] = 'worst' 
                
                # downloading 
                ydl.download([url])
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    # arguments
    parser.add_argument('url', nargs = '+', help = 'url of youtube video')
    parser.add_argument('-o', '--download_path', default = '.', help = 'Download location of video')
    parser.add_argument('-f', '--format', default = 'video', help = 'Format of yt_video')
    
    # parsing arguments
    args = parser.parse_args()
    
    download(args.url, args.download_path, format = args.format) # unpacking and passing key value pair
