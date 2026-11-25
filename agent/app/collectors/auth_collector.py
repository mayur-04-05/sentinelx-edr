import time
import queue
from typing import List, Dict, Any
from agent.app.logger import logger

try:
    import win32evtlog
    import win32evtlogutil
    win32_available = True
except ImportError:
    win32_available = False

class AuthCollector:
    def __init__(self):
        self.simulated_queue = queue.Queue()
        self.last_query_time = time.time()
        if not win32_available:
            logger.info("pywin32 event logging unavailable. Using simulated authentication channel.")

    def add_simulated_event(self, username: str, status: str, source_ip: str = "127.0.0.1"):
        """
        Allows simulators to safely feed mock logins (e.g. repeated failed logins)
        """
        self.simulated_queue.put({
            "timestamp": time.time(),
            "username": username,
            "status": status, # SUCCESS, FAILURE
            "source_ip": source_ip,
            "simulated": True
        })

    def get_auth_events(self) -> List[Dict[str, Any]]:
        events = []
        
        # 1. Pop simulated events
        while not self.simulated_queue.empty():
            try:
                evt = self.simulated_queue.get_nowait()
                events.append({
                    "action": "LOGIN",
                    "username": evt["username"],
                    "status": evt["status"],
                    "source_ip": evt["source_ip"],
                    "simulated": True
                })
            except queue.Empty:
                break
                
        # 2. Windows Event Log Polling (if available)
        if win32_available:
            try:
                # Open Windows Security Log
                hand = win32evtlog.OpenEventLog(None, "Security")
                flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                
                # We read events and filter for 4624 (Logon) and 4625 (Logon Failure)
                events_read = win32evtlog.ReadEventLog(hand, flags, 0)
                for event in events_read:
                    event_id = event.EventID & 0xFFFF
                    
                    # Convert EventTime to timestamp
                    evt_time = event.TimeGenerated.timestamp()
                    if evt_time < self.last_query_time:
                        # Event is older than our last check
                        break
                        
                    if event_id in [4624, 4625]:
                        # Extract strings from event payload
                        strings = event.StringInserts
                        username = "unknown"
                        source_ip = "127.0.0.1"
                        
                        if strings:
                            # Typically: username is at index 5 or 8, source IP is at index 18 or 19 depending on OS version
                            try:
                                if event_id == 4624:
                                    username = strings[5]
                                    source_ip = strings[18] if len(strings) > 18 else "127.0.0.1"
                                else: # 4625
                                    username = strings[5]
                                    source_ip = strings[19] if len(strings) > 19 else "127.0.0.1"
                            except Exception:
                                pass
                                
                        events.append({
                            "action": "LOGIN",
                            "username": username,
                            "status": "SUCCESS" if event_id == 4624 else "FAILURE",
                            "source_ip": source_ip,
                            "event_id": event_id,
                            "simulated": False
                        })
            except Exception as e:
                logger.debug(f"Could not read Windows Security Log (non-admin?): {e}")

        self.last_query_time = time.time()
        return events
