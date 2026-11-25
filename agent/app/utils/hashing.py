import hashlib
from pathlib import Path
from typing import Optional

def calculate_sha256(filepath: str) -> Optional[str]:
    path = Path(filepath)
    if not path.is_file():
        return None
    
    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (PermissionError, FileNotFoundError, OSError):
        # Gracefully handle file lock or missing access permissions
        return None
