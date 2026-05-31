from src.watcher import VaultEventHandler
import queue

def test_metadata_filtering():
    upload_queue = queue.Queue()
    watcher = VaultEventHandler(upload_queue, 2.0)
    bad_path = "/path/to/vault/.obsidian/config"
    watcher._enqueue(bad_path)
    assert upload_queue.empty()