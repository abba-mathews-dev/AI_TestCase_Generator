"""
TestCraft API - Converts user stories to structured test cases
with full explainability. Lightweight FastAPI backend.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
import io

from nlp_parser import parse_user_story
from test_generator import generate_test_cases
from explainability import build_explanations
from report_generator import generate_pdf_report
from report_templates import generate_pdf_with_template, SUPPORTED_TEMPLATES
from script_exporter import export_script, SUPPORTED_FRAMEWORKS
from risk_scorer import score_test_cases

app = FastAPI(title="TestCraft API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserStoryRequest(BaseModel):
    story: str


class ReportRequest(BaseModel):
    story: str
    analysis: dict
    test_cases: list
    explanations: list


class PrioritizeRequest(BaseModel):
    story: str = ""
    test_cases: list


class ScriptExportRequest(BaseModel):
    story: str
    test_cases: list


@app.post("/api/analyze")
def analyze_story(req: UserStoryRequest):
    """Parse user story, generate test cases, and provide explanations."""
    if not req.story.strip():
        raise HTTPException(400, "User story cannot be empty")

    analysis = parse_user_story(req.story)
    test_cases = generate_test_cases(analysis)
    explanations = build_explanations(analysis, test_cases)

    return {
        "analysis": analysis,
        "test_cases": test_cases,
        "explanations": explanations,
    }


@app.post("/api/report")
def export_report(
    req: ReportRequest,
    template: str = Query(
        "standard",
        description=(
            "Report template. 'standard' = original engineering report. "
            "Alternatives: 'iso29119', 'one_pager', 'client_summary'."
        ),
    ),
):
    """Generate a professional PDF report. The original 'standard' template
    is unchanged; alternative templates are produced by report_templates.py."""
    template = (template or "standard").lower()

    if template == "standard":
        pdf_bytes = generate_pdf_report(
            story=req.story,
            analysis=req.analysis,
            test_cases=req.test_cases,
            explanations=req.explanations,
        )
        filename = "testcraft_report.pdf"
    elif template in SUPPORTED_TEMPLATES:
        pdf_bytes = generate_pdf_with_template(
            template=template,
            story=req.story,
            analysis=req.analysis,
            test_cases=req.test_cases,
            explanations=req.explanations,
        )
        filename = f"testcraft_report_{template}.pdf"
    else:
        raise HTTPException(
            400,
            f"Unknown template '{template}'. "
            f"Supported: standard, {', '.join(SUPPORTED_TEMPLATES)}.",
        )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/prioritize")
def prioritize(req: PrioritizeRequest):
    """Annotate each test case with a 1-5 priority, P-label, and reasons.
    Returns a NEW list - the input is not mutated. Frontend can call this
    after /api/analyze to display priority badges and reorder cases."""
    enriched = score_test_cases(req.test_cases, req.story)
    return {"test_cases": enriched}


@app.post("/api/export/script")
def export_script_endpoint(
    req: ScriptExportRequest,
    framework: str = Query(
        "pytest",
        description=f"One of: {', '.join(SUPPORTED_FRAMEWORKS)}",
    ),
):
    """Convert generated test cases into a runnable test-script skeleton
    for the requested framework. The TestCraft source_trigger of each case
    is preserved as a docstring/comment so traceability survives."""
    try:
        filename, mimetype, body = export_script(
            framework=framework,
            story=req.story,
            test_cases=req.test_cases,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    return Response(
        content=body,
        media_type=mimetype,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "features": {
            "templates": list(SUPPORTED_TEMPLATES),
            "script_frameworks": list(SUPPORTED_FRAMEWORKS),
            "prioritize": True,
        },
    }
