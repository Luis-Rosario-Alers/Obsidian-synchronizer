## Task 1 — Google Drive API wrapper file
- Brief: 
```
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
```
- What Claude proposed:  `drive_client.py` Google Drive API Wrapper file
- What I changed before approving: Some aspects of how the wrapper file would handle errors
- Verification: Created a test file that would upload a file to the specific Google Drive folder
- One thing I learned: it is pivotal to give the AI detailed context as it will sometimes assume what you want incorrectly.

## Task 2 — Add Configuration File Support
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

## Task 3 — Allow `Syncher.py` to parse CLI arguments `--push` and `--pull`
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


## Task 4 — Create `watcher.py` for file modification overwatch

- Brief:
```
  Engineering Brief: watcher.py — File System Monitoring

Overview
Your task is to create watcher.py, which monitors the local Obsidian vault for any file changes and reacts to them. It uses the watchdog library to listen for file system events in real time. When a file is created or modified, the watcher places the affected file path onto a shared queue so the upload worker (built in a later brief) can process it. For now the queue consumer is a placeholder that simply prints the detected change.
Estimated time: 1–2 days.

Installation
watchdog is a third party library and must be installed:
bashpip install watchdog

How watchdog Works
watchdog works by attaching an Observer to a directory and passing it an event handler class. The event handler defines methods that are called automatically when the file system changes. The Observer runs on its own thread, so the rest of the program remains unblocked while it listens.
The three event types to handle are:
EventTriggeron_createdA new file appears in the vaulton_modifiedAn existing file is saved with changeson_movedA file or folder is renamed or moved
Deletions are intentionally ignored at this stage.

Implementation
1. Install and import the required watchdog classes:
pythonfrom watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import queue
import time
import logging
1. Create the event handler class:
pythonclass VaultEventHandler(FileSystemEventHandler):
    def __init__(self, upload_queue):
        self.upload_queue = upload_queue

    def on_created(self, event):
        if not event.is_directory:
            logging.info(f"File created: {event.src_path}")
            self.upload_queue.put(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            logging.info(f"File modified: {event.src_path}")
            self.upload_queue.put(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            logging.info(f"File moved: {event.src_path} -> {event.dest_path}")
            self.upload_queue.put(event.dest_path)
1. Create the watcher startup function:
pythondef start_watcher(vault_path, upload_queue):
    event_handler = VaultEventHandler(upload_queue)
    observer = Observer()
    observer.schedule(event_handler, path=vault_path, recursive=True)
    observer.start()
    logging.info(f"Watching vault at: {vault_path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
1. Add a placeholder queue consumer for testing purposes only. This simulates what the upload worker will do in a later brief and should be removed once uploader.py is connected:
pythondef placeholder_consumer(upload_queue):
    while True:
        path = upload_queue.get()
        print(f"[QUEUE] Would upload: {path}")
        upload_queue.task_done()
1. Wire into Syncher.py by updating run_push():
pythonimport queue
import threading
from sync.watcher import start_watcher, placeholder_consumer

def run_push(config, creds):
    upload_queue = queue.Queue()
    consumer_thread = threading.Thread(
        target=placeholder_consumer,
        args=(upload_queue,),
        daemon=True
    )
    consumer_thread.start()
    start_watcher(config["vault_path"], upload_queue)

Debouncing
watchdog often fires multiple events in quick succession for a single save — for example a text editor may write a temp file and then rename it, producing two or three events for one user action. To avoid uploading the same file multiple times, implement a simple debounce inside VaultEventHandler:

Record the last time each file path was enqueued in a dictionary.
Only enqueue a path if at least debounce_seconds have passed since it was last enqueued.
Read debounce_seconds from the config dictionary passed into the handler.

pythonimport time

class VaultEventHandler(FileSystemEventHandler):
    def __init__(self, upload_queue, debounce_seconds):
        self.upload_queue = upload_queue
        self.debounce_seconds = debounce_seconds
        self._last_enqueued = {}

    def _enqueue(self, path):
        now = time.time()
        last = self._last_enqueued.get(path, 0)
        if now - last >= self.debounce_seconds:
            self._last_enqueued[path] = now
            self.upload_queue.put(path)
            logging.info(f"Enqueued: {path}")

    def on_created(self, event):
        if not event.is_directory:
            self._enqueue(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._enqueue(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._enqueue(event.dest_path)

Logging
Use Python's logging module throughout. No print() calls except inside the temporary placeholder_consumer. Log the following:
EventLevelWatcher started successfullyINFOFile path enqueuedINFOFile event fired but debouncedDEBUGWatcher stoppedINFO

What Not to Do

Do not implement any upload logic inside this file. Its only job is to detect changes and enqueue file paths.
Do not read config.json directly — accept the config dictionary as a function argument.
Do not handle file deletions at this stage.
Do not remove the debounce — without it the uploader will receive a flood of duplicate events on every save.


Acceptance Criteria

 Running python Syncher.py --push starts the watcher and logs the vault path being watched.
 Modifying a file inside the vault prints [QUEUE] Would upload: followed by the file path.
 Creating a new file inside the vault triggers the same output.
 Modifying the same file twice within debounce_seconds only produces one queue entry.
 Modifying a file outside the vault directory produces no output.
 Directory events (creating or renaming a folder) produce no output.
 Pressing Ctrl+C stops the watcher cleanly with no exception stack trace.
You said: Why did you do this?excerpt_from_previous_claude_message.txt1 linetxtWhy did you do this? wouldnt this mean that any changes to directories would be ignored?11:45 a. m.Claude responded: Yes, exactly — that is intentional.Yes, exactly — that is intentional. Here is why:
In the context of this project, the watcher only needs to react to file changes, not directory changes. Directories themselves do not contain note content — the markdown files inside them do. So when a folder is created, renamed, or moved inside the vault, there is nothing to upload yet. The relevant event will come when a file inside that folder is created or modified, and that event is what gets enqueued.
Concretely, if you create a new folder called Projects/ in your vault and then create a note inside it called ideas.md, two events fire:

A directory created event for Projects/ — ignored
A file created event for Projects/ideas.md — enqueued and uploaded

The upload worker then handles creating the Projects/ folder on Google Drive as part of uploading ideas.md, so the folder structure is still mirrored correctly in the cloud. The folder does not need its own event to make that happen.
If directory events were not filtered out, the watcher would enqueue folder paths alongside file paths, and the uploader would then try to upload a directory as if it were a file, which would cause an error.
```

