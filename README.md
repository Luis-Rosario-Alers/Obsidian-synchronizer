# Obsidian ↔ Google Drive Sync

A CLI tool that syncs your Obsidian vault to Google Drive. Run `--push` to upload local changes while Obsidian is open; run `--pull` to download the latest files from Drive before opening Obsidian. The push process watches for Obsidian running and shuts down cleanly when you close it.

## Prerequisites

- Python 3.10 or higher
- A Google account
- [Obsidian](https://obsidian.md) installed
- A Google Cloud project with the Drive API enabled and `credentials.json` downloaded — [Google Cloud Console](https://console.cloud.google.com)

## Installation

1. Clone the repository: `git clone <repo-url> && cd obsidian-synchronizer`
2. Create a virtual environment: `python -m venv .venv`
3. Activate it:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com) and create a new project.
2. Navigate to **APIs & Services → Library** and enable the **Google Drive API**.
3. Go to **APIs & Services → Credentials**, click **Create Credentials → OAuth 2.0 Client ID**, and select **Desktop App**.
4. Download the generated file and save it as `credentials.json` in the project root. **Do not commit this file.**
5. Go to **APIs & Services → OAuth consent screen → Test users** and add your Google account email. Without this step, OAuth will fail with an authorization error.
6. Find your Drive folder ID: open the target folder in Google Drive in a browser — the ID is the string after `/folders/` in the URL.

## Configuration

Create `config.json` in the project root:

```json
{
  "vault_path": "/absolute/path/to/your/obsidian/vault",
  "drive_folder_id": "your-google-drive-folder-id",
  "debounce_seconds": 1.5,
  "backup_on_overwrite": true,
  "pull_delete_local_extras": false
}
```

`debounce_seconds` — delay before uploading after a file change is detected  
`backup_on_overwrite` — save a local backup when a pull overwrites a local file  
`pull_delete_local_extras` — delete local files that no longer exist in Drive during a pull

## System Configuration

**Disable access-time (atime) updates on your vault's filesystem.** The file watcher triggers on any file modification event, including the OS updating a file's last-accessed timestamp when you simply open or read a note. Without this change, every file you open in Obsidian will be queued for upload even if its contents did not change.

- **Linux**: Mount the filesystem with the `noatime` option in `/etc/fstab`.
- **macOS**: Add `noatime` to the volume's mount flags or use a launch daemon to remount with `noatime`.
- **Windows**: Run in an elevated PowerShell prompt: `fsutil behavior set disablelastaccess 1` then reboot.

## Usage

```bash
# Watches vault and uploads changes while Obsidian is open
python Syncher.py --push

# Downloads all newer files from Drive to the local vault
python Syncher.py --pull
```

## First Run

On the first run, a browser window will open asking you to authorize access to your Google Drive. After you approve, `token.json` is saved automatically and used for all future runs. **Do not commit this file.**

## Typical Workflow

1. On your primary device, run `python Syncher.py --push` before opening Obsidian.
2. Work in Obsidian as normal — changes upload automatically as you edit.
3. On a second device, run `python Syncher.py --pull` before opening Obsidian to get the latest files.

## File Reference

| File | Purpose |
|---|---|
| `config.json` | User configuration — edit this before first run |
| `credentials.json` | Google OAuth client credentials — **never commit this** |
| `token.json` | Saved OAuth token — generated automatically on first run, **never commit this** |
| `.sync-backups/` | Local backups of overwritten files created during pull |
| `sync.log` | Runtime log file for debugging |
