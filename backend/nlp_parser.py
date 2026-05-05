"""
NLP Parser - Extracts actors, actions, conditions, and outcomes
from user stories using spaCy + rule-based patterns.
Designed for transparency: every extraction is traceable.
"""
import spacy
import re

nlp = spacy.load("en_core_web_sm")

# Common user story pattern: "As a <role>, I want <action> so that <benefit>"
STORY_PATTERN = re.compile(
    r"[Aa]s\s+(?:a|an)\s+(?P<actor>.+?),?\s+"
    r"I\s+(?:want|need|would like)\s+(?:to\s+)?(?P<action>.+?)\s+"
    r"(?:so\s+that|in\s+order\s+to)\s+(?P<outcome>.+)",
    re.IGNORECASE | re.DOTALL,
)

# Fallback: simpler patterns
SIMPLE_PATTERNS = [
    re.compile(r"[Aa]s\s+(?:a|an)\s+(?P<actor>.+?),?\s+I\s+(?:want|need|would like)\s+(?:to\s+)?(?P<action>.+)", re.IGNORECASE | re.DOTALL),
    re.compile(r"(?:User|I)\s+(?:should|can|want to|need to)\s+(?P<action>.+)", re.IGNORECASE | re.DOTALL),
]

# Keywords that signal conditions/preconditions
CONDITION_KEYWORDS = [
    "if", "when", "after", "before", "while", "unless", "given", "provided",
    "assuming", "once", "already", "logged in", "authenticated", "registered",
]

# Keywords for negative/edge test cases
NEGATIVE_KEYWORDS = [
    "invalid", "wrong", "empty", "missing", "expired", "blocked",
    "unauthorized", "without", "fail", "error", "incorrect",
]


def parse_user_story(story: str) -> dict:
    """
    Parse a user story into structured components.
    Returns actor, action, outcome, conditions, entities, and verbs
    with source mappings for explainability.
    """
    story = story.strip()
    doc = nlp(story)

    result = {
        "original_story": story,
        "actor": None,
        "action": None,
        "outcome": None,
        "conditions": [],
        "entities": [],
        "verbs": [],
        "objects": [],
        "source_mappings": [],  # For explainability: what was extracted and from where
    }

    # Step 1: Try structured pattern matching
    match = STORY_PATTERN.match(story)
    if match:
        result["actor"] = match.group("actor").strip().rstrip(".,")
        result["action"] = match.group("action").strip().rstrip(".,")
        result["outcome"] = match.group("outcome").strip().rstrip(".,")
        result["source_mappings"].append({
            "type": "pattern_match",
            "description": "Matched standard user story format (As a..., I want..., so that...)",
            "extracted": {"actor": result["actor"], "action": result["action"], "outcome": result["outcome"]},
        })
    else:
        # Try simpler patterns
        for pat in SIMPLE_PATTERNS:
            m = pat.match(story)
            if m:
                groups = m.groupdict()
                result["actor"] = groups.get("actor", "user")
                if result["actor"]:
                    result["actor"] = result["actor"].strip().rstrip(".,")
                result["action"] = groups.get("action", "").strip().rstrip(".,")
                result["source_mappings"].append({
                    "type": "partial_pattern_match",
                    "description": "Matched partial user story format",
                    "extracted": {k: v for k, v in groups.items() if v},
                })
                break

    # If no pattern matched, use NLP fallback
    if not result["action"]:
        result["actor"] = "user"
        result["action"] = story
        result["source_mappings"].append({
            "type": "nlp_fallback",
            "description": "No standard pattern found; treating entire input as action description",
            "extracted": {"action": story},
        })

    # Step 2: Extract verbs and objects via dependency parsing
    for token in doc:
        if token.pos_ == "VERB" and token.text.lower() not in ("want", "need", "like", "would"):
            result["verbs"].append({
                "text": token.lemma_,
                "position": token.idx,
                "context": token.sent.text.strip(),
            })
        if token.dep_ in ("dobj", "pobj", "attr") and token.pos_ in ("NOUN", "PROPN"):
            result["objects"].append({
                "text": token.text,
                "position": token.idx,
                "head_verb": token.head.lemma_ if token.head.pos_ == "VERB" else None,
            })

    # Step 3: Extract named entities
    for ent in doc.ents:
        result["entities"].append({
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char,
        })

    # Step 4: Detect conditions
    story_lower = story.lower()
    for kw in CONDITION_KEYWORDS:
        if kw in story_lower:
            idx = story_lower.index(kw)
            # Extract the clause around the keyword
            surrounding = story[max(0, idx - 10):min(len(story), idx + 60)].strip()
            result["conditions"].append({
                "keyword": kw,
                "context": surrounding,
                "position": idx,
            })
            result["source_mappings"].append({
                "type": "condition_detected",
                "description": f"Condition keyword '{kw}' found",
                "extracted": {"condition": surrounding},
            })

    # Step 5: Detect potential negative scenarios
    result["has_negative_indicators"] = any(kw in story_lower for kw in NEGATIVE_KEYWORDS)

    return result