- What Claude proposed: Using the `watchdog` library to watch for file modifications
- What I changed before approving: Added thread locking to stop simultaneous write and read of the `self._last_enqueued` dictionary
- Verification: Modified files within the specified vault path in my `config.json` and looked for logging notifications of file modifications
- One thing I learned: `claude.ai` and `gemini` code review is very useful for finding small technical errors that could, over time, increase the technical debt of the project.

## Task 5 — Create `uploader.py` to handle file upload queue

- Brief:
```
Engineering Brief: uploader.py — Google Drive Upload Worker

Overview
Your task is to create uploader.py, a background daemon thread that continuously reads file paths from the shared upload queue and uploads each one to Google Drive. It sits between watcher.py (which detects changes and enqueues paths) and drive_client.py (which handles the actual Drive API calls). When a path appears in the queue, the uploader picks it up and calls DriveClient.upload_file().
Estimated time: 1–2 days.

How It Fits Together
At this point in the project the three components of push mode are:
watcher.py          uploader.py          drive_client.py
  detects     →      uploads      →       calls Drive API
  changes           from queue
uploader.py is the middle piece. It does not detect changes and it does not call the Drive API directly — it delegates both of those responsibilities to the modules on either side of it.

Implementation
1. Add the required imports:
pythonimport queue
import threading
import logging
from sync.drive_client import DriveClient, DriveClientError
2. Create the uploader class:
pythonclass Uploader:
    def __init__(self, upload_queue, drive_client, drive_folder_id):
        self.upload_queue = upload_queue
        self.drive_client = drive_client
        self.drive_folder_id = drive_folder_id
        self._stop_event = threading.Event()

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logging.info("Uploader started.")

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        logging.info("Uploader stopped.")

    def _run(self):
        while not self._stop_event.is_set():
            try:
                path = self.upload_queue.get(timeout=1)
                self._upload(path)
                self.upload_queue.task_done()
            except queue.Empty:
                continue

    def _upload(self, path):
        try:
            self.drive_client.upload_file(path, self.drive_folder_id)
            logging.info(f"Uploaded: {path}")
        except DriveClientError as e:
            logging.error(f"Failed to upload {path}: {e}")
3. Wire into Syncher.py by updating run_push(), replacing the placeholder consumer from the watcher brief:
pythonfrom sync.uploader import Uploader
from sync.drive_client import DriveClient
from sync.watcher import start_watcher
import queue

def run_push(config, creds):
    upload_queue = queue.Queue()
    drive_client = DriveClient(creds)
    uploader = Uploader(upload_queue, drive_client, config["drive_folder_id"])
    uploader.start()
    start_watcher(config["vault_path"], upload_queue, config["debounce_seconds"])
    uploader.stop()

Error Handling
The uploader must never crash due to a failed upload. A single bad upload should be logged and skipped so the queue continues to drain normally. The rules are:

Catch DriveClientError on every upload attempt and log it at ERROR level.
After a failed upload, continue processing the next item in the queue.
Do not retry inside the uploader — retries are already handled inside DriveClient.upload_file().


Logging
Use Python's logging module throughout. No print() calls.
EventLevelUploader startedINFOFile successfully uploadedINFOUpload failedERRORUploader stoppedINFO

What Not to Do

Do not call the Google Drive API directly inside this file. All API interaction goes through DriveClient.
Do not read config.json directly — accept the config dictionary as a function argument passed in from Syncher.py.
Do not implement any file watching logic here. That belongs in watcher.py.
Do not remove the timeout=1 on queue.get() — without it the thread blocks indefinitely and the stop signal is never checked.


Acceptance Criteria

 Running python Syncher.py --push starts the uploader daemon thread and logs Uploader started.
 Modifying a file in the vault results in that file being uploaded to the correct Drive folder.
 The uploaded file is visible in Google Drive within a few seconds of the local change.
 A simulated upload failure (temporarily pass an invalid drive_folder_id) logs an error but does not crash the program.
 Subsequent files in the queue are still uploaded after a failed upload.
 Stopping the program logs Uploader stopped. and exits cleanly.
```

