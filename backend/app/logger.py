import logging
from pathlib import Path

# Paths
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
LOG_FILE = BACKEND_DIR / "backend.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("sentinelx-backend")
