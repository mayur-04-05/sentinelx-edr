from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# User Schemas
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "Analyst"  # Default role: Analyst

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# Agent Schemas
class AgentCreate(BaseModel):
    id: str
    hostname: str
    os: str
    ip_address: Optional[str] = None
    username: Optional[str] = None
    agent_version: str

class AgentResponse(BaseModel):
    id: str
    hostname: str
    os: str
    ip_address: Optional[str] = None
    username: Optional[str] = None
    agent_version: str
    status: str
    last_seen: datetime
    risk_score: int
    created_at: datetime

    class Config:
        from_attributes = True

# Telemetry Schemas
class TelemetryEventCreate(BaseModel):
    agent_id: str
    event_type: str  # PROCESS, NETWORK, FILE, AUTH, STARTUP, SYSTEM
    timestamp: datetime
    severity: str = "LOW"
    metadata_json: Dict[str, Any]

class TelemetryEventResponse(BaseModel):
    id: int
    agent_id: str
    event_type: str
    timestamp: datetime
    severity: str
    metadata_json: Dict[str, Any]

    class Config:
        from_attributes = True

# Alert Schemas
class AlertResponse(BaseModel):
    id: int
    agent_id: str
    rule_name: str
    title: str
    severity: str
    risk_score: int
    mitre_technique: Optional[str] = None
    description: str
    evidence: Dict[str, Any]
    timestamp: datetime
    incident_id: Optional[int] = None

    class Config:
        from_attributes = True

# Incident Schemas
class IncidentResponse(BaseModel):
    id: int
    title: str
    severity: str
    risk_score: int
    status: str
    first_seen: datetime
    last_seen: datetime
    agent_id: str
    analyst_notes: Optional[str] = None
    updated_by: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True

class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    analyst_notes: Optional[str] = None

# IOC Schemas
class IOCCreate(BaseModel):
    value: str
    type: str  # IP, DOMAIN, URL, HASH, FILE_PATH
    status: str = "UNKNOWN"
    description: Optional[str] = None

class IOCUpdate(BaseModel):
    status: str
    description: Optional[str] = None

class IOCResponse(BaseModel):
    id: int
    value: str
    type: str
    status: str
    added_at: datetime
    description: Optional[str] = None

    class Config:
        from_attributes = True

# Response Action Schemas
class ResponseActionCreate(BaseModel):
    agent_id: str
    action_type: str  # TERMINATE_PROCESS, QUARANTINE_FILE, ISOLATE_AGENT, BLOCK_IOC
    details: Dict[str, Any]

class ResponseActionResponse(BaseModel):
    id: int
    agent_id: str
    action_type: str
    details: Dict[str, Any]
    status: str
    analyst: str
    timestamp: datetime
    result_message: Optional[str] = None

    class Config:
        from_attributes = True

class ResponseActionUpdate(BaseModel):
    status: str
    result_message: Optional[str] = None

# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    username: str
    action: str
    timestamp: datetime
    target: Optional[str] = None
    result: str

    class Config:
        from_attributes = True
