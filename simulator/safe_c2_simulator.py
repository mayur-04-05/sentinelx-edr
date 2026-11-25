import subprocess
import time

def main():
    print("==================================================================")
    print("   SAFE PERSISTENT C2 SIMULATOR - NOT MALWARE")
    print("==================================================================")
    print("Spawning persistent PowerShell loop to query example.com over 15s...")
    
    # Run a PowerShell command that queries example.com in a loop, sleeping 1 sec between calls
    # This keeps the powershell.exe process alive and establishes outbound TCP connections
    cmd = [
        "powershell.exe",
        "-Command",
        "for ($i=0; $i -lt 15; $i++) { try { [System.Net.HttpWebRequest]::Create('http://example.com').GetResponse().Close() } catch {} ; Start-Sleep -Seconds 1 }"
    ]
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("PowerShell background loop running. Waiting 15 seconds for EDR agent capture...")
    time.sleep(16.0)
    
    proc.terminate()
    print("C2 simulation complete.")

if __name__ == "__main__":
    main()
