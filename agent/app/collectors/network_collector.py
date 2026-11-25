import psutil
from typing import List, Dict, Any
from agent.app.logger import logger

class NetworkCollector:
    @staticmethod
    def get_network_connections() -> List[Dict[str, Any]]:
        connections = []
        try:
            # kind='inet' fetches TCP and UDP (IPv4 and IPv6)
            for conn in psutil.net_connections(kind='inet'):
                # We only want active connections (established, listening) or just any active TCP/UDP
                if not conn.raddr:
                    continue  # Ignore listeners with no remote address for EDR remote connection tracking
                    
                pid = conn.pid
                pname = "unknown"
                if pid:
                    try:
                        pname = psutil.Process(pid).name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Remote address/port
                r_host, r_port = conn.raddr
                l_host, l_port = conn.laddr if conn.laddr else ("0.0.0.0", 0)

                # Map connection status or state
                connections.append({
                    "pid": pid,
                    "process_name": pname,
                    "local_address": l_host,
                    "local_port": l_port,
                    "remote_address": r_host,
                    "remote_port": r_port,
                    "protocol": "TCP" if conn.type == 1 else "UDP",  # SOCK_STREAM is 1, SOCK_DGRAM is 2
                    "status": conn.status
                })
        except Exception as e:
            logger.debug(f"Error collecting network connections: {e}")
            
        return connections
