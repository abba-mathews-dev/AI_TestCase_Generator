"""
Test Case Generator - Converts parsed user story analysis
into structured, non-redundant test cases.
"""
import hashlib
from typing import List


def _make_id(prefix: str, seed: str) -> str:
    """Generate a short deterministic test case ID."""
    h = hashlib.md5(seed.encode()).hexdigest()[:6].upper()
    return f"{prefix}-{h}"


def generate_test_cases(analysis: dict) -> List[dict]:
    """
    Generate test cases from parsed story analysis.
    Each test case includes: id, title, type, preconditions, steps, expected_results.
    """
    cases = []
    actor = analysis.get("actor") or "user"
    action = analysis.get("action") or ""
    outcome = analysis.get("outcome") or ""
    conditions = analysis.get("conditions", [])
    verbs = analysis.get("verbs", [])
    objects = analysis.get("objects", [])

    # === 1. Happy Path (Primary) ===
    happy_case = _build_happy_path(actor, action, outcome, conditions)
    cases.append(happy_case)

    # === 2. Precondition Validation Cases ===
    for cond in conditions:
        case = _build_condition_case(actor, action, cond)
        cases.append(case)

    # === 3. Negative / Edge Cases ===
    negative_cases = _build_negative_cases(actor, action, outcome, verbs, objects)
    cases.extend(negative_cases)

    # === 4. Boundary Cases (if applicable) ===
    boundary_cases = _build_boundary_cases(actor, action, objects)
    cases.extend(boundary_cases)

    # Deduplicate by title
    seen_titles = set()
    unique_cases = []
    for c in cases:
        if c["title"] not in seen_titles:
            seen_titles.add(c["title"])
            unique_cases.append(c)

    return unique_cases


def _build_happy_path(actor, action, outcome, conditions):
    preconditions = []
    if conditions:
        preconditions = [c["context"] for c in conditions]
    else:
        preconditions = [f"The {actor} has access to the system"]

    steps = [
        f"Navigate to the relevant page/feature",
        f"Perform action: {action}",
    ]
    if outcome:
        expected = f"The system should: {outcome}"
    else:
        expected = f"The action '{action}' completes successfully"

    case = {
        "id": _make_id("TC", f"happy-{action}"),
        "title": f"Verify {actor} can {action}",
        "type": "positive",
        "category": "happy_path",
        "preconditions": preconditions,
        "steps": steps,
        "expected_results": [expected],
        "source_trigger": "Primary action from user story",
    }

    return case


def _build_condition_case(actor, action, condition):
    kw = condition["keyword"]
    ctx = condition["context"]

    case = {
        "id": _make_id("TC", f"cond-{kw}-{action}"),
        "title": f"Verify behavior when condition '{kw}' is not met",
        "type": "negative",
        "category": "precondition_validation",
        "preconditions": [f"The condition '{ctx}' is NOT satisfied"],
        "steps": [
            f"Ensure the condition '{ctx}' is not met",
            f"Attempt to: {action}",
        ],
        "expected_results": [
            f"The system should prevent or handle the action gracefully",
            f"An appropriate error message or redirect is shown",
        ],
        "source_trigger": f"Condition keyword '{kw}' detected in story",
    }

    return case


def _build_negative_cases(actor, action, outcome, verbs, objects):
    cases = []

    # Missing/empty input case
    if objects:
        obj_names = [o["text"] for o in objects[:3]]
        for obj in obj_names:
            case = {
                "id": _make_id("TC", f"neg-empty-{obj}"),
                "title": f"Verify behavior with missing/empty {obj}",
                "type": "negative",
                "category": "input_validation",
                "preconditions": [f"The {actor} is on the relevant page"],
                "steps": [
                    f"Leave the '{obj}' field empty or provide invalid data",
                    f"Attempt to: {action}",
                ],
                "expected_results": [
                    f"The system shows a validation error for '{obj}'",
                    f"The action does not proceed until valid data is provided",
                ],
                "source_trigger": f"Object '{obj}' extracted from story via NLP",
            }
            cases.append(case)

    # Invalid credentials / unauthorized access
    action_lower = action.lower()
    if any(w in action_lower for w in ["login", "log in", "sign in", "authenticate", "access"]):
        case = {
            "id": _make_id("TC", f"neg-auth-{action}"),
            "title": f"Verify behavior with invalid credentials",
            "type": "negative",
            "category": "authentication",
            "preconditions": [f"The {actor} is on the login page"],
            "steps": [
                "Enter invalid username or password",
                "Submit the login form",
            ],
            "expected_results": [
                "The system displays an authentication error",
                "The user is not granted access",
            ],
            "source_trigger": "Authentication-related action detected in story",
        }
        cases.append(case)

    # Generic failure case
    case = {
        "id": _make_id("TC", f"neg-fail-{action}"),
        "title": f"Verify error handling when {action} fails",
        "type": "negative",
        "category": "error_handling",
        "preconditions": [f"The {actor} has access to the system", "System is in a state that may cause failure"],
        "steps": [
            f"Simulate a failure condition (e.g., network error, server error)",
            f"Attempt to: {action}",
        ],
        "expected_results": [
            "The system handles the error gracefully",
            "An informative error message is displayed",
            "No data corruption occurs",
        ],
        "source_trigger": "Standard error handling coverage for the primary action",
    }
    cases.append(case)

    return cases


def _build_boundary_cases(actor, action, objects):
    cases = []
    action_lower = action.lower()

    # If action involves data entry, add boundary cases
    input_signals = ["enter", "input", "type", "fill", "submit", "upload", "search", "write"]
    if any(s in action_lower for s in input_signals):
        case = {
            "id": _make_id("TC", f"bound-{action}"),
            "title": f"Verify boundary values for input in '{action}'",
            "type": "boundary",
            "category": "boundary_analysis",
            "preconditions": [f"The {actor} is on the relevant input form"],
            "steps": [
                "Enter minimum valid input (e.g., 1 character)",
                "Enter maximum valid input (e.g., max length)",
                "Enter special characters or edge-case values",
                f"Attempt to: {action}",
            ],
            "expected_results": [
                "Minimum valid input is accepted",
                "Maximum valid input is accepted",
                "Special characters are handled appropriately",
            ],
            "source_trigger": "Input-related action detected; boundary testing recommended",
        }
        cases.append(case)

    return cases
