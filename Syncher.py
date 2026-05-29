import json
import os
import sys

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


if __name__ == "__main__":
    config = load_config()
