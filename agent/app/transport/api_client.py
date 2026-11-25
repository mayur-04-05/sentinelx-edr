import httpx
from typing import List, Dict, Any, Optional
from agent.app.config import config
from agent.app.logger import logger

class ApiClient:
    def __init__(self):
        self.backend_url = config.BACKEND_URL
        self.agent_id = config.AGENT_ID
        self.client = httpx.Client(timeout=10.0)
        self.telemetry_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 2000

    def register(self, system_info: dict) -> bool:
        try:
            url = f"{self.backend_url}/agents/register"
            payload = {
                "id": system_info["id"],
                "hostname": system_info["hostname"],
                "os": system_info["os"],
                "ip_address": system_info["ip_address"],
                "username": system_info["username"],
                "agent_version": system_info["agent_version"]
            }
            res = self.client.post(url, json=payload)
            if res.status_code == 200:
                logger.info("Agent registered/checked-in successfully.")
                return True
            else:
                logger.error(f"Failed to register agent. Code: {res.status_code}, Body: {res.text}")
                return False
        except Exception as e:
            logger.error(f"Error communicating with backend during registration: {e}")
            return False

    def send_telemetry(self, events: List[Dict[str, Any]]) -> bool:
        # Append new events to buffer first
        for event in events:
            if len(self.telemetry_buffer) < self.max_buffer_size:
                self.telemetry_buffer.append(event)
            else:
                # Discard oldest to keep cap
                self.telemetry_buffer.pop(0)
                self.telemetry_buffer.append(event)

        if not self.telemetry_buffer:
            return True

        try:
            # Attempt to transmit the entire buffer
            url = f"{self.backend_url}/telemetry/ingest"
            res = self.client.post(url, json=self.telemetry_buffer)
            if res.status_code == 202:
                # Ingested successfully, empty local buffer
                transmitted_count = len(self.telemetry_buffer)
                self.telemetry_buffer.clear()
                logger.debug(f"Transmitted {transmitted_count} telemetry events to backend.")
                return True
            else:
                logger.warning(f"Backend rejected telemetry ingestion. Code: {res.status_code}, Buffer preserved.")
                return False
        except Exception as e:
            logger.warning(f"Failed to upload telemetry (offline?). Preserving {len(self.telemetry_buffer)} events. Error: {e}")
            return False

    def fetch_pending_actions(self) -> List[Dict[str, Any]]:
        try:
            url = f"{self.backend_url}/response/pending/{self.agent_id}"
            res = self.client.get(url)
            if res.status_code == 200:
                return res.json()
            else:
                logger.error(f"Failed to fetch response actions. Code: {res.status_code}")
                return []
        except Exception as e:
            logger.debug(f"Could not connect to fetch pending containment actions: {e}")
            return []

    def update_action_status(self, action_id: int, status: str, result_message: Optional[str] = None) -> bool:
        try:
            url = f"{self.backend_url}/response/{action_id}"
            payload = {
                "status": status,
                "result_message": result_message
            }
            res = self.client.patch(url, json=payload)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Failed to report execution status for containment action {action_id}: {e}")
            return False
