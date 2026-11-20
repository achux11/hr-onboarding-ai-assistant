"""Routes each new-hire message to one of four paths and returns a cited response.

  escalate  -> sensitive topic, hand off to HR with a category
  checklist -> build the dated onboarding plan
  answer    -> grounded answer from the best policy section, with citation
  abstain   -> no policy matches well enough, so say so instead of guessing
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from . import checklist, guardrails
from .generate import ExtractiveGenerator
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


class OnboardingAgent:
    def __init__(self, retriever: Retriever | None = None, generator=None):
        self.retriever = retriever or Retriever()
        self.generator = generator or ExtractiveGenerator()

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
        text = self.generator(question, section.title, section.text)
        return Response("answer", text, [section.citation], score=score)
