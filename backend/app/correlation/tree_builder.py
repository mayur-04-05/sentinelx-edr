from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app import models

def build_process_tree(incident_id: int, db: Session) -> Dict[str, Any]:
    # 1. Fetch incident details
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        return {}

    # 2. Fetch all PROCESS telemetry events for this agent
    events = db.query(models.TelemetryEvent).filter(
        models.TelemetryEvent.agent_id == incident.agent_id,
        models.TelemetryEvent.event_type == "PROCESS"
    ).order_by(models.TelemetryEvent.timestamp.asc()).all()

    if not events:
        return {
            "name": "system",
            "pid": 0,
            "exe": "system",
            "children": []
        }

    # 3. Reconstruct tree nodes
    nodes: Dict[int, Dict[str, Any]] = {}
    
    # Track latest process state per PID
    for event in events:
        meta = event.metadata_json
        pid = meta.get("pid")
        ppid = meta.get("ppid")
        name = meta.get("name", "unknown")
        exe = meta.get("exe", "unknown")
        
        # Build node dictionary
        nodes[pid] = {
            "pid": pid,
            "ppid": ppid,
            "name": name,
            "exe": exe,
            "cmdline": meta.get("cmdline", []),
            "username": meta.get("username", "unknown"),
            "create_time": meta.get("create_time"),
            "sha256": meta.get("sha256"),
            "children": []
        }

    # 4. Connect children to parents
    roots: List[Dict[str, Any]] = []
    
    for pid, node in list(nodes.items()):
        ppid = node["ppid"]
        
        # If the parent node exists and is not itself (avoid cycles), append to parent
        if ppid in nodes and ppid != pid:
            nodes[ppid]["children"].append(node)
        else:
            roots.append(node)

    # 5. Return the root node or a virtual parent grouping them
    if not roots:
        return {
            "name": "system",
            "pid": 0,
            "exe": "system",
            "children": []
        }
        
    # If multiple roots exist, wrap them in a shell/explorer dummy root if appropriate
    if len(roots) == 1:
        return roots[0]
        
    return {
        "name": "explorer.exe",
        "pid": 9999,
        "exe": "C:\\Windows\\explorer.exe",
        "children": roots
    }

def compile_incident_timeline(incident_id: int, db: Session) -> List[Dict[str, Any]]:
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        return []

    # Get first and last seen timestamps with a 5-minute pad
    pad = datetime.timedelta(minutes=5)
    start_time = incident.first_seen - pad
    end_time = incident.last_seen + pad

    # Fetch all telemetry events in this time range for this agent
    events = db.query(models.TelemetryEvent).filter(
        models.TelemetryEvent.agent_id == incident.agent_id,
        models.TelemetryEvent.timestamp >= start_time,
        models.TelemetryEvent.timestamp <= end_time
    ).order_by(models.TelemetryEvent.timestamp.asc()).all()

    # Fetch all alerts linked to this incident
    alerts = db.query(models.Alert).filter(
        models.Alert.incident_id == incident_id
    ).all()

    timeline = []
    
    # 1. Add alerts to timeline
    for alert in alerts:
        timeline.append({
            "timestamp": alert.timestamp.isoformat(),
            "type": "ALERT",
            "title": f"Detections Alert: {alert.title}",
            "description": alert.description,
            "severity": alert.severity,
            "details": alert.evidence
        })

    # 2. Add telemetry events
    for event in events:
        meta = event.metadata_json
        
        if event.event_type == "PROCESS" and meta.get("action") == "SPAWN":
            timeline.append({
                "timestamp": event.timestamp.isoformat(),
                "type": "PROCESS_SPAWN",
                "title": "Process Launched",
                "description": f"Process {meta.get('name')} (PID: {meta.get('pid')}) was executed by {meta.get('username')}.",
                "severity": "LOW",
                "details": {"cmdline": meta.get("cmdline"), "exe": meta.get("exe"), "sha256": meta.get("sha256")}
            })
            
        elif event.event_type == "NETWORK":
            timeline.append({
                "timestamp": event.timestamp.isoformat(),
                "type": "NETWORK_CONN",
                "title": "Network Connection Established",
                "description": f"{meta.get('process_name')} connected to remote destination {meta.get('remote_address')}:{meta.get('remote_port')}.",
                "severity": "LOW",
                "details": meta
            })
            
        elif event.event_type == "FILE":
            action = meta.get("action")
            timeline.append({
                "timestamp": event.timestamp.isoformat(),
                "type": "FILE_ACTIVITY",
                "title": f"File {action.capitalize() if action else 'Modified'}",
                "description": f"File path: {meta.get('path')}",
                "severity": event.severity,
                "details": meta
            })
            
        elif event.event_type == "AUTHENTICATION":
            status = meta.get("status")
            timeline.append({
                "timestamp": event.timestamp.isoformat(),
                "type": "AUTH_EVENT",
                "title": f"Authentication {status.capitalize()}",
                "description": f"User '{meta.get('username')}' attempted logon from {meta.get('source_ip')}.",
                "severity": event.severity,
                "details": meta
            })
            
        elif event.event_type == "STARTUP":
            timeline.append({
                "timestamp": event.timestamp.isoformat(),
                "type": "PERSISTENCE",
                "title": "Startup Entry Modified",
                "description": f"Added persistence key {meta.get('location')} pointing to {meta.get('command')}.",
                "severity": "HIGH",
                "details": meta
            })

    # Sort timeline chronologically
    timeline.sort(key=lambda x: x["timestamp"])
    return timeline

import datetime
