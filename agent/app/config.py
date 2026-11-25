import os
import uuid
from pathlib import Path

# Paths
AGENT_DIR = Path(__file__).resolve().parent.parent
AGENT_ID_FILE = AGENT_DIR / ".agent_id"

# Get or create persistent Agent ID
def get_persistent_agent_id() -> str:
    if AGENT_ID_FILE.exists():
        try:
            with open(AGENT_ID_FILE, "r") as f:
                agent_id = f.read().strip()
                if agent_id:
                    return agent_id
        except Exception:
            pass
            
    # Generate new one
    new_id = str(uuid.uuid4())
    try:
        with open(AGENT_ID_FILE, "w") as f:
            f.write(new_id)
    except Exception:
        pass
    return new_id

class AgentConfig:
    AGENT_ID: str = get_persistent_agent_id()
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000/api")
    HEARTBEAT_INTERVAL: float = float(os.getenv("HEARTBEAT_INTERVAL", "15.0"))
    TELEMETRY_INTERVAL: float = float(os.getenv("TELEMETRY_INTERVAL", "5.0"))
    
    # Directory to monitor for file and FIM events
    MONITORED_DIRECTORIES: list[str] = [
        str(Path(__file__).resolve().parent.parent.parent / "sentinelx_test_environment")
    ]

config = AgentConfig()
