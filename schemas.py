from typing import List, Optional

from pydantic import BaseModel, Field


class PolicyVerdict(BaseModel):
    violates: bool = Field(description="True if this policy conflicts with the regulation")
    reason: str = Field(description="Two or three sentences citing the wording that decided it")
    recommended_action: str = Field(
        default="", description="How to fix the policy. Leave empty when there is no conflict"
    )


class ConflictingPolicy(BaseModel):
    policy_id: str
    reason: str


class ComplianceReport(BaseModel):
    target_regulation: str
    conflict_detected: bool
    conflicting_policies: List[ConflictingPolicy]
    recommended_action: str
    trace_id: Optional[str] = None


def build_report(regulation_id, verdicts, trace_id=None):
    conflicts = [v for v in verdicts if v["violates"]]
    actions = [v["recommended_action"].strip() for v in conflicts if v["recommended_action"].strip()]
    return ComplianceReport(
        target_regulation=regulation_id,
        conflict_detected=len(conflicts) > 0,
        conflicting_policies=[
            ConflictingPolicy(policy_id=v["policy_id"], reason=v["reason"]) for v in conflicts
        ],
        recommended_action=" ".join(actions) or "No changes required.",
        trace_id=trace_id,
    )