- What Claude proposed: Use a separate "uploader" thread that sequentially uploads every file in the uploader queue (files that have been marked as "modified" by `watcher.py` file overwatch)
- What I changed before approving: Changed the plan to include full folder structure mirroring to the remote obsidian vault. Ex. a file in the `Finance` folder changes, that same change should be reflected in that same folder within my remote vault.
- Verification: Use my real remote obsidian folder as my `google_drive_folder_id` and see if local changes are reflected on my Google Drive.
- One thing I learned: It's better to tweak the brief for a few more minutes to get exactly what you want than to generate mediocre code that doesn do exactly what you want it to do.

## Task 6 — Create `process_monitor.py` using `psutil`

- Brief:

```text
Engineering Brief: process_monitor.py — Obsidian Process Monitor

Overview
Your task is to create process_monitor.py, which watches for the Obsidian process using psutil and triggers a clean shutdown of the sync tool when Obsidian closes. It runs on its own thread and signals the watcher to stop, which in turn allows the uploader to drain and exit.
Estimated time: 1 day.

Installation
bashpip install psutil

Implementation
1. Imports:
pythonimport logging
import threading
import time
import psutil
2. Create the monitor class:
pythonclass ProcessMonitor:
    def __init__(self, shutdown_event: threading.Event, poll_interval: int = 5) -> None:
        self.shutdown_event = shutdown_event
        self.poll_interval = poll_interval
        self._thread: threading.Thread | None = None

    def _is_obsidian_running(self) -> bool:
        return any(
            "obsidian" in p.name().lower()
            for p in psutil.process_iter(["name"])
        )

    def _run(self) -> None:
        logging.info("Process monitor started.")
        while not self.shutdown_event.is_set():
            if not self._is_obsidian_running():
                logging.info("Obsidian process not found. Triggering shutdown.")
                self.shutdown_event.set()
                break
            time.sleep(self.poll_interval)

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self._thread.join()
        logging.info("Process monitor stopped.")
3. Wire into Syncher.py by updating run_push():
The shutdown_event is shared between the process monitor and start_watcher(). When Obsidian closes, the monitor sets the event, which signals the watcher to stop its loop, which unblocks run_push() and allows uploader.stop() to be called via the existing finally block.
pythondef run_push(config: dict, client: DriveClient) -> None:
    shutdown_event = threading.Event()
    upload_queue = queue.Queue()

    uploader = Uploader(upload_queue, client, config["drive_folder_id"], config["vault_path"])
    monitor = ProcessMonitor(shutdown_event)

    uploader.start()
    monitor.start()
    try:
        start_watcher(config["vault_path"], upload_queue, config["debounce_seconds"], shutdown_event)
    finally:
        monitor.stop()
        uploader.stop()
4. Update start_watcher() in watcher.py to accept and respect the shutdown_event:
pythondef start_watcher(vault_path, upload_queue, debounce_seconds, shutdown_event):
    event_handler = VaultEventHandler(upload_queue, debounce_seconds)
    observer = Observer()
    observer.schedule(event_handler, path=vault_path, recursive=True)
    observer.start()
    logging.info(f"Watching vault at: {vault_path}")
    try:
        while not shutdown_event.is_set():
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()

Logging
EventLevelMonitor startedINFOObsidian not found, shutdown triggeredINFOMonitor stoppedINFO

What Not to Do

Do not call uploader.stop() or upload_queue.join() inside this file — shutdown of the uploader is already handled by the finally block in Syncher.py.
Do not hardcode the process name — keep it as a case-insensitive substring match on "obsidian" to handle platform differences.
Do not set poll_interval below 5 seconds — polling more frequently than this is unnecessary and wastes CPU.


Acceptance Criteria

 Starting python Syncher.py --push with Obsidian open watches the vault normally.
 Closing Obsidian causes the program to log "Obsidian process not found. Triggering shutdown." and exit cleanly.
 The uploader fully drains the queue before the program exits.
 Killing the program with Ctrl+C still exits cleanly via the existing finally block.
 If Obsidian is not running when the program starts, it shuts down immediately.
```

