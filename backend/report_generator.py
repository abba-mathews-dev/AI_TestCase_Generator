"""
Report Generator - Creates professional, industry-standard
PDF reports from analysis results using ReportLab.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime


BRAND_PRIMARY = HexColor("#1a1a2e")
BRAND_ACCENT = HexColor("#0f3460")
BRAND_HIGHLIGHT = HexColor("#e94560")
BRAND_LIGHT = HexColor("#f5f5f5")
BRAND_BORDER = HexColor("#dddddd")
TEXT_DARK = HexColor("#222222")
TEXT_MUTED = HexColor("#666666")


def _get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontSize=22, textColor=BRAND_PRIMARY, spaceAfter=4 * mm,
        alignment=TA_LEFT, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"],
        fontSize=11, textColor=TEXT_MUTED, spaceAfter=8 * mm,
        fontName="Helvetica",
    ))
    styles.add(ParagraphStyle(
        "SectionHead", parent=styles["Heading2"],
        fontSize=14, textColor=BRAND_ACCENT, spaceBefore=6 * mm,
        spaceAfter=3 * mm, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "SubSection", parent=styles["Heading3"],
        fontSize=11, textColor=BRAND_PRIMARY, spaceBefore=4 * mm,
        spaceAfter=2 * mm, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "BodyText2", parent=styles["Normal"],
        fontSize=9.5, textColor=TEXT_DARK, spaceAfter=2 * mm,
        fontName="Helvetica", alignment=TA_JUSTIFY, leading=14,
    ))
    styles.add(ParagraphStyle(
        "SmallMuted", parent=styles["Normal"],
        fontSize=8, textColor=TEXT_MUTED, fontName="Helvetica",
    ))
    styles.add(ParagraphStyle(
        "TCTitle", parent=styles["Normal"],
        fontSize=10, textColor=BRAND_PRIMARY, fontName="Helvetica-Bold",
        spaceAfter=1 * mm,
    ))
    return styles


def generate_pdf_report(story: str, analysis: dict, test_cases: list, explanations: list) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    styles = _get_styles()
    elements = []

    # ─── Header ───
    elements.append(Paragraph("TestCraft Report", styles["ReportTitle"]))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}",
        styles["ReportSubtitle"],
    ))
    elements.append(HRFlowable(
        width="100%", thickness=1, color=BRAND_BORDER, spaceAfter=6 * mm,
    ))

    # ─── Section 1: Input ───
    elements.append(Paragraph("1. User Story Input", styles["SectionHead"]))
    elements.append(Paragraph(f'"{story}"', styles["BodyText2"]))
    elements.append(Spacer(1, 4 * mm))

    # ─── Section 2: Analysis ───
    elements.append(Paragraph("2. NLP Analysis", styles["SectionHead"]))

    analysis_data = [
        ["Component", "Extracted Value"],
        ["Actor", analysis.get("actor", "N/A")],
        ["Action", analysis.get("action", "N/A")],
        ["Outcome", analysis.get("outcome", "N/A") or "Not specified"],
    ]
    if analysis.get("conditions"):
        conds = "; ".join(c.get("context", "") for c in analysis["conditions"])
        analysis_data.append(["Conditions", conds])

    if analysis.get("verbs"):
        verb_list = ", ".join(v["text"] for v in analysis["verbs"])
        analysis_data.append(["Key Verbs", verb_list])

    if analysis.get("objects"):
        obj_list = ", ".join(o["text"] for o in analysis["objects"])
        analysis_data.append(["Key Objects", obj_list])

    # Wrap long text in Paragraphs
    wrapped = []
    for row in analysis_data:
        wrapped.append([
            Paragraph(str(row[0]), styles["BodyText2"]),
            Paragraph(str(row[1]), styles["BodyText2"]),
        ])

    t = Table(wrapped, colWidths=[4 * cm, 12 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BACKGROUND", (0, 1), (0, -1), BRAND_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BRAND_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 6 * mm))

    # ─── Section 3: Test Cases ───
    elements.append(Paragraph("3. Generated Test Cases", styles["SectionHead"]))

    for i, tc in enumerate(test_cases):
        elements.append(Paragraph(f'{tc["id"]} - {tc["title"]}', styles["TCTitle"]))

        type_label = tc.get("type", "").upper()
        cat_label = tc.get("category", "").replace("_", " ").title()
        elements.append(Paragraph(
            f'<font color="{BRAND_HIGHLIGHT}">[{type_label}]</font> &nbsp; Category: {cat_label}',
            styles["SmallMuted"],
        ))

        # Preconditions
        if tc.get("preconditions"):
            elements.append(Paragraph("<b>Preconditions:</b>", styles["BodyText2"]))
            for p in tc["preconditions"]:
                elements.append(Paragraph(f"&bull; {p}", styles["BodyText2"]))

        # Steps
        if tc.get("steps"):
            elements.append(Paragraph("<b>Test Steps:</b>", styles["BodyText2"]))
            for j, s in enumerate(tc["steps"], 1):
                elements.append(Paragraph(f"{j}. {s}", styles["BodyText2"]))

        # Expected Results
        if tc.get("expected_results"):
            elements.append(Paragraph("<b>Expected Results:</b>", styles["BodyText2"]))
            for e in tc["expected_results"]:
                elements.append(Paragraph(f"&bull; {e}", styles["BodyText2"]))

        elements.append(HRFlowable(
            width="100%", thickness=0.5, color=BRAND_BORDER,
            spaceBefore=3 * mm, spaceAfter=3 * mm,
        ))

    # ─── Section 4: Explainability ───
    elements.append(PageBreak())
    elements.append(Paragraph("4. Explainability & Reasoning", styles["SectionHead"]))
    elements.append(Paragraph(
        "Each test case below includes a transparent explanation of why it was generated "
        "and which part of the user story triggered it.",
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 3 * mm))

    for exp in explanations:
        elements.append(Paragraph(
            f'{exp["test_case_id"]} - {exp["test_case_title"]}',
            styles["SubSection"],
        ))

        elements.append(Paragraph(
            f'Confidence: <b>{exp.get("confidence", "N/A").upper()}</b>',
            styles["SmallMuted"],
        ))

        elements.append(Paragraph("<b>Reasoning Chain:</b>", styles["BodyText2"]))
        for r in exp.get("reasoning", []):
            elements.append(Paragraph(f"&rarr; {r}", styles["BodyText2"]))

        if exp.get("story_mapping"):
            elements.append(Paragraph("<b>Story Mapping:</b>", styles["BodyText2"]))
            for sm in exp["story_mapping"]:
                elements.append(Paragraph(
                    f'&bull; <b>{sm.get("element", "").title()}:</b> {sm.get("description", "")}',
                    styles["BodyText2"],
                ))

        elements.append(HRFlowable(
            width="100%", thickness=0.5, color=BRAND_BORDER,
            spaceBefore=2 * mm, spaceAfter=4 * mm,
        ))

    # ─── Footer ───
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph(
        "Report generated by TestCraft",
        styles["SmallMuted"],
    ))

    doc.build(elements)
    return buf.getvalue()
