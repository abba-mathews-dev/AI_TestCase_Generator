"""
Explainability Engine - Provides transparent reasoning for
every generated test case. Maps output → input with clear logic.
"""


def build_explanations(analysis: dict, test_cases: list) -> list:
    """
    For each test case, produce a human-readable explanation:
    - Why this test case was generated
    - Which part of the user story triggered it
    - The logical reasoning chain
    """
    explanations = []
    story = analysis.get("original_story", "")

    for tc in test_cases:
        explanation = {
            "test_case_id": tc["id"],
            "test_case_title": tc["title"],
            "reasoning": [],
            "story_mapping": [],
            "confidence": "high",
        }

        category = tc.get("category", "")
        source_trigger = tc.get("source_trigger", "")

        # Build reasoning chain based on category
        if category == "happy_path":
            explanation["reasoning"] = [
                f"The user story describes a primary action: '{analysis.get('action', '')}'",
                f"Every user story requires a 'happy path' test to verify the intended behavior works correctly.",
                f"This test validates that the {analysis.get('actor', 'user')} can successfully perform the described action.",
            ]
            if analysis.get("outcome"):
                explanation["reasoning"].append(
                    f"The expected outcome '{analysis['outcome']}' is verified as the success criterion."
                )
            explanation["story_mapping"] = _build_story_highlights(analysis, ["action", "outcome"])

        elif category == "precondition_validation":
            explanation["reasoning"] = [
                f"A condition was detected in the story: '{source_trigger}'",
                "Conditions imply that certain prerequisites must be met.",
                "Testing what happens when prerequisites are NOT met ensures robust error handling.",
                "This is a standard QA practice: validate both the presence and absence of preconditions.",
            ]
            explanation["story_mapping"] = _build_story_highlights(analysis, ["conditions"])

        elif category == "input_validation":
            explanation["reasoning"] = [
                f"The NLP parser identified input-related objects in the story.",
                "Any user-facing input must be validated for empty, missing, or malformed data.",
                "This test ensures the system doesn't crash or behave unexpectedly with bad input.",
                "Input validation is a top priority in real-world QA.",
            ]
            explanation["story_mapping"] = _build_story_highlights(analysis, ["objects"])

        elif category == "authentication":
            explanation["reasoning"] = [
                "The story contains authentication-related actions (login, sign in, access).",
                "Authentication is a critical security boundary.",
                "Testing with invalid credentials is mandatory for any auth-related feature.",
                "This covers the most common attack vector: unauthorized access attempts.",
            ]
            explanation["story_mapping"] = _build_story_highlights(analysis, ["action"])

        elif category == "error_handling":
            explanation["reasoning"] = [
                "Every feature should gracefully handle unexpected failures.",
                "This test covers system-level errors (network, server, timeout).",
                "Good QA practice requires testing failure modes, not just success paths.",
                "Users should always see meaningful error messages, never raw system errors.",
            ]
            explanation["story_mapping"] = _build_story_highlights(analysis, ["action"])
            explanation["confidence"] = "medium"

        elif category == "boundary_analysis":
            explanation["reasoning"] = [
                "The story involves data entry or user input.",
                "Boundary value analysis tests the edges of valid input ranges.",
                "Common defects occur at boundaries: min/max length, special characters, etc.",
                "This is a standard testing technique recommended by ISTQB.",
            ]
            explanation["story_mapping"] = _build_story_highlights(analysis, ["action", "objects"])

        else:
            explanation["reasoning"] = [
                f"Generated based on: {source_trigger}",
                "This test case covers an additional scenario identified during analysis.",
            ]
            explanation["confidence"] = "medium"

        explanation["source_trigger"] = source_trigger
        explanations.append(explanation)

    return explanations


def _build_story_highlights(analysis: dict, fields: list) -> list:
    """Create mappings showing which story parts triggered the test."""
    mappings = []
    story = analysis.get("original_story", "")

    for field in fields:
        if field == "action" and analysis.get("action"):
            action = analysis["action"]
            start = story.lower().find(action.lower()[:20])
            mappings.append({
                "element": "action",
                "text": action,
                "position_hint": start if start >= 0 else None,
                "description": f"Primary action: '{action}'",
            })

        elif field == "outcome" and analysis.get("outcome"):
            outcome = analysis["outcome"]
            start = story.lower().find(outcome.lower()[:20])
            mappings.append({
                "element": "outcome",
                "text": outcome,
                "position_hint": start if start >= 0 else None,
                "description": f"Expected outcome: '{outcome}'",
            })

        elif field == "conditions" and analysis.get("conditions"):
            for cond in analysis["conditions"]:
                mappings.append({
                    "element": "condition",
                    "text": cond.get("context", ""),
                    "keyword": cond.get("keyword", ""),
                    "description": f"Condition detected via keyword '{cond.get('keyword', '')}'",
                })

        elif field == "objects" and analysis.get("objects"):
            for obj in analysis["objects"][:3]:
                mappings.append({
                    "element": "object",
                    "text": obj.get("text", ""),
                    "description": f"Input object '{obj['text']}' (linked to verb: {obj.get('head_verb', 'N/A')})",
                })

    return mappings
