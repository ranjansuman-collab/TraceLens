"""
Risk calculation, test execution prioritization, and RMMM table generation for TraceLens.
Formula: Risk = Impact * Complexity * (1 + Change_Count).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from core.models import Project, Requirement, TestCase


@dataclass
class RMMMItem:
    """Risk Mitigation, Monitoring, and Management entry."""
    risk_id: str
    req_id: str
    risk_title: str
    probability: str  # "High" | "Medium" | "Low"
    impact: int       # 1-5
    risk_score: float
    mitigation: str
    monitoring: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "risk_id": self.risk_id,
            "req_id": self.req_id,
            "risk_title": self.risk_title,
            "probability": self.probability,
            "impact": self.impact,
            "risk_score": self.risk_score,
            "mitigation": self.mitigation,
            "monitoring": self.monitoring,
        }


def calculate_requirement_risk(req: Requirement) -> float:
    """
    Calculate risk metric: Impact * Complexity * (1 + Change_Count).
    """
    return float(req.impact * req.complexity * (1 + req.change_count))


def get_prioritized_test_cases(project: Project) -> List[Dict[str, Any]]:
    """
    Sort test execution order descending by the risk score of the linked requirement.
    Tests linking to volatile or high-impact/complex requirements execute first.
    """
    results: List[Dict[str, Any]] = []

    req_risk_map = {r.id: calculate_requirement_risk(r) for r in project.requirements}

    for tc in project.test_cases:
        risk_score = req_risk_map.get(tc.linked_req, 0.0)
        req = project.get_requirement(tc.linked_req)
        results.append({
            "test_id": tc.id,
            "title": tc.title,
            "type": tc.type,
            "status": tc.status,
            "linked_req": tc.linked_req,
            "req_priority": req.priority if req else "N/A",
            "req_impact": req.impact if req else 1,
            "req_complexity": req.complexity if req else 1,
            "risk_score": risk_score,
        })

    # Sort descending by risk score, then test id
    results.sort(key=lambda x: (x["risk_score"], x["test_id"]), reverse=True)
    return results


def get_uncovered_requirements_by_risk(project: Project) -> List[Dict[str, Any]]:
    """
    Return all requirements lacking test cases, ranked descending by risk score.
    Used in Gap Heatmap and Test Generator.
    """
    tested_req_ids = {t.linked_req for t in project.test_cases if t.linked_req}
    uncovered = [r for r in project.requirements if r.id not in tested_req_ids]

    results = []
    for r in uncovered:
        results.append({
            "req_id": r.id,
            "text": r.text,
            "priority": r.priority,
            "impact": r.impact,
            "complexity": r.complexity,
            "change_count": r.change_count,
            "risk_score": calculate_requirement_risk(r),
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results


def generate_rmmm_table(project: Project, custom_mitigations: Optional[Dict[str, Dict[str, str]]] = None) -> List[RMMMItem]:
    """
    Generate an RMMM (Risk Mitigation, Monitoring, and Management) table
    auto-filled for the top 5 highest risk requirements.
    """
    sorted_reqs = sorted(project.requirements, key=calculate_requirement_risk, reverse=True)
    top_5 = sorted_reqs[:5]

    rmmm_items: List[RMMMItem] = []
    mitigation_db = custom_mitigations or {}

    # Domain-aware default templates for food delivery platform
    default_strategies = {
        "R2": {
            "title": "Payment gateway timeout and charge failure under burst load",
            "mitigation": "Deploy circuit breaker pattern, retry queues, and automated fallback to secondary payment gateway.",
            "monitoring": "Track Stripe 5xx error rate and P99 payment latency alert threshold at 2.5s.",
        },
        "R10": {
            "title": "Backend API degradation and latency spike under 5000 RPS peak volume",
            "mitigation": "Implement Redis distributed caching for restaurant menus and cluster auto-scaling with horizontal pod autoscaler.",
            "monitoring": "Real-time Prometheus APM monitoring with Grafana alerts triggered if P95 latency exceeds 180ms.",
        },
        "R12": {
            "title": "Cryptographic vulnerability or plaintext credential leakage in transit/rest",
            "mitigation": "Automate AWS KMS envelope encryption rotation, strict TLS 1.3 cipher suite checks, and SonarQube SAST scans.",
            "monitoring": "Daily SIEM log auditing, automated penetration testing in CI/CD, and SSL Labs certificate health checker.",
        },
        "R5": {
            "title": "WebSocket location stream dropouts and driver GPS positioning errors",
            "mitigation": "Implement client dead-reckoning interpolation, exponential reconnect backoff, and geo-fenced coordinate validation.",
            "monitoring": "Monitor WebSocket disconnect rate and ping latency threshold at 500ms.",
        },
        "R7": {
            "title": "SMS OTP gateway outages blocking customer account registration and checkouts",
            "mitigation": "Contract dual SMS aggregators (Twilio + Infobip) with auto-switching and rate-limit abuse prevention.",
            "monitoring": "Track SMS delivery receipt rates; alert if OTP delivery time exceeds 15 seconds.",
        },
        "R8": {
            "title": "Compound dispatch workflow race conditions and distributed state inconsistency",
            "mitigation": "Adopt Saga orchestrator pattern with transactional outbox and idempotency keys across driver/kitchen/customer events.",
            "monitoring": "Distributed OpenTelemetry tracing on order dispatch events; alert on state mismatches > 0.05%.",
        },
    }

    for idx, r in enumerate(top_5, start=1):
        score = calculate_requirement_risk(r)
        prob = "High" if r.complexity >= 4 or r.change_count >= 1 else ("Medium" if r.complexity == 3 else "Low")

        custom_entry = mitigation_db.get(r.id)
        default_entry = default_strategies.get(r.id, {
            "title": f"Requirements volatility and architectural risk in {r.id}",
            "mitigation": f"Establish automated unit/contract tests for {r.id} and conduct cross-functional architecture review.",
            "monitoring": f"Track test coverage, defect leakage, and requirement linter score for {r.id}.",
        })

        title = (custom_entry.get("title") if custom_entry else None) or default_entry["title"]
        mitigation = (custom_entry.get("mitigation") if custom_entry else None) or default_entry["mitigation"]
        monitoring = (custom_entry.get("monitoring") if custom_entry else None) or default_entry["monitoring"]

        rmmm_items.append(
            RMMMItem(
                risk_id=f"RSK-0{idx}",
                req_id=r.id,
                risk_title=title,
                probability=prob,
                impact=r.impact,
                risk_score=score,
                mitigation=mitigation,
                monitoring=monitoring,
            )
        )

    return rmmm_items
