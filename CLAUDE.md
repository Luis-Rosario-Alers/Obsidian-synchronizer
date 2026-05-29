# Obsidian Synchronizer

## The goal of this project
A program designed to synchronize obsidian notes across devices
using Google Drive's API to upload and pull files remotely.

## Used Technologies
- `watchdog` File system event monitoring
- `psutil` Process detection
- `google-api-python-client` Drive API access
- `google-auth-oauthlib` OAuth 2.0 authentication
- `queue` Thread-safe queue
- `threading` Worker and monitor threads

## Constraints
- GUI-based extensions are strictly prohibited

## Files
- `Syncher.py` - Main file for program code.