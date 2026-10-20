"""
Anthropic AI Client and Robust Offline Fallback Mock Engine for TraceLens.
Handles requirement rewrites and automated test case generation with guaranteed zero-crash resilience.
"""

from __future__ import annotations
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dotenv import load_dotenv

from core.models import Requirement, TestCase
from core.linter import generate_template_rewrite

# Load environment configuration
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_anthropic_api_key() -> str:
    """Retrieve Anthropic API key from environment."""
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()


def get_anthropic_model() -> str:
    """Retrieve Anthropic model name, defaulting to claude-sonnet-4-6."""
    return os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6").strip()


def is_ai_available() -> bool:
    """
    Check if AI mode is operational with a valid key.
    Returns False for missing or dummy keys.
    """
    key = get_anthropic_api_key()
    if not key or key.lower() in ("your_api_key_here", "none", "null", "test"):
        return False
    return True


def get_mode_badge() -> Dict[str, str]:
    """
    Returns visual badge attributes for UI display.
    """
    if is_ai_available():
        return {
            "mode": "AI Mode",
            "model": get_anthropic_model(),
            "color": "green",
            "badge_html": (
                f'<span style="background-color: #064E3B; color: #34D399; padding: 4px 10px; '
                f'border-radius: 9999px; font-weight: 600; font-size: 0.82rem; border: 1px solid #059669;">'
                f'🤖 AI Mode ({get_anthropic_model()})</span>'
            ),
        }
    return {
        "mode": "Offline Mode",
        "model": "Mock Engine",
        "color": "gray",
        "badge_html": (
            '<span style="background-color: #1E293B; color: #94A3B8; padding: 4px 10px; '
            'border-radius: 9999px; font-weight: 600; font-size: 0.82rem; border: 1px solid #475569;">'
            '⚡ Offline Mode (Deterministic Mock Engine)</span>'
        ),
    }


def clean_json_response(raw_text: str) -> str:
    """
    Extract JSON substring from LLM response, stripping markdown wrappers.
    """
    text = raw_text.strip()
    # Match markdown json block ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    # Find outer bracket/brace
    start_bracket = text.find("[")
    end_bracket = text.rfind("]")
    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
        return text[start_bracket : end_bracket + 1]

    start_brace = text.find("{")
    end_brace = text.rfind("}")
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        return text[start_brace : end_brace + 1]

    return text


def rewrite_requirement_ai(req: Requirement) -> Tuple[str, bool]:
    """
    Rewrite a requirement using Claude to make it specific, measurable, and testable.
    Falls back gracefully to template rewrite if offline or upon any exception.
    Returns: (rewritten_text, is_mock_used)
    """
    if not is_ai_available():
        return generate_template_rewrite(req), True

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=get_anthropic_api_key())
        prompt = (
            f"You are a requirements engineering expert. Rewrite the following software requirement "
            f"to follow INCOSE and IEEE standards: strictly use 'shall', identify an unambiguous actor, "
            f"ensure it is quantifiable with specific numeric thresholds/metrics, make it strictly atomic, "
            f"and avoid all vague terms.\n\n"
            f"Original requirement ({req.id}): \"{req.text}\"\n\n"
            f"Respond ONLY with the single rewritten requirement text. Do not include markdown quotes, "
            f"bullet points, explanations, or introductory text."
        )

        response = client.messages.create(
            model=get_anthropic_model(),
            max_tokens=300,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )

        rewritten = response.content[0].text.strip().strip('"').strip("'")
        if len(rewritten) > 10:
            return rewritten, False
    except Exception:
        # Graceful fallback on API error or network failure
        pass

    return generate_template_rewrite(req), True