- What Claude proposed: Use `psutil` to monitor the obsidian process for when it closes
- What I changed before approving: I told claude to change the `stop()` method of the `ProcessMonitor` class to set the `shutdown_event` state
- Verification: Launching the program without obsidian closes the program. Launching the program with obsidian keeps the program running until obsidian closes which terminates the program.
- One thing I learned: Claude can only review your code so much so manual review is sometimes necessary if you are heavily stuck.

## Reflection

1) The agentic workflow let me ship more than I could alone because I was able to much more quickly understand the codebase and implement features based on already existing code, allowing me to push more changes than I usually would be able to. Additionally, I saved a lot more time on reviewing because I was able to collaboratively code review with AI to catch bugs before they became dangerous.

2) I intervened when Claude tried to edit multiple files that were not part of the scope of the current task or when functions were needlessly complicated and could be simplified for readability

3) This project revealed that my own judgement is one of the most important things when it comes to building a successful project with the assistance of AI since it allowed me to approve what was good and disapprove what was either out of scope, needlessly complicated, or did not follow project conventions. Additionally, my own knowledge gaps about the technologies being used was something that was actually still applicable to the project because even with AI one has to understand the overall logic and technologies being used to effectively orchestrate agents to carry out atomic tasks within that project. For example, understanding query formation, and how pivotal it is for local and remote filenames to be the same, within the Google Drive API was necessary for my project to understand why filenames with single quotes ended up returning `malformed query` errors, so by understanding query formation, I was able to direct the AI agent to fix the code within the appropriate file and reduce the chances of creating another bug/error dramatically. Essentially, I was able to use my knowledge of how the Google Drive API expects queries to be formed in order to get the AI agent to quickly apply a fix within a minute, which would've taken me maybe 5 minutes of docs searching beforehand to implement, saving me time.

4) I will bring this workflow into my internship by setting up visual studio code, claude code, and gemini cli on my computer to ensure that I have all the tools necessary to conduct this workflow. The first thing I will do on day one is configure these tools and give them the context they need to succeed in the projects given to us. However, if there are security practices or onboarding rules that are on the stricter side, I can still use skills learned in this AI cohort such as task decomposition and higher-level AI planning through claude.ai to scaffold and decompose a project into its individual components to make development much easier and straightforward.
