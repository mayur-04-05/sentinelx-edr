import re
from sqlalchemy.orm import Session
from backend.app import models
from backend.app.logger import logger

# Regex patterns
IP_PATTERN = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
SHA256_PATTERN = re.compile(r'\b[a-fA-F0-9]{64}\b')

def extract_and_save_iocs(alert: models.Alert, db: Session):
    """
    Parses alert evidence metadata to extract IPs, domains, and SHA-256 hashes.
    Persists them into the IOC table if new.
    """
    evidence_str = str(alert.evidence)
    
    extracted_iocs = []

    # 1. Extract SHA-256 Hashes
    hashes = SHA256_PATTERN.findall(evidence_str)
    for h in set(hashes):
        # Skip dummy or empty hashes if needed, but the regex enforces 64 hex characters
        extracted_iocs.append((h.lower(), "HASH", f"Extracted from Alert {alert.id} ({alert.title})"))

    # 2. Extract IP Addresses
    ips = IP_PATTERN.findall(evidence_str)
    for ip in set(ips):
        # Exclude loopback and local addresses
        if ip in ["127.0.0.1", "0.0.0.0", "8.8.8.8"]: # Skip loopback and public dns stub
            continue
        extracted_iocs.append((ip, "IP", f"Extracted connection from Alert {alert.id} ({alert.title})"))

    # 3. Extract File Paths (specifically looking for exe_path or file_path keys in evidence)
    if isinstance(alert.evidence, dict):
        for key in ["file_path", "exe_path", "persistence_location"]:
            path_val = alert.evidence.get(key)
            if path_val and isinstance(path_val, str) and len(path_val) > 3:
                extracted_iocs.append((path_val, "FILE_PATH", f"Trigger path in Alert {alert.id}"))

    # Save to database
    saved_count = 0
    for value, ioc_type, desc in extracted_iocs:
        try:
            # Check duplicate
            existing = db.query(models.IOC).filter(models.IOC.value == value).first()
            if not existing:
                new_ioc = models.IOC(
                    value=value,
                    type=ioc_type,
                    status="SUSPICIOUS",
                    description=desc
                )
                db.add(new_ioc)
                saved_count += 1
        except Exception as e:
            logger.error(f"Error saving extracted IOC {value}: {e}")

    if saved_count > 0:
        db.commit()
        logger.info(f"Auto-extracted and registered {saved_count} new IOCs from alert {alert.id}.")