def generate_tests_mock(req: Requirement, start_id: int) -> List[TestCase]:
    """
    Deterministic template test case generation for offline mock mode.
    Generates 3 to 4 categorized tests (Positive, Negative, Boundary, Performance/Security).
    """
    tid1 = f"T{start_id}"
    tid2 = f"T{start_id + 1}"
    tid3 = f"T{start_id + 2}"
    tid4 = f"T{start_id + 3}"

    short_topic = "operation"
    if "menu" in req.text.lower() or "food" in req.text.lower():
        short_topic = "catalog filter"
    elif "pay" in req.text.lower() or "stripe" in req.text.lower() or "card" in req.text.lower():
        short_topic = "payment settlement"
    elif "gps" in req.text.lower() or "track" in req.text.lower() or "map" in req.text.lower():
        short_topic = "telemetry streaming"
    elif "auth" in req.text.lower() or "login" in req.text.lower() or "phone" in req.text.lower():
        short_topic = "user verification"
    elif "latency" in req.text.lower() or "load" in req.text.lower() or "rps" in req.text.lower():
        short_topic = "throughput capacity"
    elif "encrypt" in req.text.lower() or "security" in req.text.lower():
        short_topic = "cryptographic integrity"

    tests = [
        TestCase(
            id=tid1,
            title=f"Verify nominal {short_topic} happy path for {req.id}",
            steps=[
                f"1. Initialize client session and configure test parameters for {req.id}",
                f"2. Execute primary action: {req.text[:80]}...",
                "3. Intercept execution response and inspect return payload",
            ],
            expected=f"Execution succeeds with status 200 OK and expected output criteria met.",
            type="Unit",
            linked_req=req.id,
            status="Not Run",
            auto_generated=True,
        ),
        TestCase(
            id=tid2,
            title=f"Verify error handling on invalid parameters for {req.id}",
            steps=[
                f"1. Construct boundary violation payload (null/empty values or malformed tokens)",
                f"2. Dispatch request to {req.id} handler endpoint",
                "3. Verify exception catching mechanism",
            ],
            expected="System returns HTTP 400 Bad Request with descriptive validation error; does not crash.",
            type="Integration",
            linked_req=req.id,
            status="Not Run",
            auto_generated=True,
        ),
        TestCase(
            id=tid3,
            title=f"Boundary limit and timeout test for {req.id}",
            steps=[
                "1. Simulate high network latency / degraded upstream connection",
                "2. Trigger operation with maximum payload size limits",
                "3. Measure elapsed timeout boundary trigger",
            ],
            expected="Timeout triggered within designated threshold and resources released cleanly.",
            type="System",
            linked_req=req.id,
            status="Not Run",
            auto_generated=True,
        ),
        TestCase(
            id=tid4,
            title=f"Security and audit verification for {req.id}",
            steps=[
                "1. Attempt execution with unprivileged / unauthenticated credentials",
                "2. Verify security barrier intercepts operation",
                "3. Inspect security audit log entry",
            ],
            expected="Operation rejected with 401/403 and security violation event recorded in audit log.",
            type="Acceptance",
            linked_req=req.id,
            status="Not Run",
            auto_generated=True,
        ),
    ]

    return tests


def generate_tests_for_requirement(req: Requirement, start_id: int) -> Tuple[List[TestCase], bool]:
    """
    Generate 3-5 test cases for a requirement using Claude or Mock fallback.
    Validates JSON output, retries once on malformed JSON, and falls back cleanly.
    Returns: (list_of_test_cases, is_mock_used)
    """
    if not is_ai_available():
        return generate_tests_mock(req, start_id), True

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=get_anthropic_api_key())

        prompt = (
            f"You are a senior QA engineer. Generate 3 to 4 comprehensive test cases "
            f"(positive, negative, boundary, and performance/security) for the following requirement:\n"
            f"Requirement ID: {req.id}\n"
            f"Text: \"{req.text}\"\n"
            f"Type: {req.type}\n"
            f"Priority: {req.priority}\n\n"
            f"Respond STRICTLY with a valid JSON array of objects. Do not include markdown explanation. "
            f"Schema:\n"
            f"[\n"
            f"  {{\n"
            f"    \"title\": \"string test title\",\n"
            f"    \"type\": \"Unit\" | \"Integration\" | \"System\" | \"Acceptance\",\n"
            f"    \"steps\": [\"step 1\", \"step 2\", \"step 3\"],\n"
            f"    \"expected\": \"string expected outcome\"\n"
            f"  }}\n"
            f"]"
        )

        def attempt_call(prompt_text: str) -> Optional[List[Dict[str, Any]]]:
            resp = client.messages.create(
                model=get_anthropic_model(),
                max_tokens=1000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt_text}],
            )
            raw = resp.content[0].text
            cleaned = clean_json_response(raw)
            parsed = json.loads(cleaned)
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
            return None

        # Attempt 1
        parsed_data = None
        try:
            parsed_data = attempt_call(prompt)
        except Exception:
            # Retry once with strict correction prompt
            try:
                retry_prompt = prompt + "\n\nCRITICAL: Return ONLY a raw JSON array. No backticks, no comments."
                parsed_data = attempt_call(retry_prompt)
            except Exception:
                parsed_data = None

        if parsed_data:
            test_cases: List[TestCase] = []
            for idx, item in enumerate(parsed_data):
                tid = f"T{start_id + idx}"
                title = str(item.get("title", f"Test for {req.id}"))
                steps_val = item.get("steps", ["1. Execute test action"])
                if isinstance(steps_val, str):
                    steps_val = [s.strip() for s in steps_val.split("\n") if s.strip()]
                expected = str(item.get("expected", "Test assertion succeeds."))
                ttype = str(item.get("type", "System"))
                if ttype not in ("Unit", "Integration", "System", "Acceptance"):
                    ttype = "System"

                test_cases.append(
                    TestCase(
                        id=tid,
                        title=title,
                        steps=steps_val,
                        expected=expected,
                        type=ttype,
                        linked_req=req.id,
                        status="Not Run",
                        auto_generated=True,
                    )
                )
            if test_cases:
                return test_cases, False

    except Exception:
        pass

    # Graceful fallback to mock mode
    return generate_tests_mock(req, start_id), True


