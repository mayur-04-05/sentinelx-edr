import pytest
import os
import tempfile
import time
from agent.app.utils.hashing import calculate_sha256
from agent.app.collectors.system_collector import SystemCollector
from agent.app.collectors.process_collector import ProcessCollector
from agent.app.collectors.network_collector import NetworkCollector
from agent.app.collectors.auth_collector import AuthCollector
from agent.app.collectors.startup_collector import StartupCollector
from agent.app.collectors.file_collector import FileCollector
from agent.app.config import config

def test_calculate_sha256():
    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"SentinelX Test Content")
        temp_path = f.name

    try:
        sha256 = calculate_sha256(temp_path)
        assert sha256 is not None
        import hashlib
        expected = hashlib.sha256(b"SentinelX Test Content").hexdigest()
        assert sha256 == expected
    finally:
        os.unlink(temp_path)

def test_system_collector():
    info = SystemCollector.get_system_info()
    assert info["id"] == config.AGENT_ID
    assert "hostname" in info
    assert "os" in info
    assert "ip_address" in info
    assert "username" in info
    assert info["agent_version"] == "1.0.0"

def test_process_collector():
    collector = ProcessCollector()
    processes = collector.get_process_list()
    assert len(processes) > 0
    p = processes[0]
    assert "pid" in p
    assert "ppid" in p
    assert "name" in p
    assert "exe" in p
    assert "cmdline" in p
    assert "username" in p
    assert "sha256" in p

def test_network_collector():
    conns = NetworkCollector.get_network_connections()
    # It might be empty if there are no active remote connections, which is fine, but we assert it is a list
    assert isinstance(conns, list)
    if len(conns) > 0:
        c = conns[0]
        assert "pid" in c
        assert "local_address" in c
        assert "remote_address" in c
        assert "protocol" in c

def test_auth_collector():
    collector = AuthCollector()
    collector.add_simulated_event("sim_user", "FAILURE", "10.0.0.5")
    events = collector.get_auth_events()
    assert len(events) == 1
    assert events[0]["username"] == "sim_user"
    assert events[0]["status"] == "FAILURE"
    assert events[0]["source_ip"] == "10.0.0.5"

def test_startup_collector():
    collector = StartupCollector()
    collector.add_simulated_entry("PersistenceMalware", "C:\\Windows\\Temp\\malware.exe")
    events = collector.get_new_startup_entries()
    assert len(events) > 0
    assert any(e["location"] == "SIMULATED\\PersistenceMalware" for e in events)
    assert any(e["command"] == "C:\\Windows\\Temp\\malware.exe" for e in events)

def test_file_collector():
    # FileCollector creates test environment on init
    collector = FileCollector()
    test_dir = config.MONITORED_DIRECTORIES[0]
    
    # Create a test file
    test_file_path = os.path.join(test_dir, "test_fim_file.txt")
    
    # Start observer
    collector.start()
    time.sleep(0.5) # Allow observer thread to spin up
    
    try:
        # 1. Trigger CREATE
        with open(test_file_path, "w") as f:
            f.write("FIM Initial content")
            
        time.sleep(0.5) # Wait for file system event
        events = collector.get_pending_events()
        assert len(events) > 0
        assert any(e["action"] == "CREATE" and e["path"] == test_file_path for e in events)
        
        # 2. Register FIM check
        fim_res = collector.fim_tracker.check_file_change(test_file_path)
        assert fim_res["changed"] == False
        
        # 3. Trigger MODIFY & FIM trigger
        with open(test_file_path, "w") as f:
            f.write("FIM Modified content here!")
            
        time.sleep(0.5)
        events_mod = collector.get_pending_events()
        assert len(events_mod) > 0
        assert any(e["action"] == "MODIFY" and e["path"] == test_file_path for e in events_mod)
    finally:
        # Cleanup
        collector.stop()
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
