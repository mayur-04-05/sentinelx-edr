import logging
from pathlib import Path

# Log directory
LOG_DIR = Path(__file__).resolve().parent.parent.parent
LOG_FILE = LOG_DIR / "agent.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("sentinelx-agent")
