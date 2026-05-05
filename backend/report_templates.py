"""
Alternative PDF report templates. The original report_generator.py
remains the default ('standard'). These templates plug into the same
PDF endpoint via a `template` query parameter and re-use the
SAME inputs (story, analysis, test_cases, explanations).

Templates:
  - iso29119      : ISO/IEC/IEEE 29119-3 inspired test specification.
  - one_pager     : Concise single-page executive summary.
  - client_summary: Non-technical, business-tone summary for stakeholders.
"""
from io import BytesIO
from datetime import datetime
from collections import Counter

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.lib import colors


PRIMARY = HexColor("#0F172A")
ACCENT  = HexColor("#2563EB")
MUTED   = HexColor("#64748B")
LIGHT   = HexColor("#F1F5F9")
BORDER  = HexColor("#CBD5E1")
GOOD    = HexColor("#059669")
WARN    = HexColor("#D97706")
BAD     = HexColor("#DC2626")


SUPPORTED_TEMPLATES = ("iso29119", "one_pager", "client_summary")


def generate_pdf_with_template(
    template: str,
    story: str,
    analysis: dict,
    test_cases: list,
    explanations: list,
) -> bytes:
    """Dispatcher. Raises ValueError for unknown templates."""
    template = (template or "iso29119").lower()
    if template == "iso29119":
        return _iso29119(story, analysis, test_cases, explanations)
    if template == "one_pager":
        return _one_pager(story, analysis, test_cases, explanations)
    if template == "client_summary":
        return _client_summary(story, analysis, test_cases, explanations)
    raise ValueError(
        f"Unknown template '{template}'. Supported: {', '.join(SUPPORTED_TEMPLATES)}"
    )


