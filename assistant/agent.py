"""Routes each new-hire message to one of four paths and returns a cited response.

  escalate  -> sensitive topic, hand off to HR with a category
  checklist -> build the dated onboarding plan
  answer    -> grounded answer from the best policy section, with citation
  abstain   -> no policy matches well enough, so say so instead of guessing
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date

from . import checklist, guardrails
from .retriever import Retriever

MIN_SCORE = 0.12  # chosen on the dev split only, see eval/run_eval.py
CHECKLIST_RE = re.compile(r"checklist|onboarding plan|what do i need to do|to-?do|first (week|month) plan", re.I)


@dataclass
class Response:
    route: str
    text: str
    citations: list[str] = field(default_factory=list)
    category: str | None = None
    score: float = 0.0


def _best_sentences(question: str, text: str, n: int = 2) -> str:
    q = set(re.findall(r"[a-z0-9]+", question.lower()))
    sentences = re.split(r"(?<=[.!?])\s+", text)
    ranked = sorted(sentences, key=lambda s: -len(q & set(re.findall(r"[a-z0-9]+", s.lower()))))
    keep = set(ranked[:n])
    return " ".join(s for s in sentences if s in keep)  # keep original order


def _llm_answer(question: str, context: str) -> str | None:
    """Optional: phrase the answer with Claude, using only the retrieved policy text."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    msg = anthropic.Anthropic().messages.create(
        model=os.getenv("HR_ASSISTANT_MODEL", "claude-haiku-5-5"),
        max_tokens=300,
        system="Answer the new hire's question using only the policy text provided. "
        "If the text does not answer it, say you don't know and suggest contacting HR.",
        messages=[{"role": "user", "content": f"Policy text:\n{context}\n\nQuestion: {question}"}],
    )
    return msg.content[0].text


class OnboardingAgent:
    def __init__(self, retriever: Retriever | None = None, use_llm: bool = False):
        self.retriever = retriever or Retriever()
        self.use_llm = use_llm

    def ask(self, question: str, start: date | None = None, remote: bool = False) -> Response:
        category = guardrails.check(question)
        if category:
            return Response(
                "escalate",
                "This is best handled by a person. I've flagged it for HR, and you can also reach HR "
                "or the anonymous ethics hotline directly.",
                ["conduct.md > Reporting a concern"],
                category,
            )
        if CHECKLIST_RE.search(question):
            plan = checklist.build(start or date.today(), remote)
            lines = [f"{r['due']:%b %d}  [{r['scope_item']}]  {r['task']}" for r in plan]
            return Response("checklist", "\n".join(lines), sorted({r["source"] for r in plan}))

        hits = self.retriever.search(question, k=3)
        section, score = hits[0]
        if score < MIN_SCORE or not self.retriever.specific_terms(question, self.retriever.index_of(section)):
            return Response("abstain", "I couldn't find this in the onboarding policies. Please ask HR.", score=score)
        text = (self.use_llm and _llm_answer(question, section.text)) or _best_sentences(question, section.text)
        return Response("answer", text, [section.citation], score=score)
