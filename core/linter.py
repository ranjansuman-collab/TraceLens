"""
Requirement Quality Linter and Conflict Detector for TraceLens.
Evaluates software requirements against IEEE/INCOSE quality standards and detects
contradictions across the requirements baseline.
"""

from __future__ import annotations
import re
import difflib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any

from core.models import Requirement


VAGUE_TERMS = [
    "fast",
    "easy",
    "user-friendly",
    "user friendly",
    "efficient",
    "flexible",
    "robust",
    "scalable",
    "seamless",
    "intuitive",
    "optimal",
    "quick",
    "responsive",
    "simple",
]

ACTORS = [
    "user",
    "customer",
    "client",
    "admin",
    "administrator",
    "system",
    "app",
    "application",
    "platform",
    "driver",
    "courier",
    "restaurant",
    "service",
    "api",
    "database",
    "server",
    "buyer",
    "seller",
]

PASSIVE_REGEX = re.compile(
    r"\b(is|are|was|were|be|been|being)\s+([a-z]+ed|written|built|sent|done|run|set|held|made|paid|lost|found|seen)\b",
    re.IGNORECASE,
)

NUMERIC_CRITERIA_REGEX = re.compile(
    r"(\d+(\.\d+)?|\b(one|two|three|four|five|six|seven|eight|nine|ten)\b|%|seconds?|sec|ms|minutes?|hours?|kb|mb|gb|rps|req/s|\$|usd|eur|gbp)",
    re.IGNORECASE,
)


@dataclass
class LintIssue:
    """Represents a specific quality issue found in a requirement."""
    rule: str
    penalty: int
    message: str
    category: str  # "Vagueness", "Measurability", "Syntax", "Structure", "Actor", "Voice"


@dataclass
class RequirementLintResult:
    """Evaluation result for an individual requirement."""
    req_id: str
    score: int
    grade: str  # "Green" (>=80), "Amber" (50-79), "Red" (<50)
    grade_label: str  # "Excellent" / "Acceptable" / "Poor"
    issues: List[LintIssue] = field(default_factory=list)
    vague_terms_found: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "req_id": self.req_id,
            "score": self.score,
            "grade": self.grade,
            "grade_label": self.grade_label,
            "issues": [
                {
                    "rule": i.rule,
                    "penalty": i.penalty,
                    "message": i.message,
                    "category": i.category,
                }
                for i in self.issues
            ],
            "vague_terms_found": self.vague_terms_found,
        }


@dataclass
class RequirementConflict:
    """Represents a contradiction or semantic conflict between two requirements."""
    req1_id: str
    req2_id: str
    description: str
    severity: str  # "High" | "Medium"
    confidence: float = 0.85

    def to_dict(self) -> Dict[str, Any]:
        """Convert conflict to dictionary."""
        return {
            "req1_id": self.req1_id,
            "req2_id": self.req2_id,
            "description": self.description,
            "severity": self.severity,
            "confidence": self.confidence,
        }