# ───────── shared style helpers ─────────
def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("DocTitle", parent=s["Title"], fontSize=20,
                         textColor=PRIMARY, alignment=TA_LEFT, spaceAfter=2 * mm,
                         fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("DocSub", parent=s["Normal"], fontSize=10,
                         textColor=MUTED, spaceAfter=6 * mm))
    s.add(ParagraphStyle("H2", parent=s["Heading2"], fontSize=13,
                         textColor=ACCENT, spaceBefore=5 * mm, spaceAfter=2 * mm,
                         fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("H3", parent=s["Heading3"], fontSize=11,
                         textColor=PRIMARY, spaceBefore=3 * mm, spaceAfter=1 * mm,
                         fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("Body", parent=s["Normal"], fontSize=9.5,
                         textColor=PRIMARY, alignment=TA_JUSTIFY, leading=14,
                         spaceAfter=2 * mm))
    s.add(ParagraphStyle("Small", parent=s["Normal"], fontSize=8,
                         textColor=MUTED))
    s.add(ParagraphStyle("Centered", parent=s["Normal"], fontSize=10,
                         textColor=PRIMARY, alignment=TA_CENTER))
    return s


def _doc(buf: BytesIO, margin_cm=2):
    return SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=margin_cm * cm, rightMargin=margin_cm * cm,
        topMargin=margin_cm * cm, bottomMargin=margin_cm * cm,
    )


def _kv_table(rows, styles):
    wrapped = [[Paragraph(str(k), styles["Body"]),
                Paragraph(str(v), styles["Body"])] for k, v in rows]
    t = Table(wrapped, colWidths=[5 * cm, 11 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("GRID",       (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _category_counts(test_cases):
    counts = Counter((tc.get("category") or "uncategorised") for tc in test_cases)
    return counts


def _type_counts(test_cases):
    return Counter((tc.get("type") or "unknown") for tc in test_cases)


# ───────── 1. ISO 29119 inspired template ─────────
def _iso29119(story, analysis, test_cases, explanations) -> bytes:
    buf = BytesIO()
    doc = _doc(buf)
    s = _styles()
    el = []

    el.append(Paragraph("Test Case Specification", s["DocTitle"]))
    el.append(Paragraph(
        f"Inspired by ISO/IEC/IEEE 29119-3 &middot; Generated {datetime.now().strftime('%B %d, %Y')}",
        s["DocSub"],
    ))
    el.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=4 * mm))

    # 1. Identification
    el.append(Paragraph("1. Identification", s["H2"]))
    el.append(_kv_table([
        ("Document Title",  "TestCraft Test Case Specification"),
        ("Document ID",     f"TCS-{datetime.now().strftime('%Y%m%d-%H%M')}"),
        ("Version",         "1.0"),
        ("Date Issued",     datetime.now().strftime("%Y-%m-%d")),
        ("Status",          "Draft"),
    ], s))
    el.append(Spacer(1, 4 * mm))

    # 2. Scope
    el.append(Paragraph("2. Scope and Objective", s["H2"]))
    el.append(Paragraph(
        "This document specifies the test cases derived automatically from "
        "the user requirement provided below. The cases are categorised by "
        "type (positive, negative, boundary) and by purpose (happy path, "
        "input validation, authentication, error handling, boundary analysis, "
        "precondition validation).",
        s["Body"],
    ))

    # 3. Source Requirement
    el.append(Paragraph("3. Source Requirement", s["H2"]))
    el.append(Paragraph(f'"{story}"', s["Body"]))
    el.append(_kv_table([
        ("Actor",     analysis.get("actor", "N/A") or "N/A"),
        ("Action",    analysis.get("action", "N/A") or "N/A"),
        ("Outcome",   analysis.get("outcome") or "Not specified"),
        ("Conditions", "; ".join(c.get("context", "") for c in analysis.get("conditions", [])) or "None"),
    ], s))

    # 4. Test Case Set
    el.append(PageBreak())
    el.append(Paragraph("4. Test Case Set", s["H2"]))
    for tc in test_cases:
        el.append(Paragraph(f'4.{test_cases.index(tc)+1} {tc.get("id","")} &mdash; {tc.get("title","")}', s["H3"]))
        prio = ""
        if tc.get("priority_label"):
            prio = f' &middot; Priority: {tc["priority_label"]}'
        el.append(Paragraph(
            f'Type: {tc.get("type","")}  &middot; Category: {tc.get("category","")}{prio}',
            s["Small"],
        ))
        el.append(_kv_table([
            ("Preconditions", "<br/>".join(f"&bull; {p}" for p in (tc.get("preconditions") or [])) or "None"),
            ("Test Steps", "<br/>".join(f"{i+1}. {x}" for i, x in enumerate(tc.get("steps") or [])) or "None"),
            ("Expected Results", "<br/>".join(f"&bull; {x}" for x in (tc.get("expected_results") or [])) or "None"),
            ("Trigger / Trace", tc.get("source_trigger", "N/A")),
        ], s))
        el.append(Spacer(1, 3 * mm))

    # 5. Traceability
    el.append(PageBreak())
    el.append(Paragraph("5. Traceability Matrix", s["H2"]))
    rows = [["Test Case ID", "Title", "Triggered By"]]
    for tc in test_cases:
        rows.append([
            tc.get("id", ""),
            (tc.get("title", "") or "")[:60],
            (tc.get("source_trigger", "") or "")[:60],
        ])
    matrix = Table(rows, colWidths=[3 * cm, 7 * cm, 6 * cm], repeatRows=1)
    matrix.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8.5),
        ("GRID",       (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
    ]))
    el.append(matrix)

    doc.build(el)
    return buf.getvalue()


# ───────── 2. One-pager executive summary ─────────
def _one_pager(story, analysis, test_cases, explanations) -> bytes:
    buf = BytesIO()
    doc = _doc(buf, margin_cm=1.5)
    s = _styles()
    el = []

    el.append(Paragraph("TestCraft &mdash; Executive One-Pager", s["DocTitle"]))
    el.append(Paragraph(datetime.now().strftime("%B %d, %Y"), s["DocSub"]))
    el.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=3 * mm))

    el.append(Paragraph("Requirement", s["H2"]))
    el.append(Paragraph(f'"{story}"', s["Body"]))

    el.append(Paragraph("At-a-glance Coverage", s["H2"]))
    type_c = _type_counts(test_cases)
    cat_c  = _category_counts(test_cases)
    summary_rows = [
        ["Total cases", str(len(test_cases))],
        ["Positive",    str(type_c.get("positive", 0))],
        ["Negative",    str(type_c.get("negative", 0))],
        ["Boundary",    str(type_c.get("boundary", 0))],
        ["Categories covered", ", ".join(sorted(cat_c.keys()))],
    ]
    if any(tc.get("priority") for tc in test_cases):
        prio_c = Counter((tc.get("priority_label") or "Unspecified") for tc in test_cases)
        summary_rows.append([
            "Priority mix",
            "; ".join(f"{k}: {v}" for k, v in prio_c.most_common())
        ])

    sumtable = Table(summary_rows, colWidths=[5 * cm, 12 * cm])
    sumtable.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    el.append(sumtable)
    el.append(Spacer(1, 4 * mm))

    el.append(Paragraph("Top Test Cases (by priority)", s["H2"]))
    sorted_cases = sorted(
        test_cases,
        key=lambda x: -(x.get("priority") or 0),
    )[:5]
    for tc in sorted_cases:
        prio = tc.get("priority_label", "")
        el.append(Paragraph(
            f'<b>{tc.get("id","")}</b> &mdash; {tc.get("title","")}'
            + (f' <font color="{BAD.hexval()}">[{prio}]</font>' if prio else ""),
            s["Body"],
        ))
        if tc.get("expected_results"):
            el.append(Paragraph(f'Expected: {tc["expected_results"][0]}', s["Small"]))

    el.append(Spacer(1, 4 * mm))
    el.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    el.append(Paragraph(
        "Generated by TestCraft &mdash; lightweight, explainable test case generation.",
        s["Small"],
    ))

    doc.build(el)
    return buf.getvalue()


