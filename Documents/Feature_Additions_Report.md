# TestCraft — Feature Additions Report (v1.1)

> A record of the six additive enhancements applied on top of the original
> TestCraft prototype described in `Dissertation_Document.docx`. **No
> existing module was rewritten or replaced** — every feature is a new
> file or a strictly additive extension to an existing file. The original
> `/api/analyze`, `/api/report` (default `template=standard`),
> `/api/health`, the spaCy NLP pipeline, the rule-based generator, the
> explainability engine, and the React UI behaviour all remain
> bit-for-bit equivalent when the new options are not used.

---

## 0. Summary of additions

| # | Feature | Layer | New artefact |
|---|---|---|---|
| 1 | Executable Test Script Generator | Backend | `backend/script_exporter.py` |
| 2 | Risk / Priority Scorer | Backend | `backend/risk_scorer.py` |
| 3 | Alternative PDF Report Templates | Backend | `backend/report_templates.py` |
| 4 | Analytics Dashboard | Frontend | `frontend/src/components/DashboardPanel.js` |
| 5 | Inline Test Case Editor | Frontend | `frontend/src/components/TestCaseEditor.js` |
| 6 | Audience-aware Explanation Toggle | Frontend | extension of `frontend/src/components/ExplanationPanel.js` |

Three new backend endpoints expose the new capabilities:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/report?template=...` | Existing endpoint — accepts a new optional `template` query parameter (`standard`, `iso29119`, `one_pager`, `client_summary`). When `template` is omitted or `standard`, behaviour is identical to v1.0. |
| `POST` | `/api/prioritize` | Returns the same test cases enriched with `priority`, `priority_label`, and `priority_reasons`. |
| `POST` | `/api/export/script?framework=...` | Returns a runnable test-script skeleton for `pytest`, `playwright`, `cypress`, `postman`, or `cucumber`. |

No new Python or npm dependency was introduced. ReportLab (already used)
covers the new PDF templates; the Dashboard uses inline SVG so it
needs no charting library.

---

## 1. Executable Test Script Generator (Feature #3)

**File added:** `backend/script_exporter.py`
**Endpoint added:** `POST /api/export/script?framework=<framework>`
**Frontend touch points:** new entries in the Export menu in
`App.js`; new helper `downloadScript` in `frontend/src/utils/api.js`.

### What it does
The structured test cases produced by `test_generator.py` are
descriptive — useful, but not directly executable. The new exporter
*translates* those cases into a runnable skeleton in the user's
chosen framework, while preserving every TestCraft `source_trigger`
as a docstring or comment so traceability survives in code form.

### Supported frameworks

| Key | Output file | Style |
|---|---|---|
| `pytest`     | `test_testcraft.py` | Pytest test functions with a stub `driver` fixture |
| `playwright` | `testcraft.spec.js` | `test.describe` block with `async ({ page })` tests |
| `cypress`    | `testcraft.cy.js` | `describe / it` blocks |
| `postman`    | `testcraft.postman_collection.json` | Postman collection v2.1 with `test` scripts |
| `cucumber`   | `testcraft.feature` | Gherkin `Feature` with `Scenario / Given / When / Then` |

### Why it strengthens the dissertation
Closes the long-standing critique of NLP test-case generators that
"cases are descriptions, never artifacts." The exporter is a *pure
transformer* over the existing JSON contract — it does not modify the
NLP pipeline, the generator, or the explainability layer, so the
original empirical results in §4 of the dissertation remain valid.

---

## 2. Risk / Priority Scorer (Feature #4)

**File added:** `backend/risk_scorer.py`
**Endpoint added:** `POST /api/prioritize`
**Frontend touch points:** new "Prioritize" button in the header of
`App.js`; new helper `prioritizeTestCases` in `api.js`; new
`PriorityBadge` component inside `TestCasesPanel.js`.

### Scoring approach
Heuristic, deterministic, and **fully explainable** (consistent with
TestCraft's design philosophy). No ML model is loaded.

* **Base score** comes from the test category — authentication=5,
  error_handling=4, precondition_validation=4, input_validation=3,
  boundary_analysis=3, happy_path=3.
* **Type nudge** — `negative` adds +1, `positive` subtracts −1.
* **Keyword scan** of the title, steps, expected results, and original
  user story against a curated high-risk vocabulary
  (`payment`, `delete`, `password`, `admin`, `pii`, …) and a
  medium-risk vocabulary (`register`, `email`, `submit`, …).
* Result is clamped to **1–5** and labelled
  `P1 - Critical | P1 - High | P2 - Medium | P3 - Low | P3 - Trivial`.

Each test case carries a `priority_reasons: [...]` list that names
the contributing factors. The list is shown in the badge tooltip on
the UI, satisfying the explainability commitment for this new
feature too.

### Effect on UI
A new amber/red **priority badge** appears on each test-case card
once the user clicks **Prioritize**. The list is also re-sorted
(highest priority first), and the dashboard adds a "Priority Mix"
chart and an "Avg priority" KPI.

---

## 3. Alternative PDF Report Templates (Feature #8)

**File added:** `backend/report_templates.py`
**Existing file modified:** `backend/main.py` — `/api/report` now
accepts an optional `?template=...` query parameter; when omitted or
set to `standard`, the **original `report_generator.py` is invoked
unchanged**.

### Templates

| Key | Persona | Sections |
|---|---|---|
| `iso29119` | QA / Compliance | Identification → Scope → Source Requirement → Test Case Set (numbered §4.x) → Traceability Matrix |
| `one_pager` | Engineering manager / sprint review | Requirement, at-a-glance coverage table, top-5 cases by priority |
| `client_summary` | Non-technical stakeholder | Plain-English coverage statement, colour-coded test list, no jargon |

Each template uses the **same input contract** as the original report
(`story`, `analysis`, `test_cases`, `explanations`) so swapping
templates requires no change to the analysis flow.

### Why this matters academically
Demonstrates that the explainability data model is rich enough to
drive multiple audience-tailored views from a single source of truth
— a concrete instance of the *category-specific reasoning chain*
philosophy described in §3.2.4 of the dissertation, applied at the
*report* level.

---

## 4. Analytics Dashboard (Feature #9)

**File added:** `frontend/src/components/DashboardPanel.js`
**Existing files extended:** `App.js` (new "Dashboard" tab),
`App.css` (new `dashboard-panel`, `dash-*` rules at the bottom only).

### What it shows
Reads exclusively from the existing `/api/analyze` response payload
(plus the optional priorities returned by `/api/prioritize`):

* **KPI strip** — total cases, categories covered, explanation count,
  average priority (when available).
* **Pie chart** — test type distribution (positive / negative / boundary).
* **Horizontal bar chart** — cases per category.
* **Horizontal bar chart** — priority mix (only rendered after the
  user has prioritized).
* **Confidence donut** — proportion of high-confidence explanations,
  with a one-line interpretation.

All charts are **inline SVG**. No new npm dependency is added; the
`package.json` is untouched.

---

## 5. Inline Test Case Editor (Feature #11)

**File added:** `frontend/src/components/TestCaseEditor.js`
**Existing files extended:** `TestCasesPanel.js` (new edit-button
column in each card header), `App.js` (modal state +
`handleSaveEdit`), `App.css` (new `tce-*` rules).

### Behaviour
* Click the pencil icon on any test-case card.
* A centred modal opens with editable fields for **title, type,
  category, preconditions, steps, expected results**.
* Add / remove rows with `+ Add` and the trash icon.
* On Save, the test case in React state is replaced with the edited
  version. A small **edited** pill appears on the card and the card
  gains a left accent border to make the change visible.
* Subsequent **PDF, Excel, and script exports automatically use the
  edited content** — there is no separate "save" step needed because
  state is single-source-of-truth in `App.js`.

### Why this fits MCA-level scope
Adds genuine *direct-manipulation UX* (a real desktop-grade pattern)
without introducing a backend persistence layer, keeping the
architectural contract from §3 of the dissertation intact.

---

## 6. Audience-aware Explanation Toggle (Feature #13)

**Existing file modified:** `frontend/src/components/ExplanationPanel.js`
(extended; original behaviour preserved when audience = `tester`).
**New CSS:** `exp-audience-bar`, `exp-audience-tabs`,
`exp-audience-blurb`, `exp-audience-summary` rules in `App.css`.

### What it does
Adds a three-button segmented control above the explanation list:

| Audience | Adaptation |
|---|---|
| **Tester** (default) | Identical to original v1.0 wording. |
| **Manager** | Re-frames each reasoning line in business language: "NLP parser" → "requirement analyser", "ISTQB" → "industry standard", "boundary value analysis" → "edge-case checks". Adds a one-line confidence summary above each card. |
| **Developer** | Re-frames in code-oriented language: "user-facing input" → "input field / form parameter", "missing/empty data" → "null / empty argument", "system-level errors" → "runtime errors (network, timeout, 5xx)". |

Adaptation is a pure client-side string-rewrite. **No backend call is
added**, no extra latency is introduced, and the underlying
explanation array is never mutated.

### Why this is dissertation-relevant
Directly addresses §5.2 of the dissertation, which highlights
"category-specific reasoning chains [provide] contextually relevant
explanations rather than generic justifications." This feature
extends that principle from *category awareness* to *audience
awareness*, demonstrating that the explainability data model
supports re-presentation without re-computation.

---

## 7. File-by-file change log

### Added (new files)
* `backend/script_exporter.py`
* `backend/risk_scorer.py`
* `backend/report_templates.py`
* `frontend/src/components/DashboardPanel.js`
* `frontend/src/components/TestCaseEditor.js`
* `Documents/Feature_Additions_Report.md` (this document)

### Extended (additive only — original behaviour preserved)
* `backend/main.py` — added imports, two request models, new
  `?template=` parameter on `/api/report`, two new endpoints
  (`/api/prioritize`, `/api/export/script`), and a richer `/api/health`
  payload listing the new capabilities. The default code path of
  `/api/report` (no template, or `template=standard`) still calls
  the original `report_generator.py`.
* `frontend/src/App.js` — added Dashboard tab, "Prioritize" header
  button, expanded Export menu (PDF templates + script frameworks),
  and editor modal wiring.
* `frontend/src/utils/api.js` — added `downloadScript`,
  `prioritizeTestCases`, and a `template` parameter on
  `downloadReport` (defaults to original behaviour).
* `frontend/src/components/TestCasesPanel.js` — added
  `PriorityBadge` and an `onEdit` prop. The component remains
  fully functional when these props are absent.
* `frontend/src/components/ExplanationPanel.js` — added the audience
  toggle and adapter functions. With audience = `tester` (default),
  output text is identical to v1.0.
* `frontend/src/styles/App.css` — appended a new section labelled
  *"ADDITIONS (v1.1)"*. **Nothing above this section was modified.**

### Untouched (verified)
* `backend/nlp_parser.py`
* `backend/test_generator.py`
* `backend/explainability.py`
* `backend/report_generator.py`
* `backend/requirements.txt`
* `frontend/src/components/InputPanel.js`
* `frontend/src/components/AnalysisPanel.js`
* `frontend/src/components/SummaryBar.js`
* `frontend/package.json`

---

## 8. How to use the new capabilities

1. Run the backend and frontend exactly as before
   (`./run.bat` then `npm start`).
2. Enter a user story and click **Generate Test Cases** (unchanged).
3. **New options become visible only after a successful analysis:**
   * Click **Prioritize** in the header — every card now shows a
     P-label badge and the cases re-sort by descending priority.
   * Click any **pencil icon** on a test-case card to edit that case
     in-place. Subsequent exports use the edited content.
   * Click **Dashboard** in the tab bar to see KPIs and charts.
   * Inside **Explainability**, click *Manager* or *Developer* in the
     "Read as:" toggle to re-frame the reasoning text.
   * Click **Export** → choose any of the four PDF templates, the
     Excel sheet, or one of the five test-script frameworks.

---

## 9. How to discuss this in the dissertation update

Suggested mapping into the existing chapter structure:

| Dissertation section | Suggested addition |
|---|---|
| §1.4 Novelty and Contribution | One additional paragraph on *audience-aware explainability* and *executable artefact emission*, framed as natural extensions of the existing core principles. |
| §3.2 System Workflow | Add §3.2.6 "Risk Scoring", §3.2.7 "Multi-template Reporting", and §3.2.8 "Executable Script Export". Each follows the same structure as §3.2.5. |
| §3.2.4 Explainability Engine | Add a paragraph on the audience adapter, with the table from §6 above. |
| §3.2.5 Reporting | Replace the single-paragraph reporting description with a comparison of the four templates. |
| §4.2 Detailed Module Results | Add precision/recall numbers for the priority scorer (against a small labelled set you can annotate from your existing 20-story corpus). |
| §4.4 Comparative Analysis | Refresh Table 4 to add a row for "Audience-tailored explanations" and "Executable script export" — both of which the existing commercial tools either lack or charge for. |
| §5.3 Future Research Directions | Two of the original future-work bullets (multi-template reports and executable artefacts) are now closed; rephrase to point at *next* steps such as a feedback-driven priority retraining loop. |
| Appendix A | Add screenshots: dashboard, editor modal, audience toggle, the three new PDF templates, an exported pytest file. |
| Appendix B | Append the contracts of the three new endpoints and a code excerpt from each new module. |

---

*Document version: 1.0 — generated alongside the v1.1 code drop.*
