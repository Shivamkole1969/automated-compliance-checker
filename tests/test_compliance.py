from data import REGULATIONS
from graph import build_graph
from schemas import PolicyVerdict, build_report
from store import build_store, search

PR_REGULATION = "REG_2026_PR_COMPLIANCE"


class FakeAuditor:
    def invoke(self, prompt):
        if "policy_001" in prompt:
            return PolicyVerdict(
                violates=True,
                reason="The policy lets employees post project updates without pre-approval.",
                recommended_action="Require PR Compliance Committee sign-off before posting.",
            )
        return PolicyVerdict(violates=False, reason="Covers a different subject.")


def test_retrieval_ranks_the_communications_policy_first():
    hits = search(build_store(), REGULATIONS[PR_REGULATION], top_k=2)
    assert hits[0]["id"] == "policy_001"


def test_retrieval_never_asks_for_more_policies_than_it_has():
    assert len(search(build_store(), REGULATIONS[PR_REGULATION], top_k=99)) == 3


def test_graph_flags_only_the_conflicting_policy():
    app = build_graph(build_store(), FakeAuditor(), top_k=2)
    state = {"regulation_id": PR_REGULATION, "regulation_text": REGULATIONS[PR_REGULATION]}

    result = app.invoke(state)
    report = build_report(PR_REGULATION, result["verdicts"], trace_id="trace-123")

    assert report.conflict_detected is True
    assert [c.policy_id for c in report.conflicting_policies] == ["policy_001"]
    assert report.trace_id == "trace-123"


def test_report_stays_clean_when_nothing_conflicts():
    verdicts = [{"policy_id": "policy_002", "violates": False, "reason": "n/a", "recommended_action": ""}]
    report = build_report(PR_REGULATION, verdicts)

    assert report.conflict_detected is False
    assert report.conflicting_policies == []
    assert report.recommended_action == "No changes required."
