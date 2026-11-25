import platform
import socket
import getpass
from agent.app.config import config

class SystemCollector:
    @staticmethod
    def get_system_info() -> dict:
        hostname = socket.gethostname()
        
        # Determine local IP address safely
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
        except Exception:
            ip_address = "127.0.0.1"

        try:
            username = getpass.getuser()
        except Exception:
            username = "unknown"

        return {
            "id": config.AGENT_ID,
            "hostname": hostname,
            "os": f"{platform.system()} {platform.release()} ({platform.version()})",
            "ip_address": ip_address,
            "username": username,
            "agent_version": "1.0.0"
        }
