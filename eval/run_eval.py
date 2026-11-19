"""Evaluate the onboarding assistant on the labeled question set.

The threshold sweep runs on the dev split only. The holdout split was written before any tuning and is reported once
with the threshold fixed in assistant/agent.py.

    python -m eval.run_eval            # dev + test report
    python -m eval.run_eval --sweep    # threshold sweep on dev
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from assistant import agent as agent_mod
from assistant.agent import OnboardingAgent

QUESTIONS = Path(__file__).with_name("questions.jsonl")


def load(split: str | None = None) -> list[dict]:
    rows = [json.loads(line) for line in QUESTIONS.read_text().splitlines() if line.strip()]
    return [r for r in rows if split is None or r["split"] == split]


def evaluate(rows: list[dict], bot: OnboardingAgent) -> dict:
    route_ok = hit1 = hit3 = answerable = esc_tp = esc_total = false_esc = abstain_ok = abstain_total = 0
    misses = []
    for r in rows:
        resp = bot.ask(r["question"])
        ok = resp.route == r["route"]
        if r["route"] == "answer":
            answerable += 1
            top3 = [s.citation for s, _ in bot.retriever.search(r["question"], k=3)]
            hit1 += top3[0] == r["expected"]
            hit3 += r["expected"] in top3
            ok = ok and resp.citations == [r["expected"]]
            false_esc += resp.route == "escalate"
        elif r["route"] == "escalate":
            esc_total += 1
            esc_tp += resp.route == "escalate"
        elif r["route"] == "abstain":
            abstain_total += 1
            abstain_ok += resp.route == "abstain"
        route_ok += ok
        if not ok:
            misses.append({"id": r["id"], "question": r["question"], "expected": r["expected"] or r["route"],
                           "got": resp.citations[0] if resp.route == "answer" else resp.route})
    pct = lambda a, b: round(100 * a / b, 1) if b else None
    return {
        "questions": len(rows),
        "end_to_end_correct_%": pct(route_ok, len(rows)),
        "retrieval_hit@1_%": pct(hit1, answerable),
        "retrieval_hit@3_%": pct(hit3, answerable),
        "escalation_recall_%": pct(esc_tp, esc_total),
        "false_escalations": false_esc,
        "abstain_correct_%": pct(abstain_ok, abstain_total),
        "misses": misses,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--sweep", action="store_true")
    args = p.parse_args()
    bot = OnboardingAgent()
    if args.sweep:
        for t in [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20]:
            agent_mod.MIN_SCORE = t
            m = evaluate(load("dev"), bot)
            print(f"threshold {t:.2f}: dev end-to-end {m['end_to_end_correct_%']}%  abstain {m['abstain_correct_%']}%")
        return
    report = {split: evaluate(load(split), bot) for split in ("dev", "holdout")}
    print(json.dumps(report, indent=2, default=str))
    Path(__file__).with_name("results.json").write_text(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
