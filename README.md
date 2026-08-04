# Automated Compliance Checker

Checks whether a company's internal policies conflict with a new external regulation.

A regulation goes in, the relevant policies are pulled out of a vector store, an LLM auditor
judges each one, and a structured JSON report comes out. Every step is traced to Langfuse.

## How it works

```
regulation text
      |
      v
[ retrieve ]  embed the regulation, similarity search over the policy collection
      |
      v
[ audit ]     one LLM call per retrieved policy -> {violates, reason, recommended_action}
      |
      v
   report     { target_regulation, conflict_detected, conflicting_policies, recommended_action, trace_id }
```

The two nodes are a LangGraph graph, so each one shows up as its own span in Langfuse and can
be tested on its own.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

Add two free keys to `.env`:

- `GROQ_API_KEY` from https://console.groq.com/keys
- `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` from https://cloud.langfuse.com

Embeddings run locally through ChromaDB, so retrieval needs no API key and no policy text
leaves the machine. Only the audit step calls out to Groq.

## Run

```bash
python main.py
python main.py --regulation REG_2026_SEC_VENDOR
python main.py --top-k 3
```

## Output

```json
{
  "target_regulation": "REG_2026_PR_COMPLIANCE",
  "conflict_detected": true,
  "conflicting_policies": [
    {
      "policy_id": "policy_001",
      "reason": "..."
    }
  ],
  "recommended_action": "...",
  "trace_id": "..."
}
```

`trace_id` links straight to the run in Langfuse, so any verdict can be traced back to the
retrieved policies and the exact prompt that produced it.

## Tests

```bash
pytest
```

The tests inject a fake auditor, so the suite runs without an API key and without spending
tokens. They cover retrieval ranking, the graph end to end, and report assembly.

## Files

| File | Purpose |
| --- | --- |
| `data.py` | The policies and regulations |
| `schemas.py` | Pydantic models for the output contract, plus report assembly |
| `store.py` | ChromaDB in-memory collection and similarity search |
| `graph.py` | The two node LangGraph graph and the auditor prompt |
| `observability.py` | Langfuse tracing, with a no-op fallback |
| `main.py` | CLI entry point |

## Design decisions

**LangGraph over a plain chain.** State is explicit, each node is separately traceable and
testable, and adding a third node later (human review, ticket creation) does not touch the
existing two.

**Pydantic structured output.** The auditor is bound to a schema, so the model returns a typed
object instead of prose we would have to parse. This is the main guard against hallucinated
output shapes.

**Retrieve before you audit.** Only the policies that are actually relevant reach the prompt.
With three policies that hardly matters, but the token cost stays flat as the library grows to
three thousand.

**One LLM call per policy.** Each judgement is isolated, so one policy cannot contaminate the
reasoning about another, a single failure does not lose the whole run, and the calls can be
parallelised later without changing the prompt.

**Dependency injection.** `build_graph(collection, auditor)` takes its collection and auditor as
arguments rather than building them internally, which is what lets the tests run offline.

**Local embeddings.** ChromaDB's built-in model keeps retrieval free and offline. Swapping to
pgvector or a hosted embedding model means changing `store.py` only.

## Failure handling

- Missing `GROQ_API_KEY` fails fast with a message that says what to do.
- Transient Groq errors are retried three times by the client.
- If Langfuse keys are missing or rejected, the audit still runs and returns `trace_id: null`.
  Observability is not allowed to take down the thing it observes.
- Retrieval asks for at most as many policies as the collection holds.
