import sys
from typing import List, Dict, Any
from agent.app.logger import logger

# Import winreg only on Windows
winreg_available = False
if sys.platform == "win32":
    try:
        import winreg
        winreg_available = True
    except ImportError:
        pass

class StartupCollector:
    def __init__(self):
        self.known_entries: Dict[str, str] = {}
        self.simulated_entries: Dict[str, str] = {}
        self.initialize_snapshot()

    def add_simulated_entry(self, name: str, command: str):
        self.simulated_entries[name] = command

    def initialize_snapshot(self):
        # Scan and load initial startup entries so we don't trigger alerts for existing items
        current = self._get_current_entries()
        self.known_entries = current
        logger.info(f"Initial startup registry snapshot cataloged. Monitoring {len(self.known_entries)} items.")

    def _get_current_entries(self) -> Dict[str, str]:
        entries = {}
        
        # 1. Read HKCU Run Key
        if winreg_available:
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_READ
                )
                info = winreg.QueryInfoKey(key)
                for i in range(info[1]):
                    name, val, _ = winreg.EnumValue(key, i)
                    entries[f"HKCU\\Run\\{name}"] = val
                winreg.CloseKey(key)
            except Exception as e:
                logger.debug(f"Failed to read HKCU Run registry: {e}")

            # 2. Read HKLM Run Key
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_READ
                )
                info = winreg.QueryInfoKey(key)
                for i in range(info[1]):
                    name, val, _ = winreg.EnumValue(key, i)
                    entries[f"HKLM\\Run\\{name}"] = val
                winreg.CloseKey(key)
            except Exception as e:
                # Often fails due to lack of elevation, which is normal.
                logger.debug(f"Failed to read HKLM Run registry (non-admin?): {e}")

        # 3. Mix in simulated entries
        for name, cmd in self.simulated_entries.items():
            entries[f"SIMULATED\\{name}"] = cmd
            
        return entries

    def get_new_startup_entries(self) -> List[Dict[str, Any]]:
        new_items = []
        current = self._get_current_entries()
        
        for key, val in current.items():
            if key not in self.known_entries:
                # New startup entry detected!
                new_items.append({
                    "action": "ADD_PERSISTENCE",
                    "location": key,
                    "command": val
                })
                self.known_entries[key] = val # add to known
                
        # Clean up removed items
        removed_keys = set(self.known_entries.keys()) - set(current.keys())
        for key in removed_keys:
            del self.known_entries[key]
            
        return new_items