# ───────── 3. Client / business summary ─────────
def _client_summary(story, analysis, test_cases, explanations) -> bytes:
    buf = BytesIO()
    doc = _doc(buf)
    s = _styles()
    el = []

    el.append(Paragraph("Test Coverage Summary", s["DocTitle"]))
    el.append(Paragraph(
        f"Prepared for stakeholders &middot; {datetime.now().strftime('%B %d, %Y')}",
        s["DocSub"],
    ))
    el.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=4 * mm))

    el.append(Paragraph("What was tested?", s["H2"]))
    el.append(Paragraph(
        "Below is the requirement that was analysed. Our automated tool reviewed it and "
        "designed a set of tests that cover not only the expected flow but also common "
        "ways things can go wrong.",
        s["Body"],
    ))
    el.append(Paragraph(f'<i>"{story}"</i>', s["Body"]))

    el.append(Paragraph("How thorough is the coverage?", s["H2"]))
    type_c = _type_counts(test_cases)
    pos = type_c.get("positive", 0)
    neg = type_c.get("negative", 0)
    bnd = type_c.get("boundary", 0)
    el.append(Paragraph(
        f"We produced <b>{len(test_cases)} tests</b> in total: "
        f"<font color='{GOOD.hexval()}'>{pos} happy-path</font>, "
        f"<font color='{BAD.hexval()}'>{neg} failure-mode</font>, "
        f"and <font color='{WARN.hexval()}'>{bnd} edge-case</font> tests. "
        "Together these check that the feature works as intended, "
        "behaves gracefully when something goes wrong, and handles unusual inputs.",
        s["Body"],
    ))

    el.append(Paragraph("What does each test check, in plain language?", s["H2"]))
    for tc in test_cases:
        ttype = (tc.get("type") or "").lower()
        colour = GOOD if ttype == "positive" else (WARN if ttype == "boundary" else BAD)
        el.append(Paragraph(
            f'<font color="{colour.hexval()}"><b>&bull; {tc.get("title","")}</b></font>',
            s["Body"],
        ))
        if tc.get("expected_results"):
            el.append(Paragraph(
                f'<i>What "good" looks like: {tc["expected_results"][0]}</i>',
                s["Small"],
            ))
        el.append(Spacer(1, 1.5 * mm))

    el.append(Spacer(1, 4 * mm))
    el.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    el.append(Paragraph(
        "If you'd like a deeper technical breakdown of any test above, request the standard "
        "engineering report.",
        s["Small"],
    ))

    doc.build(el)
    return buf.getvalue()
