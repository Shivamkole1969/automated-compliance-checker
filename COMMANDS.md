# Commands

Everything you might need to run or demo this project. Run all of these from the project
folder with the virtual environment active.

```bash
cd automated-compliance-checker
source .venv/bin/activate
```

---

## What each file does

The whole project is 338 lines of Python. Each file has one job, so you can explain any
part of it by pointing at a single short file.

### The story in one line

A regulation comes in. `store.py` finds the policies that are about the same subject.
`graph.py` asks the LLM to judge each one. `schemas.py` forces the answer into a fixed
shape. `observability.py` records how it happened. `main.py` prints it.

### File by file

| File | Think of it as | What is inside | The problem it solves |
| --- | --- | --- | --- |
| `data.py` | The rulebook | The 3 company policies and the 2 regulations, written as plain Python dictionaries | Someone non-technical can edit a policy and re-run. No database, no migration |
| `schemas.py` | The contract | Pydantic models: `PolicyVerdict`, `ConflictingPolicy`, `ComplianceReport`, plus `build_report()` | An LLM will happily reply in prose. This forces a fixed, typed shape so other systems can rely on it |
| `store.py` | The search | Builds the ChromaDB collection and one `search()` function | Answers "which policies do we even need to look at?" by meaning, not keywords |
| `graph.py` | The brain | The two LangGraph nodes (`retrieve`, `audit`) and the auditor prompt | The actual reasoning. Finds relevant policies, then judges each one against the regulation |
| `observability.py` | The flight recorder | Langfuse tracing, with a fallback that does nothing if keys are missing | Proof. Without it a verdict is just an opinion; with it every verdict can be reopened and checked |
| `main.py` | The front door | The CLI, `argparse`, and the code that ties the pieces together | How a human actually runs the thing |
| `tests/test_compliance.py` | The safety net | 4 tests using a fake auditor instead of a real LLM | Catches breakage instantly, with no API key and no cost |

### Supporting files

| File | What it is for |
| --- | --- |
| `requirements.txt` | Exact pinned versions, so the same install works on any machine |
| `.env.example` | The key names with no values, so people know what to set |
| `.env` | Your real keys. Gitignored, never committed |
| `.gitignore` | Keeps `.env`, `api_keys.txt` and `.venv` out of git |
| `README.md` | Architecture, setup, sample output, design decisions |
| `COMMANDS.md` | This file |

### Why it is split this way

Two reasons worth saying out loud if asked.

**Each piece can be swapped without touching the others.** Moving from ChromaDB to
pgvector means editing `store.py` only. Changing the model means editing `graph.py` only.

**It makes the tests possible.** `build_graph()` receives the vector store and the auditor
as arguments rather than creating them itself, so the tests hand it a fake auditor. That is
the reason the whole suite runs offline in under a second.

---

## 1. The four commands that matter

If you only remember four, remember these, in this order.

```bash
# 1. Tests first. Proves it works with no API key, no cost, in about a second.
pytest

# 2. The headline result. Matches the expected output in the brief.
python main.py --top-k 1

# 3. The optional second regulation. Same code, no changes.
python main.py --regulation REG_2026_SEC_VENDOR --top-k 1

# 4. The wider view, if they ask about policy_002.
python main.py --top-k 3
```

Then open the Langfuse trace using the `trace_id` printed at the end of the output.

---

## 2. First time setup

For a fresh machine, or if an interviewer wants to run it themselves.

```bash
git clone https://github.com/Shivamkole1969/automated-compliance-checker.git
cd automated-compliance-checker

python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env                 # then open .env and paste the keys
```

Keys needed in `.env`:

```
GROQ_API_KEY=            # console.groq.com/keys, free, no card
GROQ_MODEL=openai/gpt-oss-120b

LANGFUSE_PUBLIC_KEY=     # cloud.langfuse.com, free tier
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

Only `GROQ_API_KEY` is required. Without the Langfuse keys the audit still runs and
`trace_id` comes back `null`.

Check the install worked:

```bash
python -c "import langgraph, chromadb, langfuse; print('deps ok')"
python main.py --help
```

---

## 3. Running the checker

```bash
# Default: PR regulation, retrieves 2 policies
python main.py

# Pick the regulation
python main.py --regulation REG_2026_PR_COMPLIANCE
python main.py --regulation REG_2026_SEC_VENDOR

# Control how many policies get audited
python main.py --top-k 1        # narrowest, matches the brief exactly
python main.py --top-k 2        # default
python main.py --top-k 3        # audits every policy

# See the available options
python main.py --help
```

Save a run to a file, useful as a demo fallback if the network misbehaves:

```bash
python main.py --top-k 1 > sample_output.json
```

Run both regulations one after the other:

```bash
for r in REG_2026_PR_COMPLIANCE REG_2026_SEC_VENDOR; do
  python main.py --regulation "$r" --top-k 1
