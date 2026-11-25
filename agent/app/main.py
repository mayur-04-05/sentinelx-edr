import time
import datetime
import sys
import psutil
from pathlib import Path
from agent.app.config import config
from agent.app.logger import logger
from agent.app.collectors.system_collector import SystemCollector
from agent.app.collectors.process_collector import ProcessCollector
from agent.app.collectors.network_collector import NetworkCollector
from agent.app.collectors.file_collector import FileCollector
from agent.app.collectors.auth_collector import AuthCollector
from agent.app.collectors.startup_collector import StartupCollector
from agent.app.transport.api_client import ApiClient

def main():
    logger.info("Starting SentinelX EDR Endpoint Agent...")
    logger.info(f"Agent ID: {config.AGENT_ID}")
    logger.info(f"Backend Endpoint: {config.BACKEND_URL}")

    api_client = ApiClient()
    system_collector = SystemCollector()
    process_collector = ProcessCollector()
    network_collector = NetworkCollector()
    auth_collector = AuthCollector()
    startup_collector = StartupCollector()
    
    # Initialize watchdog file collector
    file_collector = FileCollector()
    file_collector.start()

    # Initial system registration check
    system_info = system_collector.get_system_info()
    registered = api_client.register(system_info)
    if not registered:
        logger.warning("Backend is currently offline or unreachable. Will retry in background.")

    # State tracking
    seen_pids = set()
    seen_connections = set() # Track active connection tuples: (pid, proto, local, lport, remote, rport)
    last_heartbeat = 0.0
    last_telemetry = 0.0

    # Initial process snapshot: mark all current PIDs as seen so we only report newly spawned processes
    try:
        seen_pids = {p.pid for p in psutil.process_iter()}
        logger.info(f"Initial process snapshot cataloged. Monitoring {len(seen_pids)} active processes.")
    except Exception as e:
        logger.error(f"Error cataloging initial process list: {e}")

    try:
        while True:
            now = time.time()
            
            # --- Heartbeat & Configuration Polling ---
            if now - last_heartbeat >= config.HEARTBEAT_INTERVAL:
                logger.info("Executing heartbeat and pending containment actions check...")
                
                # Check-in system details to update online status
                system_info = system_collector.get_system_info()
                api_client.register(system_info)
                
                # Check for containment commands
                pending_actions = api_client.fetch_pending_actions()
                for action in pending_actions:
                    action_id = action["id"]
                    action_type = action["action_type"]
                    details = action["details"]
                    
                    logger.info(f"Processing containment command {action_id}: {action_type}")
                    
                    if action_type == "TERMINATE_PROCESS":
                        target_pid = details.get("pid")
                        target_name = details.get("process_name", "")
                        
                        try:
                            proc = psutil.Process(target_pid)
                            proc.terminate()
                            api_client.update_action_status(
                                action_id=action_id,
                                status="SUCCESS",
                                result_message=f"Terminated process {target_name} (PID: {target_pid})"
                            )
                            logger.info(f"Successfully terminated PID {target_pid}")
                        except psutil.NoSuchProcess:
                            api_client.update_action_status(
                                action_id=action_id,
                                status="SUCCESS",
                                result_message="Process already stopped"
                            )
                        except psutil.AccessDenied:
                            api_client.update_action_status(
                                action_id=action_id,
                                status="FAILED",
                                result_message="Permission denied"
                            )
                        except Exception as e:
                            api_client.update_action_status(
                                action_id=action_id,
                                status="FAILED",
                                result_message=str(e)
                            )
                            
                    # Simulators write commands to local folders or registers, FIM quarantine moves files
                    elif action_type == "QUARANTINE_FILE":
                        orig_path_str = details.get("file_path")
                        if orig_path_str:
                            orig_path = Path(orig_path_str)
                            try:
                                # Create quarantine folder
                                q_dir = orig_path.parent / "quarantine"
                                q_dir.mkdir(exist_ok=True)
                                
                                # Move file
                                q_path = q_dir / f"quarantined_{int(time.time())}_{orig_path.name}"
                                if orig_path.exists():
                                    orig_path.rename(q_path)
                                    api_client.update_action_status(
                                        action_id=action_id,
                                        status="SUCCESS",
                                        result_message=f"Quarantined {orig_path_str} -> {q_path}"
                                    )
                                else:
                                    api_client.update_action_status(
                                        action_id=action_id,
                                        status="FAILED",
                                        result_message="File not found"
                                    )
                            except Exception as ex:
                                api_client.update_action_status(
                                    action_id=action_id,
                                    status="FAILED",
                                    result_message=str(ex)
                                )
                
                last_heartbeat = now

            # --- Telemetry collection ---
            if now - last_telemetry >= config.TELEMETRY_INTERVAL:
                events = []
                
                # 1. PROCESS TELEMETRY (Delta)
                current_processes = process_collector.get_process_list()
                current_pids = {p["pid"] for p in current_processes}
                
                # Detect spawned processes
                new_pids = current_pids - seen_pids
                for proc in current_processes:
                    if proc["pid"] in new_pids:
                        events.append({
                            "agent_id": config.AGENT_ID,
                            "event_type": "PROCESS",
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "severity": "LOW",
                            "metadata_json": {
                                "pid": proc["pid"],
                                "ppid": proc["ppid"],
                                "name": proc["name"],
                                "exe": proc["exe"],
                                "cmdline": proc["cmdline"],
                                "username": proc["username"],
                                "create_time": proc["create_time"],
                                "sha256": proc["sha256"],
                                "status": proc["status"],
                                "action": "SPAWN"
                            }
                        })
                        seen_pids.add(proc["pid"])
                        
                # Clean up exited processes from memory
                exited_pids = seen_pids - current_pids
                for pid in exited_pids:
                    seen_pids.remove(pid)
                    
                # 2. NETWORK TELEMETRY (Delta)
                network_conns = network_collector.get_network_connections()
                current_conns = set()
                for conn in network_conns:
                    conn_tuple = (
                        conn["pid"],
                        conn["protocol"],
                        conn["local_address"],
                        conn["local_port"],
                        conn["remote_address"],
                        conn["remote_port"]
                    )
                    current_conns.add(conn_tuple)
                    
                    if conn_tuple not in seen_connections:
                        events.append({
                            "agent_id": config.AGENT_ID,
                            "event_type": "NETWORK",
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "severity": "LOW",
                            "metadata_json": conn
                        })
                        seen_connections.add(conn_tuple)
                        
                # Clean up closed connections from memory
                closed_conns = seen_connections - current_conns
                for conn_tuple in closed_conns:
                    seen_connections.remove(conn_tuple)

                # 3. FILE SYSTEM & FIM TELEMETRY
                file_events = file_collector.get_pending_events()
                for fe in file_events:
                    # Determine severity based on FIM alerts
                    severity = "LOW"
                    metadata = fe.copy()
                    
                    if "fim_event" in fe:
                        severity = "HIGH"
                        metadata["fim_alert"] = True
                        
                    events.append({
                        "agent_id": config.AGENT_ID,
                        "event_type": "FILE",
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "severity": severity,
                        "metadata_json": metadata
                    })

                # 4. AUTHENTICATION TELEMETRY
                auth_events = auth_collector.get_auth_events()
                for ae in auth_events:
                    events.append({
                        "agent_id": config.AGENT_ID,
                        "event_type": "AUTHENTICATION",
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "severity": "LOW" if ae["status"] == "SUCCESS" else "MEDIUM",
                        "metadata_json": ae
                    })

                # 5. STARTUP/PERSISTENCE TELEMETRY
                startup_events = startup_collector.get_new_startup_entries()
                for se in startup_events:
                    events.append({
                        "agent_id": config.AGENT_ID,
                        "event_type": "STARTUP",
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "severity": "HIGH",
                        "metadata_json": se
                    })

                # Send telemetry batch
                if events:
                    logger.info(f"Captured {len(events)} new security events. Transmission pending...")
                    api_client.send_telemetry(events)
                    
                last_telemetry = now

            time.sleep(1.0)
            
    except KeyboardInterrupt:
        logger.info("Stopping EDR file watcher...")
        file_collector.stop()
        logger.info("SentinelX EDR Agent stopped by analyst.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Agent crashed unexpectedly: {e}")
        file_collector.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
