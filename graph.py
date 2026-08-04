import os
from typing import TypedDict

from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph

from schemas import PolicyVerdict
from store import search

AUDITOR_PROMPT = """You are a compliance auditor. Compare one internal company policy against one new external regulation.

Regulation {regulation_id}:
{regulation_text}

Company policy {policy_id}, section "{policy_section}":
{policy_text}

Decide whether the policy conflicts with the regulation.

Mark violates true only when both of these hold:
1. The policy permits or enables the specific activity the regulation governs.
2. It allows that activity without the control the regulation makes mandatory.

Mark violates false when the policy is silent on the regulated activity, covers a different
subject, or already requires an equivalent or stricter control. Failing to mention the
regulation's topic is not by itself a conflict.

Rules:
- Use only the two texts above. Do not rely on outside knowledge or assume details that are not written.
- Quote the specific wording that decided your answer.
- Leave recommended_action empty when there is no conflict."""


class State(TypedDict):
    regulation_id: str
    regulation_text: str
    policies: list
    verdicts: list


def make_auditor():
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")

    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        temperature=0,
        max_retries=3,
    )
    # json_schema makes Groq enforce the schema server side. Tool calling let a model
    # return violates as the string "true", which failed validation.
    return llm.with_structured_output(PolicyVerdict, method="json_schema")


def build_graph(collection, auditor, top_k=2):
    def retrieve(state: State):
        return {"policies": search(collection, state["regulation_text"], top_k)}

    def audit(state: State):
        verdicts = []
        for policy in state["policies"]:
            prompt = AUDITOR_PROMPT.format(
                regulation_id=state["regulation_id"],
                regulation_text=state["regulation_text"],
                policy_id=policy["id"],
                policy_section=policy["section"],
                policy_text=policy["text"],
            )
            verdict = auditor.invoke(prompt)
            verdicts.append({"policy_id": policy["id"], **verdict.model_dump()})
        return {"verdicts": verdicts}

    graph = StateGraph(State)
    graph.add_node("retrieve", retrieve)
    graph.add_node("audit", audit)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "audit")
    graph.add_edge("audit", END)
    return graph.compile()
