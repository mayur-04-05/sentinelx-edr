import os
import time
from pathlib import Path

def main():
    print("==================================================================")
    print("   SAFE SENTINELX FILE SYSTEM ACTIVITY SIMULATOR - NOT MALWARE")
    print("==================================================================")
    print("This script generates rapid file writes, updates, and renames")
    print("to trigger FIM, Mass Modification, and Mass Rename alert rules.")
    
    test_dir = Path(__file__).resolve().parent.parent / "sentinelx_test_environment"
    test_dir.mkdir(exist_ok=True)
    
    print(f"Monitored folder: {test_dir}")
    
    # 1. Trigger FILE_INTEGRITY_CHANGED (FIM)
    # Modify a file that should already be registered in FIM
    fim_file = test_dir / "test_fim_file.txt"
    print(f"Modifying FIM target: {fim_file}")
    with open(fim_file, "w") as f:
        f.write(f"SAFE SENTINELX TEST - INITIAL HASH STATE {time.time()}\n")
        
    time.sleep(2.0) # Allow agent to register the baseline hash
    
    print(f"Modifying hash value to trigger FIM alert on {fim_file}...")
    with open(fim_file, "a") as f:
        f.write("SAFE SENTINELX TEST - FILE INTEGRITY CHANGED! NEW SIGNATURE GENERATED.\n")
        
    time.sleep(1.0)
    
    # 2. Trigger RULE_MASS_FILE_MODIFICATION (15 rapid modifications)
    print("Starting mass file modifications (generating 15 file writes)...")
    for i in range(15):
        filepath = test_dir / f"mass_mod_file_{i}.txt"
        with open(filepath, "w") as f:
            f.write(f"Mass modification test file {i}\n")
        time.sleep(0.1) # Rapid speed
        
    time.sleep(1.0)

    # 3. Trigger RULE_MASS_FILE_RENAME (6 rapid renames)
    print("Starting mass file renaming (renaming 6 files)...")
    for i in range(6):
        src = test_dir / f"mass_mod_file_{i}.txt"
        dest = test_dir / f"mass_mod_file_{i}.txt.locked"
        if src.exists():
            src.rename(dest)
        time.sleep(0.1)

    print("File system simulation tasks complete. Telemetry generated successfully.")

if __name__ == "__main__":
    main()
