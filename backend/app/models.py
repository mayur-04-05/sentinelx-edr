from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float, Table
from sqlalchemy.orm import relationship
import datetime
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="Analyst", nullable=False)  # Admin, Analyst, Viewer
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, index=True)  # Agent UUID
    hostname = Column(String, index=True, nullable=False)
    os = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    username = Column(String, nullable=True)
    agent_version = Column(String, nullable=False)
    status = Column(String, default="ONLINE", nullable=False)  # ONLINE, OFFLINE
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    risk_score = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    telemetry_events = relationship("TelemetryEvent", back_populates="agent", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="agent", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="agent", cascade="all, delete-orphan")
    response_actions = relationship("ResponseAction", back_populates="agent", cascade="all, delete-orphan")
    file_integrity_records = relationship("FileIntegrityRecord", back_populates="agent", cascade="all, delete-orphan")

class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)  # PROCESS, NETWORK, FILE, AUTH, STARTUP, SYSTEM
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    severity = Column(String, index=True, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    metadata_json = Column(JSON, nullable=False)  # telemetry metadata
    
    agent = relationship("Agent", back_populates="telemetry_events")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), index=True, nullable=False)
    rule_name = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    severity = Column(String, index=True, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Integer, default=0)
    mitre_technique = Column(String, nullable=True, index=True)
    description = Column(String, nullable=False)
    evidence = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True, index=True)
    
    agent = relationship("Agent", back_populates="alerts")
    incident = relationship("Incident", back_populates="alerts")

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    severity = Column(String, index=True, default="LOW")
    risk_score = Column(Integer, default=0)
    status = Column(String, default="NEW", index=True)  # NEW, INVESTIGATING, CONTAINED, RESOLVED, FALSE_POSITIVE
    first_seen = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    agent_id = Column(String, ForeignKey("agents.id"), index=True, nullable=False)
    analyst_notes = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    agent = relationship("Agent", back_populates="incidents")
    alerts = relationship("Alert", back_populates="incident")

class IOC(Base):
    __tablename__ = "iocs"
    
    id = Column(Integer, primary_key=True, index=True)
    value = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, index=True, nullable=False)  # IP, DOMAIN, URL, HASH, FILE_PATH
    status = Column(String, default="UNKNOWN", index=True)  # UNKNOWN, SUSPICIOUS, CONFIRMED
    added_at = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    target = Column(String, nullable=True)
    result = Column(String, nullable=False)

class ResponseAction(Base):
    __tablename__ = "response_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), index=True, nullable=False)
    action_type = Column(String, nullable=False)  # TERMINATE_PROCESS, QUARANTINE_FILE, ISOLATE_AGENT, BLOCK_IOC
    details = Column(JSON, nullable=False)
    status = Column(String, default="PENDING", index=True)  # PENDING, SUCCESS, FAILED
    analyst = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    result_message = Column(String, nullable=True)
    
    agent = relationship("Agent", back_populates="response_actions")

class FileIntegrityRecord(Base):
    __tablename__ = "file_integrity_records"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), index=True, nullable=False)
    file_path = Column(String, index=True, nullable=False)
    sha256_hash = Column(String, nullable=False)
    last_monitored = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="MONITORED")  # MONITORED, CHANGED, DELETED
    
    agent = relationship("Agent", back_populates="file_integrity_records")
