import argparse
import os
import time
import datetime
import shutil

#Default values 
DEFAULT_SOURCE_FOLDER_PATH = './source_folder'
DEFAULT_REPLICA_FOLDER_PATH = './replica_folder'
DEFAULT_LOG_FILE_FOLDER_PATH = './log_folder'
DEFAULT_SYNC_INTERVAL = 10 #SECONDS

#Values for type of log messages
INFO = "INFO"
OKAY = "OKAY"
ERROR = "ERROR"
CREATED = "CREATED"
DELETED = "DELETED"
UPDATED = "UPDATED"

def get_command_line_arguments():
    """
    Parses command line arguments 

    Returns:
        argparse.Namespace: An object containing the parsed command line arguments.
    """
    #Creates parser instance and adds program name and description
    parser = argparse.ArgumentParser(description="""This script guarantees a one-way periodic synchronization
                between a source and a replica folder. It also logs file creation, copying, and removal operations 
                to a file and to the console output. The user can choose the paths of the two folders and 
                the log file, as well as the synchronization interval time.""")
    
    #Add arguments
    parser.add_argument('-sf', '--source_folder', default=DEFAULT_SOURCE_FOLDER_PATH, help='Path to Source folder path (default value: %(default)s)', metavar='')
    parser.add_argument('-rf', '--replica_folder', default=DEFAULT_REPLICA_FOLDER_PATH, help='Replica folder path (default value: %(default)s)', metavar='')
    parser.add_argument('-lf', '--log_folder', default=DEFAULT_LOG_FILE_FOLDER_PATH, help='Log folder path (default value: %(default)s)', metavar='')
    parser.add_argument('-si', '--sync_interval', type=int, default=DEFAULT_SYNC_INTERVAL, help='Synchronization interval time in seconds (default value: %(default)s)', metavar='')    
    
    # Parse the arguments
    return parser.parse_args()

def log_message(msg_text, msg_type, file_path=None):
    """
    Logs a message to the console and optionally to a file.

    Args:
        msg_text (str): The text of the message to log.
        msg_type (str): The type of the message (e.g., INFO, ERROR, OKAY).
        file_path (str, optional): The path to the log file. If provided, the message is also written to the file.
    """
    msg = f'[{datetime.datetime.now()}] {msg_type:<7} - {msg_text}'
    print(msg)
    
    if file_path is not None: #log to file if a file_path is given
        with open(file_path, "a") as file:
            file.write(msg +'\n')  

def check_folder(folder_path):
    """
    Checks if a folder exists and has read/write permissions. Prompts the user to create the folder if it doesn't exist.

    Args:
        folder_path (str): The path to the folder to check.

    Returns:
        tuple: A tuple containing:
            - error (str or None): A string if an error occurred, None otherwise.
            - folder_created (bool): True if the folder was created, False otherwise.
    """
    error = None
    folder_created = False
    
    if not os.path.exists(folder_path): #Check if folder exists        
        response = input(f"Folder '{folder_path}' does not exist. Do you want to create it? Press 'y' if yes or any other key to exit program: ").strip().lower()
        if response == 'y':
            try: 
                os.makedirs(folder_path) #create folder
                folder_created = True
            except OSError:
                error = f'Failed to create folder {folder_path}. Exiting...'   
        else:
            error =f'Folder {folder_path} does not exist and user declined creation. Exiting...'
    elif not os.access(folder_path, os.R_OK | os.W_OK): #check folder permissions
        error = f'Folder {folder_path} does not have read and writing permissions. Exiting...'
        
    return error, folder_created 

def check_folders_and_log(folder_path, folder_type, log_file_path=None):
    """
    Checks if a folder exists, has read/write permissions, and logs the result.

    Args:
        folder_path (str): The path to the folder to check.
        folder_type (str): The type of folder (e.g., 'Source', 'Replica', 'Log').
        log_file_path (str, optional): The path to the log file. If provided, log messages are written to the file.

    Returns:
        bool: True if the folder exists and has necessary permissions, False otherwise.
    """
    error, folder_created = check_folder(folder_path)
    if error is None:
        if folder_created:
            log_message(f'{folder_type} folder was created: {folder_path}', CREATED, log_file_path)
        log_message(f'{folder_type} folder exists and has necessary permissions: {folder_path}', OKAY, log_file_path)
        return True
    else:
        log_message(error, ERROR, log_file_path)
        return False

