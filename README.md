# One way synchronization between two folders - Veeam test task

This repository contains my Python solution to the Veeam test task for the Junior Developer in QA position.

This test task consists of implementing a program, in Python or C#, that should guarantee a one-way synchronization between a source and a replica folder and shall meet the following requirements:
- After the synchronization content of the replica folder should be modified to exactly match content of the source folder;
- Synchronization should be performed periodically;
- File creation/copying/removal operations should be logged to a file and to the console output;
- Folder paths, synchronization interval and log file path should be provided using the command line arguments;

## Script Overview
The script ensures periodic, one-way synchronization between a source folder and a replica folder. It performs the following tasks:
-Removes files and folders in the replica folder that are no longer present in the source folder.
-Creates missing files and folders in the replica folder from the source folder.
-Updates files in the replica folder if they are different from the corresponding files in the source folder.
All operations are logged in both a log file (when possible) and to the console for traceability and monitoring.


## How to Run the Script
1.  **Clone the repository:**
2. **Run the script with command-line arguments:**
`-sf` or `--source_folder`: Path to the source folder. (Default: ./source_folder)
`-rf` or `--replica_folder`: Path to the replica folder. (Default: ./replica_folder)
`-lf` or `--log_folder`: Path to the log folder. (Default: ./log_folder)
`-si` or `--sync_interval`: Synchronization interval in seconds. (Default: 10 seconds)
   **Example:**
    ```bash
    python sync_folders.py -sf /home/user/my_source_folder -rf /home/user/my_replica_folder -lf /home/user/my_logs -si 20
    ```
    This will synchronize `/home/user/my_source_folder` with `/home/user/my_replica_folder` every `20` seconds and log the actions to `/home/user/my_logs`


## Logging

The log file logs 6 types of messages:

- INFO - Messages with general information (e.g. start of a synchronization).
- OKAY - Messages indicating that checks were successful (e.g. folder existence and permissions).
- ERROR - Messages indicating an error occurred (e.g. failure to copy a file).
- CREATED - Messages indicating that a file or folder was created in the replica folder.
- DELETED - Messages indicating that a file or folder was deleted from the replica folder.
- UPDATED - Messages indicating that a file in the replica folder was updated based on the source folder.