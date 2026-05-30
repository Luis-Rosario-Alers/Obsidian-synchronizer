## Task 3 — Google Drive API wrapper file
- Brief: 
Engineering Brief: drive_client.py — Google Drive API Wrapper

Overview
Your task is to build drive_client.py, a self-contained wrapper class around the Google Drive API. Every other module in the project (uploader.py, puller.py) will talk to Google Drive exclusively through this file. No other module should import or call the Drive API directly.
Estimated time: 2–3 days.

Prerequisites
Before writing any code, complete the following setup steps:

Create a Google Cloud project at console.cloud.google.com.
Enable the Google Drive API for that project.
Create an OAuth 2.0 Client ID credential (Desktop App type) and download it as credentials.json into the project root.
Install the required libraries:

   pip install google-api-python-client google-auth-oauthlib

Class Interface
Create a single class called DriveClient. It should be initialized with the path to credentials.json and token.json, and all five methods below must be implemented exactly as specified — other modules will depend on these exact signatures.

authenticate()
Handles OAuth 2.0 login. On first run, opens a browser window for the user to log in and grant Drive access, then saves the resulting token to token.json. On all subsequent runs, loads the token from token.json directly without opening a browser. If the token is expired, refresh it automatically without user interaction.
This method must be called once before any other method is used. A good pattern is to call it inside __init__ so authentication is always guaranteed.

get_or_create_folder(name, parent_id) → str
Given a folder name and a parent folder ID, check whether a folder with that name already exists inside the parent on Drive. If it does, return its ID. If it does not, create it and return the new ID.
This is used to mirror the local vault's nested folder structure in Drive — the uploader calls this when it encounters a file inside a subdirectory that may not exist yet on Drive.

upload_file(local_path, drive_folder_id) → str
Upload a single local file to the specified Drive folder. If a file with the same name already exists in that folder, overwrite it in place (update its contents) rather than creating a duplicate. Return the Drive file ID.
The method must handle both cases cleanly:

File does not exist on Drive yet → create it.
File already exists on Drive → update it.


list_remote_files(drive_folder_id) → list[dict]
Return a flat list of every file inside the given Drive folder, including files in all subfolders. Each item in the list should be a dictionary with at least these keys:
python{
  "id": "drive-file-id",
  "name": "filename.md",
  "relative_path": "subfolder/filename.md",  # path relative to vault root
  "modified_time": "2025-05-29T10:42:00Z"    # ISO 8601 string
}
This is called by puller.py to compare remote files against the local vault.

download_file(drive_file_id, local_path)
Download a file by its Drive file ID and write it to local_path on disk. Create any intermediate directories in local_path if they do not already exist. Overwrite the local file if it is already present.

Error Handling
Every method must handle errors explicitly — do not let raw API exceptions bubble up uncaught. The following rules apply:

Wrap all API calls in try/except blocks.
Raise a custom DriveClientError exception (define it at the top of the file) with a human-readable message for any failure. This gives the rest of the codebase a single, predictable exception type to catch.
For network or quota errors specifically (HTTP 429, 500, 503), retry up to 3 times with an exponential backoff delay (1s, 2s, 4s) before raising.
Never silently swallow an exception — if a retry is exhausted, raise DriveClientError with the original error message included.


Logging
Use Python's logging module throughout — no bare print() calls. Log the following at the appropriate levels:
EventLevelSuccessful authenticationINFOToken refreshedINFOFile uploaded or updatedINFOFolder createdINFORetry attemptWARNINGFinal failure after retriesERROR

What Not to Do

Do not read from config.json inside this file. Accept all paths and IDs as method arguments or constructor parameters.
Do not implement any business logic (debouncing, backup creation, comparing timestamps). This file is purely a Drive API wrapper.
Do not hardcode any file paths, folder names, or credentials.


Acceptance Criteria
Before marking this task done, verify all of the following manually:

 authenticate() completes without a browser prompt on the second run.
 upload_file() creates a new file on Drive when it does not exist yet.
 upload_file() updates an existing file without creating a duplicate.
 list_remote_files() returns entries for files in nested subfolders, not just the top level.
 download_file() creates intermediate directories if they do not exist locally.
 Passing an invalid folder ID raises DriveClientError with a clear message.
 All log output uses logging, not print().

- What Claude proposed:  `drive_client.py` Google Drive API Wrapper file
- What I changed before approving: Some aspects of how the wrapper file would handle errors
- Verification: Created a test file that would upload a file to the specific Google Drive folder
- One thing I learned: it is pivitol to give the AI detailed context as it will sometimes assume what you want incorrectly.