def create_log_file(log_folder_path):
    """
    Creates the log file in the specified folder.

    Args:
        log_folder_path (str): The path to the folder where the log file should be created.

    Returns:
        str: The path to the created log file, or None if an error occurred.
    """
    if check_folders_and_log(log_folder_path, 'Log', log_file_path=None): #log_file does not yet exists 
        log_filename = f'{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_sync_folders_log.txt'
        log_file_path = os.path.join(log_folder_path, log_filename)
        open(log_file_path, 'w').close() #Create file
        log_message(f'Log file was created: {log_file_path}', CREATED, log_file_path) 
    else:
        log_file_path = None        
    
    return log_file_path          

def get_all_files_and_folders(base_path):
    """
    Gets all files and folders within a given directory.

    Args:
        base_path (str): The path to the directory.

    Returns:
        tuple: A tuple containing two sets:
            - all_files (set): A set of relative paths to all files.
            - all_folders (set): A set of relative paths to all folders.
    """
    all_files = set()
    all_folders = set()
    
    for dirpath, dirnames, filenames in os.walk(base_path, topdown=False):
        for file in filenames:
            file_path = os.path.relpath(os.path.join(dirpath, file), base_path)
            all_files.add(file_path)
        
        for folder in dirnames:            
            folder_path = os.path.relpath(os.path.join(dirpath, folder), base_path)
            all_folders.add(folder_path)
            
    return all_files, all_folders

def delete_files(all_folders, all_files, path, log_file_path):
    """
    Deletes files and folders from the given path and logs the deletions.

    Args:
        all_folders (set): Set of folder paths to be deleted.
        all_files (set): Set of file paths to be deleted.
        path (str): Path where the files and folders are located.
        log_file_path (str): Path to the log file for logging deletions.
    """
    deleted_items = set()
    
    for folder_to_delete in sorted(all_folders, key=lambda x: x.count(os.path.sep)): #Sort to guarantee top to bottom order
        if folder_to_delete not in deleted_items: #check that folder was not already deleted by deletion of top folder
            folder_path = os.path.join(path, folder_to_delete)
            try:            
                shutil.rmtree(folder_path)
                for item in all_folders | all_files:
                    if folder_to_delete in item:                        
                        item_path = os.path.join(path, item)
                        deleted_items.add(item)
                        log_message(f'{item_path}', DELETED, log_file_path)
                        
            except OSError:
                log_message(f'{folder_path} could not be deleted. Trying again next synchronization', ERROR, log_file_path)
    
    for file_to_delete in all_files:
        if file_to_delete not in deleted_items: #check that file was not already deleted by deletion of top folder
            file_path = os.path.join(path, file_to_delete)
            try:
                os.remove(file_path)
                log_message(f'{file_path}', DELETED, log_file_path)
            except OSError:
                log_message(f'{file_path} could not be deleted. Trying again next synchronization', ERROR, log_file_path)
    
    

def create_files(all_folders, all_files, source_path, destination_path, log_file_path):  
    """
    Creates files and folders from the source path to the destination path and logs the creations.

    Args:
        all_folders (set): Set of folder paths to be created.
        all_files (set): Set of file paths to be created.
        source_path (str): Source path for the files and folders.
        destination_path (str): Destination path where items will be created.
        log_file_path (str): Path to the log file for logging creations.
    """
    created_items = set()
    
    for folder_to_create in sorted(all_folders, key=lambda x: x.count(os.path.sep)): #Sort to guarantee top to bottom order
        if folder_to_create not in created_items: #check that folder was not already created by copy of top folder
            source_folder_path = os.path.join(source_path, folder_to_create)
            destination_folder_path = os.path.join(destination_path, folder_to_create)
            try:            
                shutil.copytree(source_folder_path, destination_folder_path)
                for item in all_folders | all_files:
                    if folder_to_create in item:
                        created_items.add(item)                        
                        item_path = os.path.join(destination_path, item)
                        log_message(f'{item_path}', CREATED, log_file_path)
                        
            except OSError:
                log_message(f'{destination_folder_path} could not be created. Trying again next synchronization', ERROR, log_file_path)
    
    for file_to_create in all_files:
        if file_to_create not in created_items:
            source_file_path = os.path.join(source_path, file_to_create)
            destination_file_path = os.path.join(destination_path, file_to_create)
            try:
                shutil.copy2(source_file_path, destination_file_path) 
                log_message(f'{destination_file_path}', CREATED, log_file_path)
            except OSError:
                log_message(f'{destination_file_path} could not be created. Trying again next synchronization', ERROR, log_file_path)

