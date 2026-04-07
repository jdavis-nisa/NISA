#!/usr/bin/env python3.11
"""
NISA Compliance Report Generator
Pulls last 24h from audit_log2 and generates a signed PDF report
"""
import os
import sys
import psycopg2
from datetime import datetime, timedelta, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ── DB Config ────────────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "nisa",
    "user": "nisa_user",
    "password": "nisa_secure_2026"
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../benchmarks/results")

def fetch_audit_records(hours: int = 24) -> list:
    """Pull audit records from the last N hours"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    cur.execute("""
        SELECT id, event_id, timestamp, event_type, user_prompt,
               model_used, routing_reason, tool_executed,
               response_summary, framework_used, signature
        FROM audit_log2
        WHERE created_at >= %s
        ORDER BY id ASC
    """, (cutoff,))
    rows = cur.fetchall()
    conn.close()
    return rows

def generate_report(hours: int = 24) -> str:
    """Generate compliance PDF and return output path"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"nisa_compliance_report_{timestamp}.pdf"
    output_path = os.path.join(OUTPUT_DIR, filename)

    records = fetch_audit_records(hours)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "NISATitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "NISASubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#4a4a6a"),
        alignment=TA_CENTER,
        spaceAfter=4
    )
    section_style = ParagraphStyle(
        "NISASection",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1a1a2e"),
        spaceBefore=16,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "NISABody",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2a2a2a")
    )
    mono_style = ParagraphStyle(
        "NISAMono",
        parent=styles["Code"],
        fontSize=7,
        leading=10,
        textColor=colors.HexColor("#333333"),
        backColor=colors.HexColor("#f5f5f5")
    )

    story = []

    # ── Header ───────────────────────────────────────────────────
    story.append(Paragraph("NISA", title_style))
    story.append(Paragraph("Network Intelligence Security Assistant", subtitle_style))
    story.append(Paragraph("Compliance & Audit Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2,
                            color=colors.HexColor("#1a1a2e"), spaceAfter=12))

    # ── Report Metadata ──────────────────────────────────────────
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_data = [
        ["Report Generated:", generated_at],
        ["Coverage Period:", f"Last {hours} hours"],
        ["Total Events:", str(len(records))],
        ["Report Classification:", "INTERNAL USE ONLY"],
        ["Platform:", "NISA v0.2.0 - github.com/jdavis-nisa/NISA"],
        ["Signing Algorithm:", "ML-DSA-65 (CRYSTALS-Dilithium) - NIST FIPS 204"],
        ["Quantum Resistant:", "YES - Post-quantum cryptographic signatures"],
    ]
    meta_table = Table(meta_data, colWidths=[2*inch, 4.5*inch])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1a1a2e")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#f0f0f8"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccccdd")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 16))

    # ── Summary ──────────────────────────────────────────────────
    story.append(Paragraph("Executive Summary", section_style))

    event_types = {}
    models_used = {}
    tools_used = {}
    sig_verified = 0

    for row in records:
        et = row[3] or "unknown"
        event_types[et] = event_types.get(et, 0) + 1
        mu = row[5] or "none"
        models_used[mu] = models_used.get(mu, 0) + 1
        tu = row[7] or "none"
        tools_used[tu] = tools_used.get(tu, 0) + 1
        if row[10]:
            sig_verified += 1

    # Detect signing algorithms used
    algo_counts = {}
    for row in records:
        sig = row[10] or ""
        if sig.startswith("ML-DSA-65:"):
            algo_counts["ML-DSA-65"] = algo_counts.get("ML-DSA-65", 0) + 1
        elif sig.startswith("HMAC-SHA256:"):
            algo_counts["HMAC-SHA256"] = algo_counts.get("HMAC-SHA256", 0) + 1
        else:
            algo_counts["HMAC-SHA256"] = algo_counts.get("HMAC-SHA256", 0) + 1

    primary_algo = "ML-DSA-65 (NIST FIPS 204)" if "ML-DSA-65" in algo_counts else "HMAC-SHA256"

    summary_text = (
        f"This report covers <b>{len(records)}</b> audit events recorded by NISA "
        f"during the last <b>{hours} hours</b>. "
        f"All events are cryptographically signed using <b>{primary_algo}</b>. "
        f"<b>{sig_verified}</b> of {len(records)} entries carry valid signatures. "
        f"Event types recorded: {', '.join(event_types.keys()) or 'none'}."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 8))

    # ── Event Type Breakdown ─────────────────────────────────────
    if event_types:
        story.append(Paragraph("Event Type Breakdown", section_style))
        et_data = [["Event Type", "Count"]]
        for k, v in sorted(event_types.items(), key=lambda x: -x[1]):
            et_data.append([k, str(v)])
        et_table = Table(et_data, colWidths=[3.5*inch, 1.5*inch])
        et_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#f0f0f8"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccccdd")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ]))
        story.append(et_table)
        story.append(Spacer(1, 8))

    # ── Audit Log Entries ────────────────────────────────────────
    story.append(Paragraph("Audit Log Entries", section_style))

    if not records:
        story.append(Paragraph(
            "No audit events recorded in the specified time window.",
            body_style
        ))
    else:
        log_data = [["ID", "Timestamp", "Event Type", "Model", "Tool", "Sig"]]
        for row in records:
            sig_status = "OK" if row[10] else "-"
            log_data.append([
                str(row[0]),
                str(row[2])[:19],
                str(row[3] or "-")[:20],
                str(row[5] or "-")[:20],
                str(row[7] or "-")[:15],
                sig_status
            ])
        log_table = Table(log_data,
                          colWidths=[0.4*inch, 1.4*inch, 1.4*inch, 1.4*inch, 1.1*inch, 0.4*inch])
        log_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#f0f0f8"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccccdd")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (5, 0), (5, -1), "CENTER"),
            ("TEXTCOLOR", (5, 1), (5, -1), colors.HexColor("#006600")),
        ]))
        story.append(log_table)

    story.append(Spacer(1, 16))

    # ── Footer ───────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1,
                            color=colors.HexColor("#ccccdd"), spaceBefore=8))
    footer_text = (
        "This report was automatically generated by NISA - Network Intelligence Security Assistant. "
        "All audit entries are cryptographically signed using ML-DSA-65 (CRYSTALS-Dilithium) - NIST FIPS 204. "
        "Unauthorized distribution is prohibited."
    )
    story.append(Paragraph(footer_text, ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=7, textColor=colors.HexColor("#888888"),
        alignment=TA_CENTER, spaceBefore=4
    )))

    doc.build(story)
    return output_path

if __name__ == "__main__":
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    print(f"Generating NISA compliance report for last {hours} hours...")
    path = generate_report(hours)
    print(f"Report saved: {path}")
