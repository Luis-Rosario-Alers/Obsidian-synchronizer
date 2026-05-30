import argparse
import json
import logging
import os
import queue
import sys
import threading
from src.drive_client import DriveClient, DriveClientError
from src.watcher import start_watcher, placeholder_consumer

REQUIRED_FIELDS = [
    "vault_path",
    "drive_folder_id",
    "debounce_seconds",
    "backup_on_overwrite",
    "pull_delete_local_extras",
]

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
    parser = argparse.ArgumentParser(
        description="Obsidian <-> Google Drive sync tool"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--push", action="store_true", help="Upload local changes to Drive")
    group.add_argument("--pull", action="store_true", help="Download remote changes from Drive")
    return parser.parse_args()


def run_push(config: dict, client: DriveClient) -> None:
    upload_queue = queue.Queue()
    consumer_thread = threading.Thread(
        target=placeholder_consumer,
        args=(upload_queue,),
        daemon=True,
    )
    consumer_thread.start()
    start_watcher(config["vault_path"], upload_queue, config["debounce_seconds"])


def run_pull(config: dict, client: DriveClient) -> None:
    logging.info("[PULL] Pull mode activated.")  # Placeholder for actual pull logic


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args()
    client = DriveClient(credentials_path="credentials.json", token_path="token.json")
    config = load_config()

    if args.push:
        run_push(config, client)
    elif args.pull:
        run_pull(config, client)


if __name__ == "__main__":
    main()
