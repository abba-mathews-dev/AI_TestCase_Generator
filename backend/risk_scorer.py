"""
Risk / Priority Scorer - Assigns each generated test case a 1-5
priority and a P1/P2/P3 severity label, plus a transparent reason
list explaining the score. Heuristic-only (no ML model required),
which keeps it fast, offline, and aligned with TestCraft's
explainability commitment.

Scoring philosophy:
  - High-risk categories (auth, payment, security, deletion) score higher.
  - Negative & error-handling cases are inherently more important than
    happy paths because regressions there are silent in production.
  - Boundary cases score moderately - they catch many real defects.
  - Each contributing factor is recorded so the user can see WHY the
    score came out the way it did.
"""
from typing import List

# Keyword tables
HIGH_RISK_KEYWORDS = {
    "payment", "pay", "checkout", "billing", "credit", "card",
    "delete", "remove", "purge", "drop",
    "password", "credential", "token", "auth", "login", "logout",
    "admin", "permission", "role", "privilege",
    "personal", "pii", "ssn", "medical", "patient",
    "transfer", "withdraw", "deposit", "balance",
}

MEDIUM_RISK_KEYWORDS = {
    "register", "signup", "email", "verify", "reset",
    "upload", "download", "import", "export",
    "search", "filter", "submit", "save", "update", "edit",
    "order", "cart", "subscribe",
}

CATEGORY_BASE_SCORE = {
    "authentication":           5,
    "error_handling":           4,
    "precondition_validation":  4,
    "input_validation":         3,
    "boundary_analysis":        3,
    "happy_path":               3,
}

TYPE_NUDGE = {
    "negative":  +1,
    "boundary":   0,
    "positive":  -1,
}


def score_test_cases(test_cases: List[dict], story: str = "") -> List[dict]:
    """
    Returns a NEW list of test cases with three extra fields per case:
        priority         : int 1-5  (5 = run first / highest risk)
        priority_label   : str P1/P2/P3
        priority_reasons : list[str]
    Original list is not mutated.
    """
    story_lower = (story or "").lower()
    enriched = []
    for tc in test_cases:
        score, reasons = _score_one(tc, story_lower)
        out = dict(tc)
        out["priority"] = score
        out["priority_label"] = _label(score)
        out["priority_reasons"] = reasons
        enriched.append(out)
    enriched.sort(key=lambda x: (-x["priority"], x.get("id", "")))
    return enriched


def _score_one(tc: dict, story_lower: str) -> tuple[int, list[str]]:
    reasons: list[str] = []
    category = (tc.get("category") or "").lower()
    tc_type = (tc.get("type") or "").lower()

    # Base from category
    base = CATEGORY_BASE_SCORE.get(category, 3)
    score = base
    reasons.append(f"Base score {base} from category '{category or 'unknown'}'")

    # Type nudge
    nudge = TYPE_NUDGE.get(tc_type, 0)
    if nudge:
        score += nudge
        sign = "+" if nudge > 0 else ""
        reasons.append(f"Type '{tc_type}' adjusts score by {sign}{nudge}")

    # Keyword scan across title + steps + expected_results + story
    haystack = " ".join([
        tc.get("title") or "",
        " ".join(tc.get("steps") or []),
        " ".join(tc.get("expected_results") or []),
        story_lower,
    ]).lower()

    high_hits = sorted({k for k in HIGH_RISK_KEYWORDS if k in haystack})
    if high_hits:
        score += 1
        reasons.append(f"High-risk keyword(s) detected: {', '.join(high_hits[:4])}")

    med_hits = sorted({k for k in MEDIUM_RISK_KEYWORDS if k in haystack})
    if med_hits and not high_hits:
        # Don't double-stack with high-risk
        reasons.append(f"Medium-risk keyword(s) detected: {', '.join(med_hits[:4])}")

    # Clamp to 1..5
    if score > 5:
        score = 5
        reasons.append("Capped at maximum priority 5")
    if score < 1:
        score = 1
        reasons.append("Floored at minimum priority 1")

    return score, reasons


def _label(score: int) -> str:
    if score >= 5:
        return "P1 - Critical"
    if score == 4:
        return "P1 - High"
    if score == 3:
        return "P2 - Medium"
    if score == 2:
        return "P3 - Low"
    return "P3 - Trivial"