def analyze_conflict_ai(req1: Requirement, req2: Requirement) -> Tuple[Dict[str, Any], bool]:
    """
    Perform deep semantic conflict analysis between two requirements.
    Evaluates policy contradictions, behavioral inconsistencies, or technical conflicts.
    Returns: (result_dict, is_mock_used)
    """
    if is_ai_available():
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=get_anthropic_api_key())
            prompt = (
                f"Analyze if these two software requirements contradict or conflict with each other:\n"
                f"Requirement 1 ({req1.id}): \"{req1.text}\"\n"
                f"Requirement 2 ({req2.id}): \"{req2.text}\"\n\n"
                f"Return ONLY a JSON object formatted exactly as:\n"
                f"{{\n"
                f"  \"conflict_detected\": true,\n"
                f"  \"confidence\": 0.95,\n"
                f"  \"severity\": \"High\" | \"Medium\" | \"Low\" | \"None\",\n"
                f"  \"explanation\": \"Detailed explanation of why they conflict or why they are compatible\",\n"
                f"  \"resolution\": \"Proposed requirement modification or resolution strategy\"\n"
                f"}}"
            )
            resp = client.messages.create(
                model=get_anthropic_model(),
                max_tokens=600,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text
            cleaned = clean_json_response(raw)
            data = json.loads(cleaned)
            if isinstance(data, dict) and "conflict_detected" in data:
                return data, False
        except Exception:
            pass

    # Deterministic mock analysis
    t1 = req1.text.lower()
    t2 = req2.text.lower()

    # Rule checks
    anon_kws = [r"anonymous", r"guest", r"without login", r"without creating an account"]
    auth_kws = [r"mandatory", r"require.*auth", r"must.*login", r"authentication"]
    anon = any(re.search(k, t1) for k in anon_kws) and any(re.search(k, t2) for k in auth_kws)
    anon_rev = any(re.search(k, t2) for k in anon_kws) and any(re.search(k, t1) for k in auth_kws)
    retention = ("indefinitely" in t1 or "forever" in t1) and ("purge" in t2 or "delete after" in t2)
    retention_rev = ("indefinitely" in t2 or "forever" in t2) and ("purge" in t1 or "delete after" in t1)
    dark_light = ("dark mode only" in t1 and "light mode only" in t2) or ("light mode only" in t1 and "dark mode only" in t2)


    if anon or anon_rev:
        return {
            "conflict_detected": True,
            "confidence": 0.95,
            "severity": "High",
            "explanation": f"Authentication contradiction: {req1.id} permits guest checkout while {req2.id} mandates verified user authentication.",
            "resolution": "Standardize on allowing guest checkout with optional post-order account claiming, or mandate authentication only for saved payment methods.",
        }, True

    if retention or retention_rev:
        return {
            "conflict_detected": True,
            "confidence": 0.90,
            "severity": "High",
            "explanation": f"Data lifecycle contradiction between {req1.id} and {req2.id} regarding retention duration.",
            "resolution": "Enforce a GDPR-compliant 90-day retention schedule with anonymized cold storage.",
        }, True

    if dark_light:
        return {
            "conflict_detected": True,
            "confidence": 0.92,
            "severity": "Medium",
            "explanation": f"UI visual theme collision between {req1.id} and {req2.id}.",
            "resolution": "Implement a system theme toggle supporting both dark and light modes with OS preference detection.",
        }, True

    return {
        "conflict_detected": False,
        "confidence": 0.88,
        "severity": "None",
        "explanation": f"No direct semantic contradiction detected between {req1.id} and {req2.id}. Both requirements appear technically compatible.",
        "resolution": "Requirements are complementary; no harmonization required.",
    }, True


def suggest_requirement_ai(topic_or_draft: str, req_type: str = "Functional") -> Tuple[str, bool]:
    """
    Suggest an IEEE 830-compliant requirement statement given a topic or rough user note.
    Returns: (suggested_requirement_text, is_mock_used)
    """
    topic = topic_or_draft.strip()
    if is_ai_available():
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=get_anthropic_api_key())
            prompt = (
                f"You are a requirements engineering expert. Draft an IEEE 830-compliant {req_type} software requirement "
                f"for the following topic/prompt:\n\"{topic}\"\n\n"
                f"Guidelines:\n"
                f"- Use standard normative phrasing: 'The [actor/system] shall [action]...'\n"
                f"- Include an exact, verifiable threshold, SLA, or acceptance metric (e.g. seconds, percentages, throughput)\n"
                f"- Keep it atomic and single-sentence\n"
                f"- Return ONLY the requirement sentence with no introductory conversational text."
            )
            resp = client.messages.create(
                model=get_anthropic_model(),
                max_tokens=200,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            cleaned = resp.content[0].text.strip().strip('"').strip("'")
            if cleaned:
                return cleaned, False
        except Exception:
            pass

    # Deterministic mock templates based on keywords
    low = topic.lower()
    if any(k in low for k in ["pay", "checkout", "stripe", "credit", "card", "billing"]):
        return (
            "The payment service shall tokenize credit card data and process transactions via Stripe with an authorized response time of under 2.0 seconds and a 99.9% success rate.",
            True,
        )
    if any(k in low for k in ["login", "auth", "password", "otp", "register", "token"]):
        return (
            "The authentication service shall verify user credentials and deliver two-factor SMS OTPs within 5 seconds, enforcing account lockout after 5 consecutive failed attempts.",
            True,
        )
    if any(k in low for k in ["search", "menu", "filter", "restaurant", "catalog"]):
        return (
            "The search engine shall return restaurant menu search results filtered by cuisine and dietary criteria within 300 milliseconds for catalog datasets containing up to 50,000 items.",
            True,
        )
    if any(k in low for k in ["track", "gps", "location", "map", "driver", "courier"]):
        return (
            "The mobile app shall refresh real-time courier GPS coordinates on the order tracking map every 3 seconds with a spatial precision radius of within 15 meters.",
            True,
        )
    if any(k in low for k in ["notify", "alert", "push", "sms", "email"]):
        return (
            "The notification dispatcher shall broadcast order status change push notifications to customer devices within 2 seconds of event publication.",
            True,
        )
    if any(k in low for k in ["perf", "speed", "fast", "latency", "load", "scale"]):
        return (
            "The backend API gateway shall sustain 5,000 requests per second with a 95th percentile latency of less than 200 milliseconds under peak concurrent load.",
            True,
        )

    # General IEEE 830 compliant template
    clean_topic = topic if topic else "perform the requested business function"
    return (
        f"The system shall {clean_topic} within a verified processing duration of no more than 1.5 seconds under standard operational load.",
        True,
    )


def generate_rmmm_mitigation_ai(req: Requirement) -> Tuple[Dict[str, str], bool]:
    """
    Generate tailored RMMM mitigation, monitoring, and management strategies for a requirement.
    Returns: (strategy_dict, is_mock_used)
    """
    if is_ai_available():
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=get_anthropic_api_key())
            prompt = (
                f"You are a software risk management expert. Generate an RMMM (Risk Mitigation, Monitoring, and Management) "
                f"strategy for this software requirement:\n"
                f"Requirement ID: {req.id}\n"
                f"Type: {req.type}\n"
                f"Text: \"{req.text}\"\n"
                f"Impact: {req.impact}/5, Complexity: {req.complexity}/5\n\n"
                f"Return ONLY a JSON object with this exact structure:\n"
                f"{{\n"
                f"  \"title\": \"string concise risk title\",\n"
                f"  \"mitigation\": \"string actionable architectural or engineering mitigation\",\n"
                f"  \"monitoring\": \"string quantifiable metric/telemetry alert threshold to track risk trigger\"\n"
                f"}}"
            )
            resp = client.messages.create(
                model=get_anthropic_model(),
                max_tokens=400,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text
            cleaned = clean_json_response(raw)
            data = json.loads(cleaned)
            if isinstance(data, dict) and "title" in data and "mitigation" in data and "monitoring" in data:
                return data, False
        except Exception:
            pass

    # Deterministic fallback
    low = req.text.lower()
    if "payment" in low or "stripe" in low or "checkout" in low:
        return {
            "title": f"Payment processing timeout and reconciliation drift in {req.id}",
            "mitigation": "Deploy circuit breaker pattern with automated gateway failover and transactional idempotency keys.",
            "monitoring": "Prometheus metric alert for payment gateway 5xx rate > 0.5% and P99 latency > 2.5s.",
        }, True
    if "gps" in low or "location" in low or "map" in low:
        return {
            "title": f"Telemetry stream dropouts and driver position staleness in {req.id}",
            "mitigation": "Implement client dead-reckoning position estimation and exponential WebSocket reconnect backoff.",
            "monitoring": "Alert when WebSocket client ping latency exceeds 500ms or drop rate exceeds 1%.",
        }, True

    return {
        "title": f"Specification volatility and verification regression risk in {req.id}",
        "mitigation": f"Implement automated end-to-end regression suites and peer-reviewed interface contracts for {req.id}.",
        "monitoring": f"Track test pass rates and static lint violations during pull request CI builds.",
    }, True