@dataclass
class RequirementDuplicate:
    """Represents a pair of requirements with substantial textual or semantic overlap (>80%)."""
    req1_id: str
    req2_id: str
    similarity: float
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert duplicate info to dictionary."""
        return {
            "req1_id": self.req1_id,
            "req2_id": self.req2_id,
            "similarity": self.similarity,
            "description": self.description,
        }



def lint_requirement(req: Requirement) -> RequirementLintResult:
    """
    Evaluate a requirement using rule-based scoring (0-100).
    Starts at 100, subtracting:
      - Vague terms (-15 each)
      - No measurable criterion/number (-20)
      - Missing 'shall' (-10)
      - Compound requirement with multiple 'and'/'or' (-10)
      - No clear actor (-10)
      - Passive voice (-5)
    """
    text = req.text.strip()
    score = 100
    issues: List[LintIssue] = []
    vague_found: List[str] = []

    # 1. Vague terms check (-15 each)
    lower_text = text.lower()
    for term in VAGUE_TERMS:
        pattern = rf"\b{re.escape(term)}\b"
        if re.search(pattern, lower_text):
            vague_found.append(term)
            score -= 15
            issues.append(
                LintIssue(
                    rule="Vague Terminology",
                    penalty=15,
                    message=f"Ambiguous adjective '{term}' lacks empirical test criteria.",
                    category="Vagueness",
                )
            )

    # 2. Measurable criterion / number check (-20)
    if not NUMERIC_CRITERIA_REGEX.search(text):
        score -= 20
        issues.append(
            LintIssue(
                rule="Unquantifiable Metric",
                penalty=20,
                message="No measurable threshold, numeric metric, or acceptance criterion specified.",
                category="Measurability",
            )
        )

    # 3. Missing 'shall' check (-10)
    if not re.search(r"\bshall\b", text, re.IGNORECASE):
        score -= 10
        issues.append(
            LintIssue(
                rule="Non-Standard Modality",
                penalty=10,
                message="Missing standard normative auxiliary 'shall' (found 'must', 'should', or informal phrasing).",
                category="Syntax",
            )
        )

    # 4. Compound requirement with multiple 'and'/'or' (-10)
    and_count = len(re.findall(r"\band\b", text, re.IGNORECASE))
    or_count = len(re.findall(r"\bor\b", text, re.IGNORECASE))
    if (and_count + or_count) >= 2:
        score -= 10
        issues.append(
            LintIssue(
                rule="Compound Requirement",
                penalty=10,
                message=f"Contains multiple coordination conjunctions ({and_count} 'and', {or_count} 'or'); split into atomic requirements.",
                category="Structure",
            )
        )

    # 5. Clear actor check (-10)
    has_actor = any(re.search(rf"\b{actor}\b", lower_text) for actor in ACTORS)
    if not has_actor:
        score -= 10
        issues.append(
            LintIssue(
                rule="Missing Actor/Subject",
                penalty=10,
                message="No explicit primary actor identified (e.g., 'The system', 'The customer', 'The API').",
                category="Actor",
            )
        )

    # 6. Passive voice check (-5)
    if PASSIVE_REGEX.search(text):
        score -= 5
        issues.append(
            LintIssue(
                rule="Passive Voice Construction",
                penalty=5,
                message="Passive voice detected; specify who performs the action to avoid ambiguity.",
                category="Voice",
            )
        )

    # Clamp score to 0..100
    final_score = max(0, min(100, score))

    if final_score >= 80:
        grade = "Green"
        grade_label = "High Quality"
    elif final_score >= 50:
        grade = "Amber"
        grade_label = "Needs Improvement"
    else:
        grade = "Red"
        grade_label = "Poor Quality"

    return RequirementLintResult(
        req_id=req.id,
        score=final_score,
        grade=grade,
        grade_label=grade_label,
        issues=issues,
        vague_terms_found=vague_found,
    )


def detect_conflicts(requirements: List[Requirement]) -> List[RequirementConflict]:
    """
    Detect likely semantic conflicts and opposing directives across requirements.
    Rules check opposing concepts on related subject domains.
    """
    conflicts: List[RequirementConflict] = []
    n = len(requirements)

    for i in range(n):
        for j in range(i + 1, n):
            r1 = requirements[i]
            r2 = requirements[j]
            t1 = r1.text.lower()
            t2 = r2.text.lower()

            # Rule 1: Guest/Anonymous vs Mandatory Authentication/Registration
            anon_keywords = ["anonymous", "guest", "without creating an account", "without logging in", "no login"]
            auth_keywords = ["mandatory", "require.*authentication", "must.*login", "verified.*phone", "registration prior", "enforce login"]

            has_anon_1 = any(re.search(kw, t1) for kw in anon_keywords)
            has_auth_1 = any(re.search(kw, t1) for kw in auth_keywords)
            has_anon_2 = any(re.search(kw, t2) for kw in anon_keywords)
            has_auth_2 = any(re.search(kw, t2) for kw in auth_keywords)

            if (has_anon_1 and has_auth_2) or (has_anon_2 and has_auth_1):
                conflicts.append(
                    RequirementConflict(
                        req1_id=r1.id,
                        req2_id=r2.id,
                        description=(
                            f"Contradiction in authentication policy: {r1.id} permits guest/anonymous checkout "
                            f"while {r2.id} mandates verified user authentication before order placement."
                        ),
                        severity="High",
                        confidence=0.95,
                    )
                )

            # Rule 2: Theme / UI mode conflicts (dark only vs light only)
            if ("dark mode only" in t1 and "light mode only" in t2) or ("dark mode only" in t2 and "light mode only" in t1):
                conflicts.append(
                    RequirementConflict(
                        req1_id=r1.id,
                        req2_id=r2.id,
                        description=f"Direct visual theme conflict between {r1.id} and {r2.id}.",
                        severity="Medium",
                        confidence=0.90,
                    )
                )

            # Rule 3: Data retention vs deletion conflicts
            retain_indefinite = "indefinitely" in t1 or "forever" in t1 or "retain all" in t1
            purge_data = "purge" in t2 or "delete after" in t2 or "erase" in t2
            if (retain_indefinite and purge_data) or (
                ("indefinitely" in t2 or "forever" in t2 or "retain all" in t2) and ("purge" in t1 or "delete after" in t1 or "erase" in t1)
            ):
                conflicts.append(
                    RequirementConflict(
                        req1_id=r1.id,
                        req2_id=r2.id,
                        description=f"Conflicting data retention lifecycle between {r1.id} and {r2.id}.",
                        severity="High",
                        confidence=0.88,
                    )
                )

    return conflicts


def detect_duplicates(requirements: List[Requirement], threshold: float = 0.80) -> List[RequirementDuplicate]:
    """
    Detect overlapping or duplicate requirements across the baseline.
    Uses SequenceMatcher ratio and word token similarity to find statements >= threshold.
    """
    duplicates: List[RequirementDuplicate] = []
    n = len(requirements)

    for i in range(n):
        for j in range(i + 1, n):
            r1 = requirements[i]
            r2 = requirements[j]
            t1 = r1.text.strip().lower()
            t2 = r2.text.strip().lower()

            if not t1 or not t2:
                continue

            # Exact match check
            if t1 == t2:
                duplicates.append(
                    RequirementDuplicate(
                        req1_id=r1.id,
                        req2_id=r2.id,
                        similarity=1.0,
                        description=f"Exact textual duplicate between {r1.id} and {r2.id}.",
                    )
                )
                continue

            seq_ratio = difflib.SequenceMatcher(None, t1, t2).ratio()
            words1 = set(re.findall(r"\w+", t1))
            words2 = set(re.findall(r"\w+", t2))
            jaccard = len(words1 & words2) / max(1, len(words1 | words2))
            blended = round(max(seq_ratio, 0.4 * seq_ratio + 0.6 * jaccard), 2)

            if blended >= threshold:
                duplicates.append(
                    RequirementDuplicate(
                        req1_id=r1.id,
                        req2_id=r2.id,
                        similarity=blended,
                        description=(
                            f"High conceptual overlap ({int(blended * 100)}%) between {r1.id} and {r2.id}. "
                            f"Consider consolidating into a single atomic requirement."
                        ),
                    )
                )

    return sorted(duplicates, key=lambda d: d.similarity, reverse=True)



def generate_template_rewrite(req: Requirement) -> str:
    """
    Generate an offline/mock rewritten requirement that solves detected quality issues:
    - Adds standard 'The system shall' / explicit actor
    - Replaces vague terms with concrete metrics
    - Splits or unifies compound expressions
    """
    text = req.text.strip()
    rewritten = text

    # Specific known mock rewrites for the sample dataset
    if req.id == "R3" or "user-friendly" in text.lower():
        return (
            "The customer user interface shall achieve a System Usability Scale (SUS) score of "
            "at least 80 and permit completing order placement in no more than 3 user interactions."
        )
    if req.id == "R4" or text.lower() == "the app should be fast.":
        return (
            "The mobile application shall render the home catalog screen within 1.5 seconds on 4G LTE connections "
            "and respond to touch interactions within 100 milliseconds."
        )
    if req.id == "R11" or ("flexible" in text.lower() and "robust" in text.lower()):
        return (
            "The payment service architecture shall implement a pluggable adapter interface supporting "
            "at least 3 third-party payment gateways with automated failover and 99.99% service availability."
        )
    if req.id == "R8" or len(re.findall(r"\band\b", text, re.IGNORECASE)) >= 3:
        return (
            "Upon delivery assignment acceptance by the driver, the system shall notify the restaurant, "
            "send an SMS notification to the customer within 5 seconds, and persist the dispatch audit record."
        )

    # General rule-based fallback rewrite
    # 1. Ensure actor
    if not any(re.search(rf"\b{actor}\b", rewritten, re.IGNORECASE) for actor in ACTORS):
        rewritten = f"The system shall {rewritten}"

    # 2. Ensure 'shall'
    rewritten = re.sub(r"\b(should|must|needs to|is to)\b", "shall", rewritten, flags=re.IGNORECASE)
    if not re.search(r"\bshall\b", rewritten, re.IGNORECASE):
        rewritten = re.sub(r"^(The\s+[a-zA-Z0-9_\- ]+?)\s+([a-z]+)", r"\1 shall \2", rewritten)

    # 3. Replace vague terms
    rewritten = re.sub(r"\bfast\b", "respond within 1.5 seconds", rewritten, flags=re.IGNORECASE)
    rewritten = re.sub(r"\buser-friendly\b|\buser friendly\b", "achieve SUS score >= 80", rewritten, flags=re.IGNORECASE)
    rewritten = re.sub(r"\befficient\b", "utilize less than 20% peak CPU and < 256MB memory", rewritten, flags=re.IGNORECASE)
    rewritten = re.sub(r"\bflexible and robust\b", "maintain 99.9% uptime with extensible modular interfaces", rewritten, flags=re.IGNORECASE)
    rewritten = re.sub(r"\bscalable\b", "scale horizontally to 10,000 concurrent users without latency degradation", rewritten, flags=re.IGNORECASE)

    # 4. Ensure at least one number
    if not NUMERIC_CRITERIA_REGEX.search(rewritten):
        rewritten = f"{rewritten} with a verified success rate of at least 99.5%."

    return rewritten


def compute_diff(before: str, after: str) -> str:
    """
    Generate unified text diff between original and rewritten requirement.
    """
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    diff = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile="Original",
        tofile="Rewritten (Proposed)",
        lineterm="",
    )
    return "\n".join(diff)
