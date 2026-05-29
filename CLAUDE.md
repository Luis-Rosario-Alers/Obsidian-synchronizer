# CLAUDE.md

## What this project is?
This project is a program made to allow one to sync their obsidian vault to their Google Drive to allow for cross-device notes

## Goal
Synchronize Obsidian vault files across devices using Google Drive's API. Runs as a background CLI process — no GUI.

## Setup
```powershell
# Install dependencies
.venv\Scripts\pip install -r requirements.txt

# Run the synchronizer
.venv\Scripts\python Syncher.py --push   # upload local changes
.venv\Scripts\python Syncher.py --pull   # download remote changes
```

OAuth credentials are requested on first run and saved to `token.json`. The Google Cloud project is named "Obsidian Synchronizer".

## Planned Architecture
The program is split into focused modules orchestrated by `Syncher.py`:

- `Syncher.py` — Entry point; parses `--push`/`--pull` CLI args, initializes OAuth, coordinates all components
- `watcher.py` — `watchdog`-based file system monitor; enqueues changed files for upload
- `uploader.py` — Daemon thread; drains the upload queue and writes to Google Drive
- `puller.py` — Downloads remote Drive files to the local vault
- `process_monitor.py` — `psutil`-based monitor; shuts down cleanly when the Obsidian process exits and the upload queue is empty
- `config.json` — User-facing configuration (vault path, Drive folder ID, etc.)

## Key Constraints
- No GUI — strictly CLI
- OAuth token persisted in `token.json` (excluded from git)
- Upload/download coordination uses `queue.Queue` between `watcher.py` and `uploader.py`
- Shutdown is cooperative: `process_monitor.py` signals shutdown only after the queue drains

## Conventions
- Prefer to explain code in places where its purpose is not obvious.
- Prefer `snake_case` function naming.
- Prefer to use type hints.