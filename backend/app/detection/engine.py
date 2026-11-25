import os
import yaml
import re
import datetime
import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app import models
from backend.app.websocket_manager import manager
from backend.app.config import settings

# Global rules list
RULES: List[Dict[str, Any]] = []

def load_all_rules():
    global RULES
    RULES = []
    rules_dir = Path(__file__).resolve().parent.parent.parent.parent / "rules"
    if not rules_dir.exists():
        # Fallback if path is different
        rules_dir = Path("./rules")

    if rules_dir.exists():
        for filename in os.listdir(rules_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                try:
                    filepath = rules_dir / filename
                    with open(filepath, "r") as f:
                        data = yaml.safe_load(f)
                        if data and "rules" in data:
                            RULES.extend(data["rules"])
                except Exception as e:
                    print(f"Error loading rule file {filename}: {e}")
    print(f"Loaded {len(RULES)} behavioral detection rules.")

# Import Path inside helper
from pathlib import Path

# Load on module import
load_all_rules()

async def run_detection_engine(events: List[models.TelemetryEvent], db: Session):
    for event in events:
        metadata = event.metadata_json
        
        # Check each loaded rule
        for rule in RULES:
            rule_id = rule["id"]
            rule_name = rule["name"]
            severity = rule["severity"]
            risk_score = rule["risk_score"]
            mitre_technique = rule.get("mitre_technique")
            conditions = rule.get("conditions", {})
            
            triggered = False
            evidence = {}

            # RULE_SUSPICIOUS_PATH
            if rule_id == "RULE_SUSPICIOUS_PATH" and event.event_type == "PROCESS":
                exe_path = (metadata.get("exe") or "").lower()
                name = (metadata.get("name") or "").lower()
                
                path_match = any(p in exe_path for p in conditions.get("exe_contains", []))
                name_match = any(re.match(pattern, name) for pattern in conditions.get("name_matches", []))
                
                if path_match and name_match:
                    triggered = True
                    evidence = {
                        "process_name": name,
                        "exe_path": exe_path,
                        "trigger": "Execution of suspicious process name in sandboxed/temp directory"
                    }

            # RULE_SUSPICIOUS_CHAIN
            elif rule_id == "RULE_SUSPICIOUS_CHAIN" and event.event_type == "PROCESS":
                # Find parent-child chain
                ppid = metadata.get("ppid")
                pid = metadata.get("pid")
                child_name = (metadata.get("name") or "").lower()
                
                # Retrieve parent info from telemetry if possible, else look up in DB
                parent_name = "unknown"
                parent_event = db.query(models.TelemetryEvent).filter(
                    models.TelemetryEvent.agent_id == event.agent_id,
                    models.TelemetryEvent.event_type == "PROCESS",
                    models.TelemetryEvent.metadata_json["pid"].as_integer() == ppid
                ).order_by(models.TelemetryEvent.timestamp.desc()).first()
                
                if parent_event:
                    parent_name = (parent_event.metadata_json.get("name") or "").lower()
                
                # Check condition
                if parent_name in conditions.get("parent_name", []) and child_name in conditions.get("child_name", []):
                    triggered = True
                    evidence = {
                        "parent_process": parent_name,
                        "child_process": child_name,
                        "pid": pid,
                        "ppid": ppid,
                        "trigger": f"Suspicious process chain: {parent_name} -> {child_name}"
                    }

            # RULE_CMDLINE_PATTERN
            elif rule_id == "RULE_CMDLINE_PATTERN" and event.event_type == "PROCESS":
                cmdline_args = [str(arg).lower() for arg in metadata.get("cmdline", [])]
                cmdline_str = " ".join(cmdline_args)
                
                matched_arg = None
                for arg in conditions.get("cmdline_contains", []):
                    if arg in cmdline_str:
                        matched_arg = arg
                        triggered = True
                        break
                        
                if triggered:
                    evidence = {
                        "command_line": cmdline_str,
                        "matched_argument": matched_arg,
                        "trigger": f"Suspicious parameter '{matched_arg}' detected in command line arguments."
                    }

            # RULE_FILE_INTEGRITY_CHANGED
            elif rule_id == "RULE_FILE_INTEGRITY_CHANGED" and event.event_type == "FILE":
                if metadata.get("action") == "MODIFY" and metadata.get("fim_alert") == True:
                    triggered = True
                    fim_event = metadata.get("fim_event", {})
                    evidence = {
                        "file_path": metadata.get("path"),
                        "original_hash": fim_event.get("original_hash"),
                        "current_hash": fim_event.get("current_hash"),
                        "trigger": "FIM Hash Alteration Alert"
                    }

            # RULE_MASS_FILE_MODIFICATION / RULE_MASS_FILE_RENAME
            elif rule_id in ["RULE_MASS_FILE_MODIFICATION", "RULE_MASS_FILE_RENAME"] and event.event_type == "FILE":
                window = conditions.get("time_window_seconds", 10)
                threshold = conditions.get("modification_count_threshold", 10) if rule_id == "RULE_MASS_FILE_MODIFICATION" else conditions.get("rename_count_threshold", 5)
                action_type = "MODIFY" if rule_id == "RULE_MASS_FILE_MODIFICATION" else "RENAME"
                
                # Count matching file events from the same agent within window
                cutoff = datetime.datetime.utcnow() - datetime.timedelta(seconds=window)
                
                # Fetch recent file events from database
                recent_events = db.query(models.TelemetryEvent).filter(
                    models.TelemetryEvent.agent_id == event.agent_id,
                    models.TelemetryEvent.event_type == "FILE",
                    models.TelemetryEvent.timestamp >= cutoff
                ).all()
                
                count = sum(1 for e in recent_events if e.metadata_json.get("action") == action_type)
                
                if count >= threshold:
                    triggered = True
                    evidence = {
                        "threshold": threshold,
                        "event_count": count,
                        "time_window": f"{window}s",
                        "trigger": f"Mass file {action_type.lower()}s threshold reached."
                    }

            # RULE_REPEATED_AUTH_FAILURES
            elif rule_id == "RULE_REPEATED_AUTH_FAILURES" and event.event_type == "AUTHENTICATION":
                if metadata.get("status") == "FAILURE":
                    window = conditions.get("time_window_seconds", 30)
                    threshold = conditions.get("failure_threshold", 3)
                    
                    cutoff = datetime.datetime.utcnow() - datetime.timedelta(seconds=window)
                    
                    recent_events = db.query(models.TelemetryEvent).filter(
                        models.TelemetryEvent.agent_id == event.agent_id,
                        models.TelemetryEvent.event_type == "AUTHENTICATION",
                        models.TelemetryEvent.timestamp >= cutoff
                    ).all()
                    
                    failures = sum(1 for e in recent_events if e.metadata_json.get("status") == "FAILURE")
                    
                    if failures >= threshold:
                        triggered = True
                        evidence = {
                            "threshold": threshold,
                            "failed_attempts": failures,
                            "time_window": f"{window}s",
                            "username": metadata.get("username"),
                            "trigger": "Brute-force authentication pattern detected"
                        }

            # RULE_NEW_STARTUP_ENTRY
            elif rule_id == "RULE_NEW_STARTUP_ENTRY" and event.event_type == "STARTUP":
                if metadata.get("action") == "ADD_PERSISTENCE":
                    triggered = True
                    evidence = {
                        "persistence_location": metadata.get("location"),
                        "configured_command": metadata.get("command"),
                        "trigger": "New registry startup persistence entry detected"
                    }

            # RULE_SUSPICIOUS_NET_PROCESS
            elif rule_id == "RULE_SUSPICIOUS_NET_PROCESS" and event.event_type == "NETWORK":
                proc_name = (metadata.get("process_name") or "").lower()
                remote_ip = metadata.get("remote_address")
                
                name_match = proc_name in conditions.get("process_name", [])
                exclude_ip = remote_ip in conditions.get("exclude_dest_ips", [])
                
                if name_match and not exclude_ip:
                    triggered = True
                    evidence = {
                        "process_name": proc_name,
                        "pid": metadata.get("pid"),
                        "local_socket": f"{metadata.get('local_address')}:{metadata.get('local_port')}",
                        "remote_socket": f"{remote_ip}:{metadata.get('remote_port')}",
                        "trigger": f"External network socket opened by terminal executable {proc_name}."
                    }

            if triggered:
                # Add Alert
                alert = models.Alert(
                    agent_id=event.agent_id,
                    rule_name=rule_id,
                    title=rule_name,
                    severity=severity,
                    risk_score=risk_score,
                    mitre_technique=mitre_technique,
                    description=rule["description"],
                    evidence=evidence,
                    timestamp=datetime.datetime.utcnow()
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)
                
                # Fetch agent and increase risk score
                agent = db.query(models.Agent).filter(models.Agent.id == event.agent_id).first()
                if agent:
                    # Update agent's risk score (capping at 100)
                    agent.risk_score = min(agent.risk_score + risk_score, 100)
                    db.commit()
                    
                # Broadcast alert live to dashboard via Websocket
                alert_data = {
                    "event": "NEW_ALERT",
                    "data": {
                        "id": alert.id,
                        "agent_id": alert.agent_id,
                        "hostname": agent.hostname if agent else "Unknown Host",
                        "rule_name": alert.rule_name,
                        "title": alert.title,
                        "severity": alert.severity,
                        "risk_score": alert.risk_score,
                        "mitre_technique": alert.mitre_technique,
                        "description": alert.description,
                        "evidence": alert.evidence,
                        "timestamp": alert.timestamp.isoformat()
                    }
                }
                await manager.broadcast_json(alert_data)
                
                # In Phase 5, we will hook Alert Correlation to group this alert into an Incident
                from backend.app.correlation.correlator import correlate_alert_to_incident
                correlate_alert_to_incident(alert, db)
                
                # In Phase 7, we extract potential IOCs (hashes, IPs, etc.) from alert details
                from backend.app.services.ioc_extractor import extract_and_save_iocs
                extract_and_save_iocs(alert, db)
                
                break # Only trigger one alert per matching event to keep logs clean
