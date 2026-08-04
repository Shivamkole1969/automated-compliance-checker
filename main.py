import argparse
import json
import sys

from dotenv import load_dotenv

from data import REGULATIONS
from graph import build_graph, make_auditor
from observability import start_trace
from schemas import build_report
from store import build_store


def run(regulation_id, top_k=2):
    if regulation_id not in REGULATIONS:
        raise ValueError(f"Unknown regulation '{regulation_id}'. Available: {', '.join(REGULATIONS)}")

    state = {"regulation_id": regulation_id, "regulation_text": REGULATIONS[regulation_id]}
    app = build_graph(build_store(), make_auditor(), top_k)

    with start_trace("compliance-check", state) as trace:
        result = app.invoke(state, config={"callbacks": trace.callbacks})
        report = build_report(regulation_id, result["verdicts"], trace.trace_id)
        trace.finish(report.model_dump())

    return report


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Check company policies against a new regulation.")
    parser.add_argument("--regulation", default="REG_2026_PR_COMPLIANCE", choices=list(REGULATIONS))
    parser.add_argument("--top-k", type=int, default=2, help="How many policies to retrieve")
    args = parser.parse_args()

    try:
        report = run(args.regulation, args.top_k)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(json.dumps(report.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
