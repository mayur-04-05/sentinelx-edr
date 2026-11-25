import os
import time
import json
import queue
from pathlib import Path
from typing import List, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from agent.app.utils.hashing import calculate_sha256
from agent.app.logger import logger
from agent.app.config import config

class FimTracker:
    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.hashes: Dict[str, str] = {}
        self.load_cache()

    def load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    self.hashes = json.load(f)
            except Exception as e:
                logger.error(f"Error loading FIM cache: {e}")

    def save_cache(self):
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.hashes, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving FIM cache: {e}")

    def register_file(self, filepath: str) -> str:
        sha256 = calculate_sha256(filepath) or ""
        self.hashes[filepath] = sha256
        self.save_cache()
        return sha256

    def check_file_change(self, filepath: str) -> Dict[str, Any]:
        """
        Checks if file hash has changed.
        Returns check dict with original/current hash, and whether FIM change triggered.
        """
        old_hash = self.hashes.get(filepath)
        current_hash = calculate_sha256(filepath)
        
        if not current_hash:
            return {"changed": False, "exists": False}
            
        if old_hash is None:
            # File is newly discovered
            self.hashes[filepath] = current_hash
            self.save_cache()
            return {"changed": False, "exists": True, "new_file": True}
            
        if old_hash != current_hash:
            self.hashes[filepath] = current_hash
            self.save_cache()
            return {
                "changed": True,
                "exists": True,
                "original_hash": old_hash,
                "current_hash": current_hash
            }
            
        return {"changed": False, "exists": True}

class FileActivityHandler(FileSystemEventHandler):
    def __init__(self, event_queue: queue.Queue, fim_tracker: FimTracker):
        self.event_queue = event_queue
        self.fim_tracker = fim_tracker

    def on_created(self, event):
        if event.is_directory:
            return
        logger.info(f"File created: {event.src_path}")
        # Register in FIM
        file_hash = self.fim_tracker.register_file(event.src_path)
        
        self.event_queue.put({
            "action": "CREATE",
            "path": event.src_path,
            "size": os.path.getsize(event.src_path) if os.path.exists(event.src_path) else 0,
            "sha256": file_hash
        })

    def on_modified(self, event):
        if event.is_directory:
            return
        logger.info(f"File modified: {event.src_path}")
        
        # Check FIM for changes
        fim_result = self.fim_tracker.check_file_change(event.src_path)
        
        event_data = {
            "action": "MODIFY",
            "path": event.src_path,
            "size": os.path.getsize(event.src_path) if os.path.exists(event.src_path) else 0,
            "sha256": fim_result.get("current_hash") or calculate_sha256(event.src_path)
        }
        
        if fim_result.get("changed"):
            event_data["fim_event"] = {
                "type": "FILE_INTEGRITY_CHANGED",
                "original_hash": fim_result["original_hash"],
                "current_hash": fim_result["current_hash"]
            }
            
        self.event_queue.put(event_data)

    def on_deleted(self, event):
        if event.is_directory:
            return
        logger.info(f"File deleted: {event.src_path}")
        
        # Remove from FIM hashes
        if event.src_path in self.fim_tracker.hashes:
            del self.fim_tracker.hashes[event.src_path]
            self.fim_tracker.save_cache()
            
        self.event_queue.put({
            "action": "DELETE",
            "path": event.src_path
        })

    def on_moved(self, event):
        if event.is_directory:
            return
        logger.info(f"File renamed/moved from {event.src_path} to {event.dest_path}")
        
        # Update FIM tracker
        old_hash = self.fim_tracker.hashes.pop(event.src_path, None)
        new_hash = calculate_sha256(event.dest_path) or old_hash or ""
        if event.dest_path:
            self.fim_tracker.hashes[event.dest_path] = new_hash
        self.fim_tracker.save_cache()
        
        self.event_queue.put({
            "action": "RENAME",
            "path": event.src_path,
            "dest_path": event.dest_path,
            "size": os.path.getsize(event.dest_path) if os.path.exists(event.dest_path) else 0,
            "sha256": new_hash
        })

class FileCollector:
    def __init__(self):
        self.event_queue = queue.Queue()
        self.observer = Observer()
        
        # Initialize FIM Tracker
        cache_path = Path(__file__).resolve().parent.parent / ".fim_cache.json"
        self.fim_tracker = FimTracker(cache_path)
        
        self.monitored_paths = config.MONITORED_DIRECTORIES
        self.setup_directories()

    def setup_directories(self):
        for path_str in self.monitored_paths:
            path = Path(path_str)
            if not path.exists():
                logger.info(f"Monitored directory {path_str} does not exist. Creating it.")
                path.mkdir(parents=True, exist_ok=True)
                
            # Scan existing files and register their hashes in FIM
            for root, _, files in os.walk(path):
                for f in files:
                    filepath = str(Path(root) / f)
                    if filepath not in self.fim_tracker.hashes:
                        self.fim_tracker.register_file(filepath)

    def start(self):
        event_handler = FileActivityHandler(self.event_queue, self.fim_tracker)
        for path in self.monitored_paths:
            if os.path.exists(path):
                self.observer.schedule(event_handler, path, recursive=True)
                logger.info(f"Started monitoring file activity in {path}")
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def get_pending_events(self) -> List[Dict[str, Any]]:
        events = []
        while not self.event_queue.empty():
            try:
                events.append(self.event_queue.get_nowait())
            except queue.Empty:
                break
        return events
