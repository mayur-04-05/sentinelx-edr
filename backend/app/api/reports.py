from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from backend.app.database import get_db
from backend.app import models
from backend.app.security import rbac

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/incident/{incident_id}")
def generate_incident_report_pdf(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(rbac.allow_any)
):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    alerts = db.query(models.Alert).filter(models.Alert.incident_id == incident_id).all()
    agent = db.query(models.Agent).filter(models.Agent.id == incident.agent_id).first()

    # Create memory buffer
    buffer = io.BytesIO()
    
    # Setup document template
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#0F172A'), # Slate 900
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=12,
        spaceAfter=6,
        borderPadding=2
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        textColor=colors.HexColor('#334155'),
        leading=14
    )
    
    evidence_style = ParagraphStyle(
        'EvidenceText',
        parent=styles['Code'],
        fontSize=8,
        textColor=colors.HexColor('#475569'),
        leading=11
    )

    elements = []
    
    # Header Logo/Title banner
    elements.append(Paragraph("SENTINELX EDR &mdash; SECURITY INCIDENT REPORT", title_style))
    elements.append(Paragraph("Detect. Investigate. Respond.", ParagraphStyle('Sub', parent=body_style, fontSize=10, fontName='Helvetica-Oblique', spaceAfter=15)))
    elements.append(Spacer(1, 10))

    # Meta table data
    meta_data = [
        [
            Paragraph("<b>Incident ID:</b>", body_style), Paragraph(f"INC-{incident.id}", body_style),
            Paragraph("<b>Risk Score:</b>", body_style), Paragraph(f"{incident.risk_score}/100", body_style)
        ],
        [
            Paragraph("<b>Severity:</b>", body_style), Paragraph(f"{incident.severity}", body_style),
            Paragraph("<b>Status:</b>", body_style), Paragraph(f"{incident.status}", body_style)
        ],
        [
            Paragraph("<b>Affected Host:</b>", body_style), Paragraph(f"{agent.hostname if agent else 'Unknown'}", body_style),
            Paragraph("<b>Agent ID:</b>", body_style), Paragraph(f"{incident.agent_id[:18]}...", body_style)
        ],
        [
            Paragraph("<b>First Observed:</b>", body_style), Paragraph(f"{incident.first_seen.strftime('%Y-%m-%d %H:%M:%S')}", body_style),
            Paragraph("<b>Last Activity:</b>", body_style), Paragraph(f"{incident.last_seen.strftime('%Y-%m-%d %H:%M:%S')}", body_style)
        ]
    ]
    
    t = Table(meta_data, colWidths=[100, 160, 100, 160])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#F1F5F9')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    # Analyst notes
    elements.append(Paragraph("Analyst Investigation Notes", section_style))
    notes_txt = incident.analyst_notes or "No analyst notes registered."
    elements.append(Paragraph(notes_txt, body_style))
    elements.append(Spacer(1, 15))

    # Triggered alerts
    elements.append(Paragraph("Triggered Detection Alerts", section_style))
    if not alerts:
        elements.append(Paragraph("No alerts linked to this incident.", body_style))
    else:
        for idx, alert in enumerate(alerts, 1):
            elements.append(Paragraph(f"<b>{idx}. {alert.title}</b> &mdash; Severity: {alert.severity} (Score: {alert.risk_score})", body_style))
            elements.append(Paragraph(f"Rule triggered: {alert.rule_name} | MITRE Technique: {alert.mitre_technique or 'None'}", body_style))
            elements.append(Paragraph(f"Description: {alert.description}", body_style))
            elements.append(Paragraph(f"Evidence: {str(alert.evidence)}", evidence_style))
            elements.append(Spacer(1, 8))
            
    elements.append(Spacer(1, 10))

    # Containment details
    elements.append(Paragraph("Containment & Audit Actions Log", section_style))
    # Query response actions on this agent
    actions = db.query(models.ResponseAction).filter(models.ResponseAction.agent_id == incident.agent_id).all()
    if not actions:
        elements.append(Paragraph("No containment actions executed for this endpoint.", body_style))
    else:
        for act in actions:
            elements.append(Paragraph(
                f"&bull; <b>{act.action_type}</b> by {act.analyst} on {act.timestamp.strftime('%Y-%m-%d %H:%M:%S')} &rarr; Status: <b>{act.status}</b> ({act.result_message or 'N/A'})", 
                body_style
            ))
            
    # Build report document
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=sentinelx_report_INC_{incident.id}.pdf"}
    )
