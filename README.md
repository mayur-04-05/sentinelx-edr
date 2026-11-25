# SENTINELX EDR — AI-ASSISTED ENDPOINT DETECTION & RESPONSE PLATFORM

### *Detect. Investigate. Respond.*

SentinelX EDR is a complete, lightweight, professional Endpoint Detection & Response (EDR) platform designed for Security Operations Center (SOC) analysts to monitor host telemetry, detect suspicious behaviors, map threats to the MITRE ATT&CK framework, investigate timelines and process execution trees, and coordinate response containment activities.

---

## 1. Architectural Design

```
   ┌──────────────────────────────────────────────────────────┐
   │                    WINDOWS ENDPOINT                      │
   │                                                          │
   │   [System info]  [Process monitor]  [Sockets monitor]    │
   │   [Watchdog FIM] [Auth logger]      [Registry Startup]   │
   │                          │                               │
   │                          ▼                               │
   │               [Transport Queue/Buffer]                   │
   └──────────────────────────┬───────────────────────────────┘
                              │ Secure REST / WebSockets
                              ▼
   ┌──────────────────────────────────────────────────────────┐
   │                   FASTAPI BACKEND CORE                   │
   │                                                          │
   │     [JWT / RBAC] ──► [Detections Rule-Engine]            │
   │                           │                              │
   │                           ▼                              │
   │                [Correlation / Incidents]                 │
   │                   │                 │                    │
   │                   ▼                 ▼                    │
   │              [(Database)]   [AI Investigation]           │
   └───────────────────┬───────────────────┬──────────────────┘
                       │ WebSockets        │ REST API
                       ▼                   ▼
   ┌──────────────────────────────────────────────────────────┐
   │                    SOC DASHBOARD UI                      │
   │                                                          │
   │      [Live Alerts Feed]     [Process Tree Graph]         │
   │      [Incident Timeline]    [Containment Actions]        │
   └──────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack
- **Endpoint Agent**: Python 3.12+ (`psutil`, `watchdog`, `httpx`, `winreg` / `win32evtlog` hooks).
- **Backend Services**: Python, FastAPI, SQLAlchemy, SQLite (for local developer ease) & PostgreSQL, bcrypt password hashing, PyJWT, WebSockets.
- **Frontend Dashboard**: React, Vite, Tailwind CSS, Lucide React, Axios, React Router.
- **AI Threat Parser**: OpenAI-compatible client & Ollama local integrations (with deterministic offline local-parsing backup).
- **PDF Report Exporter**: ReportLab document builder.

---

## 3. Privacy Policy & Safeguards

SentinelX is built as an EDR tool, not spyware. The agent strictly complies with the following privacy controls:
- **No Keystroke Logging**: The agent does not capture user keystrokes.
- **No Keystroke / Screen Recording**: Silent screenshots, video captures, webcam, and microphone recordings are entirely omitted.
- **No Personal File Exfiltration**: The agent monitors directory metadata (creation, modification, hashes) within specified boundaries (`./sentinelx_test_environment/`) and never reads or uploads contents of personal documents.
- **Safe Containment Actions**: Response actions (like process kills) are audited in permanent logs and explicitly restricted from terminating protected core system processes (`lsass.exe`, `svchost.exe`, etc.).

---

## 4. MITRE ATT&CK Detections Matrix

| Tactic | Technique | ID | Detection Rule |
| :--- | :--- | :--- | :--- |
| **Execution** | PowerShell Scripting | T1059.001 | Obfuscated parameter execution signatures |
| **Execution** | Command Interpreter | T1059 | Shell execution spawn events |
| **Persistence** | Registry Run Keys | T1547.001 | Startup run configuration changes |
| **Defense Evasion** | Masquerading | T1036 | Staged binary executing from temp folders |
| **Credential Access** | Brute Force Logins | T1110 | Repeated failed auth attempts |
| **Command & Control** | Standard Ports | T1043 | Shell processes initiating sockets |
| **Impact** | Data Encryption | T1486 | Mass modification and rename indicators |
| **Impact** | FIM Changes | T1496 | Hash signature changes on registered files |

---

## 5. First-Run Installation & Setup

### Prerequisites
- Python 3.12+
- Node.js v20+ and npm

### Step 1: Clone and Set Up Workspace
Set your active editor workspace folder to:
`C:\Users\Mayur\.gemini\antigravity\scratch\sentinelx-edr`

Create your local environment config file:
```bash
copy .env.example .env
```

### Step 2: Start Backend Server
Install backend requirements and run FastAPI using Uvicorn:
```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Verify the health endpoint: `http://127.0.0.1:8000/health`.

### Step 3: Start SOC Dashboard
Install frontend packages and launch Vite:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your web browser. Seed your administrator account by clicking **Request Registration**, fill in credentials, select Admin, and log in.

### Step 4: Run EDR Endpoint Agent
In a separate terminal on the host computer:
```bash
pip install -r agent/requirements.txt
python agent/app/main.py
```
Observe the EDR dashboard in your browser. The endpoint status will switch to **🟢 ONLINE**.

---

## 6. Running Safe Simulations

To verify detections and incidents, run the safe simulation scripts:

### A. Suspicious Process Chain Simulation
```bash
python simulator/safe_process_test.py
```
*Triggers: Suspicious Process Path (`RULE_SUSPICIOUS_PATH`) & Browser-Shell Chain (`RULE_SUSPICIOUS_CHAIN`).*

### B. Ransomware & FIM Simulation
```bash
python simulator/safe_file_activity_test.py
```
*Triggers: FIM Hash Alteration (`RULE_FILE_INTEGRITY_CHANGED`), Mass Writes (`RULE_MASS_FILE_MODIFICATION`), and Mass Renames (`RULE_MASS_FILE_RENAME`).*

### C. Command & Control Socket Simulation
```bash
python simulator/safe_network_test.py
```
*Triggers: Shell Network connection (`RULE_SUSPICIOUS_NET_PROCESS`) and PowerShell web commands (`RULE_CMDLINE_PATTERN`).*
