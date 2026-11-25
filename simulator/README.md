# SentinelX Safe Telemetry Simulator

This directory contains harmless behavior-simulation scripts. They mimic malicious techniques (Defense Evasion, Command Execution, Impact, Credential Access) without causing any system harm.

## Simulators Guide

### 1. Process Spawn Chain Simulation
- **Script**: `safe_process_test.py`
- **Tactic**: Execution & Defense Evasion
- **MITRE technique**: T1059 (Command and Scripting Interpreter), T1036 (Masquerading)
- **Goal**: Spawns a nested process (`Python` -> `CMD` -> `PowerShell` -> `Python child`) from the temporary environment.
- **Run**:
  ```bash
  python simulator/safe_process_test.py
  ```

### 2. Ransomware & File Integrity Simulation
- **Script**: `safe_file_activity_test.py`
- **Tactic**: Impact
- **MITRE technique**: T1486 (Data Encrypted for Impact), T1496 (File Integrity Modification)
- **Goal**: Modifies a registered file to alter its cryptographic hash (FIM change), creates 15 files in rapid succession (Mass Modification), and renames them (Mass Rename).
- **Run**:
  ```bash
  python simulator/safe_file_activity_test.py
  ```

### 3. Outbound Connection Simulation
- **Script**: `safe_network_test.py`
- **Tactic**: Command and Control
- **MITRE technique**: T1043 (Commonly Used Port Network)
- **Goal**: Spawns a shell (`powershell.exe`) to execute a web request to `example.com`, generating an outbound socket connection telemetry event.
- **Run**:
  ```bash
  python simulator/safe_network_test.py
  ```
