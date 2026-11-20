"""Evaluate generated answers, not just retrieval.

For every question whose correct route is `answer`, the full pipeline runs (guardrails,
retrieval, generation) and the answer is checked against a hand-written answer key.

Metrics
  answer_correct      every key fact from the answer key appears in the answer
  correct_given_hit   same, counting only questions where retrieval found the right section
  unsupported_number  the answer contains a number that is in neither the retrieved policy
                      text nor the question: a simple, strict hallucination check
  said_dont_know      the model declined even though the policy covers the question

    python -m eval.run_generation_eval --backend extractive
    python -m eval.run_generation_eval --backend hf --model Qwen/Qwen2.5-1.5B-Instruct
    python -m eval.run_generation_eval --backend claude
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from assistant.agent import OnboardingAgent
from assistant.generate import IDK, make
from eval.run_eval import load

OUT = Path(__file__).parent / "generation"
NUM = re.compile(r"\d+(?:\.\d+)?")


def has_facts(answer: str, key: list[list[str]]) -> bool:
    a = answer.lower()
    return all(any(alt.lower() in a for alt in fact) for fact in key)


def unsupported_numbers(answer: str, source: str, question: str) -> list[str]:
    allowed = set(NUM.findall(source)) | set(NUM.findall(question))
    return [n for n in NUM.findall(answer) if n not in allowed]


def evaluate(split: str, bot: OnboardingAgent) -> tuple[dict, list[dict]]:
    rows = [r for r in load(None if split == "all" else split) if r["route"] == "answer"]
    by_citation = {s.citation: s for s in bot.retriever.sections}
    out, correct, hit, correct_hit, unsupported, idk, answered = [], 0, 0, 0, 0, 0, 0
    for r in rows:
        resp = bot.ask(r["question"])
        is_hit = resp.route == "answer" and resp.citations == [r["expected"]]
        source = by_citation[resp.citations[0]].text if resp.route == "answer" else ""
        bad = unsupported_numbers(resp.text, source, r["question"]) if resp.route == "answer" else []
        ok = resp.route == "answer" and has_facts(resp.text, r["answer_key"])
        answered += resp.route == "answer"
        correct += ok
        hit += is_hit
        correct_hit += ok and is_hit
        unsupported += bool(bad)
        idk += resp.route == "answer" and IDK in resp.text.lower()
        out.append({"id": r["id"], "question": r["question"], "route": resp.route,
                    "citation": resp.citations[:1], "answer": resp.text,
                    "correct": ok, "unsupported_numbers": bad})
    pct = lambda a, b: round(100 * a / b, 1) if b else None
    summary = {
        "split": split, "questions": len(rows),
        "answer_correct_%": pct(correct, len(rows)),
        "correct_given_hit_%": pct(correct_hit, hit),
        "unsupported_number_%": pct(unsupported, answered),
        "said_dont_know_%": pct(idk, answered),
    }
    return summary, out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--backend", default="extractive", choices=["extractive", "claude", "hf"])
    p.add_argument("--model")
    p.add_argument("--splits", default="dev,holdout")
    args = p.parse_args()
    gen = make(args.backend, args.model)
    bot = OnboardingAgent(generator=gen)
    OUT.mkdir(exist_ok=True)
    report = {"generator": gen.name}
    for split in args.splits.split(","):
        summary, rows = evaluate(split, bot)
        report[split] = summary
        tag = gen.name.replace("/", "_").replace(":", "_")
        (OUT / f"{tag}_{split}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (OUT / f"{gen.name.replace('/', '_').replace(':', '_')}_summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
