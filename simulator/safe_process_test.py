import subprocess
import sys
import time
from pathlib import Path

def main():
    print("==================================================================")
    print("   SAFE SENTINELX PROCESS SIMULATOR - NOT MALWARE")
    print("==================================================================")
    print("This script simulates a parent-child shell execution sequence")
    print("to trigger the RULE_SUSPICIOUS_CHAIN behavioral rule.")
    
    # 1. Create a dummy child script inside our test environment
    test_dir = Path(__file__).resolve().parent.parent / "sentinelx_test_environment"
    test_dir.mkdir(exist_ok=True)
    
    child_script = test_dir / "suspicious_test.py"
    with open(child_script, "w") as f:
        f.write('''
import sys
import time
print("SAFE SENTINELX TEST CHILD PROCESS EXECUTION")
print("Process executed successfully from temp/sandbox folder.")
time.sleep(2.0)
sys.exit(0)
''')
        
    print(f"Created child script: {child_script}")
    
    # 2. Launch CMD -> PowerShell -> Python execution chain
    print("Launching nested process chain: Python -> CMD -> PowerShell -> Python child...")
    time.sleep(1.0)
    
    cmd = [
        "cmd.exe", "/c",
        f"powershell.exe -Command \"& {{ python.exe '{child_script}' }}\""
    ]
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = proc.communicate()
    print("Execution complete. Output:")
    print(stdout)
    if stderr:
        print("Errors:")
        print(stderr)
        
    # Clean up
    try:
        child_script.unlink()
    except Exception:
        pass

if __name__ == "__main__":
    main()
