import httpx
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from backend.app import models
from backend.app.config import settings
from backend.app.logger import logger

def generate_local_offline_analysis(incident: models.Incident, alerts: List[models.Alert]) -> Dict[str, Any]:
    """
    Fallback deterministic analysis when no AI provider is configured.
    """
    evidence_list = []
    mitre_techniques = []
    suspicious_reasons = []
    recommendations = [
        "Isolate the endpoint immediately using EDR host containment.",
        "Inspect active network sockets and terminate suspect processes.",
        "Check persistence entries in the startup registry folder."
    ]

    for alert in alerts:
        evidence_list.append(f"{alert.title}: {alert.description}")
        if alert.mitre_technique and alert.mitre_technique not in mitre_techniques:
            mitre_techniques.append(alert.mitre_technique)
            
        if "RULE_SUSPICIOUS_PATH" in alert.rule_name:
            suspicious_reasons.append("Binary executed from a temporary downloads directory, which is a common payload staging technique.")
        elif "RULE_SUSPICIOUS_CHAIN" in alert.rule_name:
            suspicious_reasons.append("A parent user process spawned a command-line interpreter, indicating possible remote shell execution.")
            recommendations.append("Audit user shell logs and check parent process command lines.")
        elif "RULE_CMDLINE_PATTERN" in alert.rule_name:
            suspicious_reasons.append("PowerShell parameter obfuscation or command downloading signatures detected.")
        elif "RULE_FILE_INTEGRITY_CHANGED" in alert.rule_name:
            suspicious_reasons.append("FIM: Cryptographic modification detected on monitored security file.")
            recommendations.append("Revert the file from a known secure backup and review file write logs.")
        elif "RULE_REPEATED_AUTH_FAILURES" in alert.rule_name:
            suspicious_reasons.append("Authentication: Brute force login attempts detected.")
            recommendations.append("Lock user account temporarily and check remote login source IPs.")

    summary = (
        f"Local Security Assessment: Incident INC-{incident.id} represents suspicious behavior "
        f"affecting host {incident.agent_id[:8]} with an overall risk score of {incident.risk_score}/100. "
        f"Detections map to MITRE technique(s): {', '.join(mitre_techniques) if mitre_techniques else 'None'}. "
        f"Verify telemetry details manually."
    )

    return {
        "summary": summary,
        "suspicious_reasons": suspicious_reasons or ["Aggregated alert triggers exceed baseline threat indicators."],
        "recommendations": recommendations,
        "attack_sequence": "Spawn -> Command Execution -> Action on Objectives",
        "limitations": "Offline analysis mode — configure an AI provider for LLM contextual reasoning."
      }

async def analyze_incident_threat(incident_id: int, db: Session) -> Dict[str, Any]:
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        return {"error": "Incident not found"}

    alerts = db.query(models.Alert).filter(models.Alert.incident_id == incident_id).all()
    
    # Check if AI is configured
    provider = settings.AI_PROVIDER
    api_key = settings.AI_API_KEY
    
    if not provider or provider.lower() == "none" or (provider == "openai" and not api_key):
        return generate_local_offline_analysis(incident, alerts)

    # Reconstruct prompt context
    alerts_context = []
    for alert in alerts:
        alerts_context.append(f"- Alert: {alert.title}\n  Description: {alert.description}\n  Evidence: {alert.evidence}")

    prompt = f"""
You are a senior SOC analyst assistant. Analyze this EDR security incident:
Incident ID: INC-{incident.id}
Affected Agent ID: {incident.agent_id}
Overall Incident Risk Score: {incident.risk_score}/100
Severity: {incident.severity}

Correlated Alerts:
{"\n".join(alerts_context)}

Respond in structured JSON format with these exact keys:
1. "summary" (detailed string incident summary)
2. "suspicious_reasons" (list of strings explaining why this is suspicious)
3. "recommendations" (list of specific containment and remediation recommendations)
4. "attack_sequence" (string summarizing the potential attack path)
5. "limitations" (string explaining limitations of this automated analysis)
Do not return any extra markdown formatting or preambles, return raw JSON string.
"""

    try:
        if provider == "openai":
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post("https://api.openai.com/v1/chat/completypes", json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    import json
                    return json.loads(content)
                else:
                    logger.error(f"OpenAI API failed: {res.text}. Falling back to offline analyzer.")
                    return generate_local_offline_analysis(incident, alerts)

        elif provider == "ollama":
            url = f"{settings.OLLAMA_URL}/api/generate"
            payload = {
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    import json
                    return json.loads(data["response"])
                else:
                    logger.warning("Ollama connection failed. Falling back to offline analyzer.")
                    return generate_local_offline_analysis(incident, alerts)
                    
    except Exception as e:
        logger.error(f"AI Assistant failed: {e}. Falling back to offline analyzer.")
        
    return generate_local_offline_analysis(incident, alerts)