## Task 4 — Add Configuration File Support
- Brief:
-  
```
Engineering Brief: config.json — Configuration File

Overview
Your task is to create config.json, the central configuration file for the sync tool, and wire it into main.py so that every module reads its settings from this single source. No module should have hardcoded paths, folder IDs, or tunable values — everything configurable must live in this file.
Estimated time: half a day.

The File
Create config.json in the project root with exactly the following fields:
json{
  "vault_path": "/absolute/path/to/your/obsidian/vault",
  "drive_folder_id": "your-google-drive-folder-id",
  "debounce_seconds": 1.5,
  "backup_on_overwrite": true,
  "pull_delete_local_extras": false
}

What Each Field Does
FieldTypeDescriptionvault_pathstringAbsolute path to the local Obsidian vault directorydrive_folder_idstringID of the root vault folder on Google Drive (taken from the folder's browser URL)debounce_secondsfloatHow long to wait after a file event before uploading, to avoid redundant uploads on rapid savesbackup_on_overwritebooleanIf true, a copy of any local file about to be overwritten during a pull is saved to .sync-backups/ firstpull_delete_local_extrasbooleanIf true, pull mode will delete local files that do not exist on Drive

Loading Config in main.py
Create a load_config() function in main.py that:

Opens and parses config.json using Python's json stdlib module.
Validates that all five required fields are present. If any are missing, exit immediately with a clear error message naming the missing field.
Validates that vault_path points to a directory that actually exists on disk. If not, exit with a clear error message.
Validates that drive_folder_id is not an empty string. If it is, exit with a clear error message.
Returns the config as a plain Python dictionary that gets passed down to every module that needs it.

A simple example of the validation pattern to follow:
python 
import JSON
import os
import sys

REQUIRED_FIELDS = [
    "vault_path",
    "drive_folder_id",
    "debounce_seconds",
    "backup_on_overwrite",
    "pull_delete_local_extras"
]

def load_config(config_path="config.json"):
    with open(config_path) as f:
        config = json.load(f)
    for field in REQUIRED_FIELDS:
        if field not in config:
            sys.exit(f"Missing required config field: '{field}'")
    if not os.path.isdir(config["vault_path"]):
        sys.exit(f"vault_path does not exist: {config['vault_path']}")
    if not config["drive_folder_id"].strip():
        sys.exit("drive_folder_id cannot be empty")
    return config

How Config Values Are Used
Once loaded, the config dictionary is passed as an argument to the modules that need it. The expected usage in each module is:
ModuleFields it useswatcher.pyvault_path, debounce_secondsuploader.pydrive_folder_idpuller.pyvault_path, drive_folder_id, backup_on_overwrite, pull_delete_local_extrasprocess_monitor.pynone (no config needed)drive_client.pynone (receives values as method arguments)
No module should open or parse config.json itself — they all receive the already-loaded dictionary from main.py.

Security

Add config.json to .gitignore immediately. It will contain a local file path and a Drive folder ID that should not be committed.
Add token.json and credentials.json to .gitignore as well if they are not already there.


Acceptance Criteria

 config.json exists in the project root with all five fields populated.
 Running main.py with a missing field in config.json exits immediately with a message naming the missing field.
 Running main.py with a non-existent vault_path exits with a clear error message.
 Running main.py with an empty drive_folder_id exits with a clear error message.
 No module other than main.py opens or reads config.json directly.
 config.json, token.json, and credentials.json are all listed in .gitignore.
```

- What Claude proposed: A configuration file that holds information such as Google Drive folder ID, absolute path of vault, and other options.
- What I changed before approving: I changed some of the configuration handling to make sure it is more robust in terms of error handling.
- Verification: Run `Syncher.py` and purposefully make mistakes in the configuration to ensure there is proper error handling.
- One thing I learned: It is important to make sure the brief to have context of previous tasks so that the brief has continuity with the actual project.

## Task 5 — Allow `Syncher.py` to parse CLI arguments `--push` and `--pull`
- Brief: 
```
Engineering Brief: Extending Syncher.py — CLI Argument Parsing

Overview
Your task is to extend the existing Syncher.py file to support two command line arguments: --push and --pull. The file already exists with OAuth authentication logic from the previous brief — do not remove or modify any of that existing code. You are only adding argument parsing on top of what is already there.
Estimated time: 2–3 hours.

Expected Usage
bashpython Syncher.py --push
python Syncher.py --pull

What To Add
At the top of the file, add the argparse import alongside the existing imports:
pythonimport argparse
Then add the following two functions anywhere below the existing authenticate() function, before main():
pythondef parse_args():
    parser = argparse.ArgumentParser(
        description="Obsidian <-> Google Drive sync tool"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--push", action="store_true", help="Upload local changes to Drive")
    group.add_argument("--pull", action="store_true", help="Download latest files from Drive")
    return parser.parse_args()

def run_push():
    print("[PUSH] Push mode activated.")

def run_pull():
    print("[PULL] Pull mode activated.")
Finally, update the existing main() function to call parse_args() and route to the correct mode. Authentication should still run first, before either mode is launched:
pythondef main():
    args = parse_args()       # new — parse CLI arguments first
    creds = authenticate()    # existing — must still run before anything else

    if args.push:
        run_push()
    elif args.pull:
        run_pull()

What Not To Touch

Do not remove or modify the existing authenticate() function.
Do not remove or modify the existing token.json logic.
Do not move or rename the file.


What Not To Do

Do not implement any sync logic inside this file.
Do not use sys.argv directly — use argparse only.
Do not accept any arguments other than --push and --pull at this stage.


Acceptance Criteria

 The existing OAuth authentication behaviour is completely unchanged.
 Running python Syncher.py --push authenticates and then prints [PUSH] Push mode activated.
 Running python Syncher.py --pull authenticates and then prints [PULL] Pull mode activated.
 Running python Syncher.py with no arguments prints a usage message and exits cleanly.
 Running python Syncher.py --push --pull prints a usage message and exits cleanly.
 ```
- What Claude Proposed: Use `argparse` standard library import to capture CLI arguments
- What I changed before approving: Changed `Syncher.py` to use the `authenticate()` method from the dedicated `drive_client.py` instead of its own authenticate function.
- Verification: Ran `Syncher.py` in both `--push` and `--pull` mode and they printed the correct outputs.
- One thing I learned: Its very easy to get caught up with the AI generating everything so its very important to check the results carefully before moving on.


## Task 3 — <short name>
- Brief: [link or paste]
- What Claude proposed: [1-2 lines]
- What I changed before approving: [1-2 lines]
- Verification: [what you ran or clicked to confirm it works]
- One thing I learned: ...