done
```

Just the trace ID from a run:

```bash
python main.py --top-k 1 | python -c "import json,sys; print(json.load(sys.stdin)['trace_id'])"
```

Just which policies were flagged:

```bash
python main.py --top-k 3 | python -c "import json,sys; [print(c['policy_id']) for c in json.load(sys.stdin)['conflicting_policies']]"
```

---

## 4. Tests

```bash
pytest                  # all four, quiet
pytest -v               # one line per test, use this in a demo
pytest -q               # minimal output
pytest -k retrieval     # just the retrieval tests
```

Expected:

```
tests/test_compliance.py::test_retrieval_ranks_the_communications_policy_first PASSED
tests/test_compliance.py::test_retrieval_never_asks_for_more_policies_than_it_has PASSED
tests/test_compliance.py::test_graph_flags_only_the_conflicting_policy PASSED
tests/test_compliance.py::test_report_stays_clean_when_nothing_conflicts PASSED

4 passed in 0.82s
```

These run without an API key because the tests inject a fake auditor.

---

## 5. Showing how it works

Use these when someone asks you to prove a claim rather than state it.

### Retrieval scores for both regulations

The single best thing to show. Lower distance means closer.

```bash
python -c "
from data import REGULATIONS
from store import build_store, search
c = build_store()
for rid, text in REGULATIONS.items():
    print(rid)
    for h in search(c, text, top_k=3):
        print(f\"   {h['id']}  {h['section']:<28} {h['distance']:.3f}\")
"
```

Output:

```
REG_2026_PR_COMPLIANCE
   policy_001  Corporate Communications     1.204
   policy_002  Data Security & Sharing      1.322
   policy_003  Vendor Management            1.523
REG_2026_SEC_VENDOR
   policy_003  Vendor Management            1.220
   policy_002  Data Security & Sharing      1.324
   policy_001  Corporate Communications     1.735
```

The point to make: the regulation says "external public communications", the policy says
"public social media platforms". No words overlap, and it still ranks first.

### The graph structure

```bash
python -c "
from store import build_store
from graph import build_graph
print(build_graph(build_store(), None, 2).get_graph().draw_mermaid())
"
```

Prints a mermaid diagram showing `__start__ -> retrieve -> audit -> __end__`.

### The auditor prompt

```bash
python -c "from graph import AUDITOR_PROMPT; print(AUDITOR_PROMPT)"
```

### The output schema

```bash
python -c "
import json
from schemas import ComplianceReport, PolicyVerdict
print(json.dumps(PolicyVerdict.model_json_schema(), indent=2))
print(json.dumps(ComplianceReport.model_json_schema(), indent=2))
"
```

### The policies and regulations

```bash
python -c "
from data import POLICIES, REGULATIONS
for p in POLICIES: print(p['id'], '-', p['section'])
for r in REGULATIONS: print(r)
"
```

### Line count, if asked how big it is

```bash
wc -l *.py tests/*.py
```

---

## 6. Troubleshooting

### No Groq key

```
Error: GROQ_API_KEY is not set. Copy .env.example to .env and add your key.
```

```bash
grep GROQ_API_KEY .env          # check it is there and not empty
```

### Check the Groq key actually works

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
print(ChatGroq(model=os.getenv('GROQ_MODEL'), temperature=0).invoke('say ok').content)
"
```

### Rate limited on the free tier

Wait a moment and retry, or switch to a smaller model:

```bash
GROQ_MODEL=llama-3.1-8b-instant python main.py --top-k 1
```

Note that some models do not support `json_schema`. If you see a 400 about response
format, go back to `openai/gpt-oss-120b`.

### trace_id comes back null

Means Langfuse is not configured. The audit still ran correctly.

```bash
grep LANGFUSE .env

python -c "
from dotenv import load_dotenv; load_dotenv()
from langfuse import get_client
print('auth ok:', get_client().auth_check())
"
```

### Which model am I actually using

```bash
python -c "
import os
from dotenv import load_dotenv; load_dotenv()
print('model:', os.getenv('GROQ_MODEL'))
"
```

### Start clean

```bash
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 7. Repository

```bash
git log --oneline
git status

# Prove no secret was ever committed
git log --all --pretty=format: --name-only | sort -u
git grep -I -n -E "gsk_|sk-lf-|pk-lf-" $(git rev-list --all)
```

The second command should return nothing at all. `.env` and `api_keys.txt` are gitignored.

```bash
# Confirm the repo is public
gh repo view Shivamkole1969/automated-compliance-checker --json visibility
```

---

## 8. Quick reference

| Command | What it does |
| --- | --- |
| `pytest -v` | Four tests, no API key needed |
| `python main.py --top-k 1` | The expected answer from the brief |
| `python main.py --regulation REG_2026_SEC_VENDOR --top-k 1` | The optional second regulation |
| `python main.py --top-k 3` | Audits every policy |
| `python main.py --help` | All options |
| `pip install -r requirements.txt` | Install pinned dependencies |
| `cp .env.example .env` | Create the config file |

### Numbers worth quoting

| Thing | Value |
| --- | --- |
| policy_001 distance to the PR regulation | 1.204, closest of the three |
| Retrieval step | 0.11s |
| Audit step | 1.46s, where all the time goes |
| Tokens per audit call | 441 in, 509 out |
| Tests | 4, passing in under a second |
| Code size | About 200 lines across 6 modules |
