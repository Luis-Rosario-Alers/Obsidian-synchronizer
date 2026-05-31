import logging
from src.drive_client import DriveClient, DriveClientError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.json"
TARGET_FOLDER_ID = "13qzFVINFDiRDzb1_CMsC8bpp1lh7jfD5" # <-- random folder drive.
TEST_FILE_PATH = "test_file.txt"

with open(TEST_FILE_PATH, "w") as f:
    f.write("Hello from Obsidian Synchronizer test upload!\n")

try:
    client = DriveClient(CREDENTIALS_PATH, TOKEN_PATH)
    file_id = client.upload_file(TEST_FILE_PATH, TARGET_FOLDER_ID)
    print(f"Upload successful. Drive file ID: {file_id}")
except DriveClientError as e:
    print(f"Upload failed: {e}")
