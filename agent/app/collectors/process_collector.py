import psutil
import datetime
from typing import List, Dict, Any
from agent.app.utils.hashing import calculate_sha256
from agent.app.logger import logger

class ProcessCollector:
    def __init__(self):
        self._hash_cache: Dict[str, str] = {}

    def get_process_list(self) -> List[Dict[str, Any]]:
        processes = []
        for proc in psutil.process_iter(attrs=['pid', 'ppid', 'name', 'exe', 'cmdline', 'username', 'create_time', 'status']):
            try:
                info = proc.info
                exe_path = info.get('exe')
                
                # Check cache for hash
                sha256 = None
                if exe_path:
                    if exe_path in self._hash_cache:
                        sha256 = self._hash_cache[exe_path]
                    else:
                        sha256 = calculate_sha256(exe_path)
                        if sha256:
                            self._hash_cache[exe_path] = sha256
                
                # Format launch time
                create_time = info.get('create_time')
                if create_time:
                    try:
                        dt = datetime.datetime.fromtimestamp(create_time, tz=datetime.timezone.utc)
                        create_time_str = dt.isoformat()
                    except Exception:
                        create_time_str = datetime.datetime.utcnow().isoformat()
                else:
                    create_time_str = datetime.datetime.utcnow().isoformat()

                processes.append({
                    "pid": info.get('pid'),
                    "ppid": info.get('ppid'),
                    "name": info.get('name'),
                    "exe": exe_path,
                    "cmdline": info.get('cmdline') or [],
                    "username": info.get('username') or "unknown",
                    "create_time": create_time_str,
                    "status": info.get('status') or "unknown",
                    "sha256": sha256
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logger.debug(f"Error inspecting process {proc.pid}: {e}")
                continue
                
        return processes
