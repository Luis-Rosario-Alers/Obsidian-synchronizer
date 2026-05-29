import argparse
import json
import os
import sys

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

REQUIRED_FIELDS = [
    "vault_path",
    "drive_folder_id",
    "debounce_seconds",
    "backup_on_overwrite",
    "pull_delete_local_extras",
]


def authenticate() -> Credentials:
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                os.remove(TOKEN_FILE)
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                sys.exit(
                    "credentials.json not found. "
                    "Download it from your Google Cloud project and place it in the project root."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def load_config(config_path: str = "config.json") -> dict:
    try:
        with open(config_path) as f:
            config = json.load(f)
    except FileNotFoundError:
        sys.exit(f"Config file not found: '{config_path}'")
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON in config file: {e}")

    for field in REQUIRED_FIELDS:
        if field not in config:
            sys.exit(f"Missing required config field: '{field}'")

    if not os.path.isdir(config["vault_path"]):
        sys.exit(f"vault_path does not exist: {config['vault_path']}")

    if not config["drive_folder_id"].strip():
        sys.exit("drive_folder_id cannot be empty")

    return config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Obsidian vault synchronizer")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--push", action="store_true", help="Upload local changes to Drive")
    group.add_argument("--pull", action="store_true", help="Download remote changes from Drive")
    return parser.parse_args()


def run_push(config: dict, creds: Credentials) -> None:
    pass  # stub — upload logic goes here


def run_pull(config: dict, creds: Credentials) -> None:
    pass  # stub — download logic goes here


def main() -> None:
    args = parse_args()
    creds = authenticate()
    config = load_config()

    if args.push:
        run_push()
    elif args.pull:
        run_pull()


if __name__ == "__main__":
    main()
