import subprocess
import time

def main():
    print("==================================================================")
    print("   SAFE SENTINELX NETWORK ACTIVITY SIMULATOR - NOT MALWARE")
    print("==================================================================")
    print("This script triggers suspicious outbound network connections")
    print("by launching PowerShell to query a safe public domain.")
    
    print("Spawning PowerShell outbound connection to https://example.com...")
    time.sleep(1.0)
    
    cmd = [
        "powershell.exe",
        "-Command",
        "Invoke-WebRequest -Uri https://example.com -UseBasicParsing"
    ]
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = proc.communicate()
    print("Connection simulation completed.")
    print("Outbound packet telemetry generated.")

if __name__ == "__main__":
    main()