def update_files(all_files, source_path, destination_path, log_file_path):        
    """
    Updates files in the destination path if they differ from the source and logs the updates.

    Args:
        all_files (set): Set of file paths to be updated.
        source_path (str): Source path for the files.
        destination_path (str): Destination path where the files will be updated.
        log_file_path (str): Path to the log file for logging updates.
    """
    for file_to_update in all_files:      
        source_file_path = os.path.join(source_path, file_to_update)
        destination_file_path = os.path.join(destination_path, file_to_update) 
                
        modified_date_source = os.path.getmtime(source_file_path)
        modified_date_destination = os.path.getmtime(destination_file_path)
        
        if modified_date_destination!=modified_date_source:  #check if file was altered    
            try:
                shutil.copy2(source_file_path, destination_file_path) 
                log_message(f'{destination_file_path}', UPDATED, log_file_path)
            except OSError:
                log_message(f'{destination_file_path} could not be updated. Trying again next synchronization', ERROR, log_file_path)


def sync_folders(source_path, replica_path, log_file_path):
    """
    Synchronizes the contents of the source folder with the replica folder.

    This function compares the files and folders in the source and replica folders and performs the following actions:
    - Deletes files and folders in the replica folder that are not present in the source folder.
    - Creates files and folders in the replica folder that are present in the source folder but not in the replica folder.
    - Updates files in the replica folder if they differ from the corresponding files in the source folder.
    - Logs all synchronization actions to the specified log file.

    Args:
        source_path (str): The path to the source folder.
        replica_path (str): The path to the replica folder.
        log_file_path (str): The path to the log file for logging synchronization actions.

    Returns:
        bool: True if the synchronization was successful, False if an error occurred (e.g., log file or folders were deleted).
    """
    if not(os.path.exists(os.path.dirname(log_file_path)) and os.path.exists(log_file_path) and os.path.exists(source_path) and os.path.exists(replica_path)):
        return False
    
    source_files, source_folders = get_all_files_and_folders(source_path)
    replica_files, replica_folders = get_all_files_and_folders(replica_path)
    
    deleted_files = replica_files - source_files 
    deleted_folders = replica_folders - source_folders
    created_files = source_files - replica_files
    created_folders = source_folders - replica_folders
    common_files = source_files.intersection(replica_files) 
        
    delete_files(deleted_folders, deleted_files, replica_path, log_file_path)
    create_files(created_folders, created_files, source_path, replica_path, log_file_path)
    update_files(common_files, source_path, replica_path, log_file_path)
    
    return True   
    
def main():
    """
    Main function of the folder synchronization script.

    It parses command line arguments, checks the existence and permissions of the 
    source, replica, and log folders, and then enters the main synchronization loop.
    """
    args = get_command_line_arguments()
    
    log_file_path = create_log_file(args.log_folder) 
    
    if log_file_path==None: #log source not ok, program will end
        return
    
    if not check_folders_and_log(args.source_folder, 'Source', log_file_path):
        return
    
    if not check_folders_and_log(args.replica_folder, 'Replica', log_file_path):
        return    
          
    log_message('All given folders exist and have necessary permissions.', OKAY, log_file_path)
    log_message(f'Starting synchronization with intervals of {args.sync_interval} seconds', INFO, log_file_path)
    
    try:
        while(True):
            log_message('Started synchronization', INFO, log_file_path)
            if not sync_folders(args.source_folder, args.replica_folder, log_file_path):
                log_message('Folders or log file were deleted. Exiting...', ERROR)
                return
            log_message('Finished synchronization', INFO, log_file_path)
            time.sleep(args.sync_interval)
       
    except KeyboardInterrupt:
        log_message('Synchronization interrupted by user. Exiting...', INFO, log_file_path)

if __name__ == "__main__":
    main()