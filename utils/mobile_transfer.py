import ftplib
import sys; sys.path.append('.')  # appending root directory of project to import modules
from tqdm import tqdm
import os
import argparse
# importing FTP server details and file to upload
from config.FTPServerConfig import mobile_ip, mobile_port, username, password

def split_path_and_filename(input_path):
    input_file_path, input_file_name = os.path.split(input_path)
    
    # handling os.path.split() bug: returns file_path in input_file_name when no file name provided in input_path
    if not os.path.splitext(input_file_name)[1]: 
        input_path = input_path + '/'
    
    return os.path.split(input_path)

def handleDictTransfer(input_file, output_file, ftp, is_first=True):  # is_first: to make directory in remote for only first time of recursion
    # saving files in a directory (same name as input dict) in remote
    if is_first:
        output_file = os.path.join(output_file, os.path.split(input_file)[-1])
    
    # items in directory
    dict_items = os.listdir(input_file)
    
    # nested directories
    nested_directories = [dict for dict in dict_items if os.path.isdir(os.path.join(input_file, dict))]
    # handle each nested_directories 
    for nested_directory in nested_directories:
        nested_local_directory = os.path.join(input_file, nested_directory)
        nested_remote_directory = os.path.join(output_file, nested_directory)
        
        # creating nested directory in remote
        ensure_directory(ftp, nested_remote_directory)
        
        handleDictTransfer(nested_local_directory, nested_remote_directory, ftp, is_first=False)
    
    # handing files
    for item in dict_items:
        full_loc_local = os.path.join(input_file, item)
        full_loc_remote = os.path.join(output_file, item)
        if os.path.isfile(full_loc_local):
            try:
                upload_to_mobile(full_loc_local, full_loc_remote)
            except Exception as e:
                print(f"Error uploading {full_loc_local} to mobile")
                print(e)


def ensure_directory(ftp, remote_directory):
    # Split the directory into parts
    parts = remote_directory.strip('/').split('/')
    
    # Start with the root directory
    current_path = ''
    
    for part in parts:
        current_path += '/' + part  # Build the path incrementally
        try:
            # Try to change to the current path
            ftp.cwd(current_path)
        except ftplib.error_perm:
            # If it does not exist, create it
            print(f"Directory '{current_path}' does not exist. Creating it...")
            try:
                ftp.mkd(current_path)
                print(f"Directory '{current_path}' created successfully.")
            except ftplib.error_perm as e:
                print(f"Failed to create directory '{current_path}': {e}")


def prepareOutputFilePath(input_file, output_file):
    # changing to root directory for remote if not provided 
    if not output_file.startswith('/'):
        output_file = '/' + output_file
        
    input_file_name = str(split_path_and_filename(input_file)[1])  # Using the custom function here
    output_path, output_file_name = str(split_path_and_filename(output_file)[0]), str(split_path_and_filename(output_file)[1])  # Updated to use the custom function
            
    # giving name of input file if no name provided
    if not os.path.isfile(output_file): 
        output_file_name = input_file_name
    
    return output_path, output_file_name
    

def upload_to_mobile(input_files, output_file, mobile_ip = mobile_ip, mobile_port = mobile_port, username = username, password = password):
    # Check if the input is a string and convert it to a list
    if isinstance(input_files, str):
        input_files = [input_files]  # Convert string to a list    
        
    # uploading each input_file 
    for input_file in input_files:

        # expanding the filepath if ~ provided in input_file
        input_file = os.path.abspath(os.path.expanduser(input_file))

        # exiting early if input file doesn't exists
        if not os.path.exists(input_file): 
            print(f"Input file {input_file} doesn't exists")
            return 

        # Connect to the mobile FTP server
        with ftplib.FTP() as ftp:
            # Open a connection to the server
            try: 
                ftp.connect(mobile_ip, mobile_port)
                ftp.login(username, password)  # Login with username and password

            except ftplib.all_errors as e: 
                print("Error connecting to ftp server (mobile)")
                print(e)        
                return

            # handling if input file is directory
            if os.path.isdir(input_file): 
                print(f'{input_file} is a directory\n transferring content of directory to mobile')
                handleDictTransfer(input_file, output_file, ftp)
                return 

            # output location configuration
            output_path, output_file_name = prepareOutputFilePath(input_file, output_file)
            
            # Open the file in binary mode
            try: 
                with open(input_file, 'rb') as file:
                    # Get the total file size for progress tracking
                    total_size = os.path.getsize(input_file)

                    # Ensure the directory exists on the FTP server, creating one if necessary
                    ensure_directory(ftp, output_path)

                    # Create a tqdm progress bar
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=f'Uploading {os.path.basename(input_file)}') as pbar:
                        # Define a callback function to update the progress bar
                        def update_progress(block):
                            pbar.update(len(block))

                        # Upload the file with progress tracking
                        ftp.storbinary(f'STOR {output_path}/{output_file_name}', file, 1024, callback=update_progress)

                    print(f"File '{input_file}' uploaded successfully.")

            except FileNotFoundError: 
                print("Error opening input file")
                sys.exit(1)

if __name__ == '__main__': 
    parser = argparse.ArgumentParser()
    
    # input files
    parser.add_argument('input_files', nargs='+', help='List of input file paths')
    
    # remote path 
    parser.add_argument('-o', '--output', default='/', help='remote directory location')
    
    # Optional flag for verbosity
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output (default: False)')
    
    # remote configuration
    parser.add_argument('-m', '--mobile_ip', type=str, default=None, help='IP address of the mobile device')
    parser.add_argument('-P', '--mobile_port', type=int, default=None, help='Port of the mobile device')
    parser.add_argument('-u', '--username', type=str, default=None, help='Username for authentication')
    parser.add_argument('-p', '--password', type=str, default=None, help='Password for authentication')
    
    # processing arguments
    args = parser.parse_args()
    
    # Build a dictionary of arguments for upload_to_mobile function
    upload_args = {
        'input_files': args.input_files,
        'output_file': args.output
    }

    # Add non-None optional arguments
    if args.mobile_ip is not None:
        upload_args['mobile_ip'] = args.mobile_ip
    if args.mobile_port is not None:
        upload_args['mobile_port'] = args.mobile_port
    if args.username is not None:
        upload_args['username'] = args.username
    if args.password is not None:
        upload_args['password'] = args.password
    
    upload_to_mobile(**upload_args)