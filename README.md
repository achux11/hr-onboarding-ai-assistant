# HR Onboarding AI Assistant

[![CI](https://github.com/achux11/hr-onboarding-ai-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/achux11/hr-onboarding-ai-assistant/actions/workflows/ci.yml)

**A new hire has questions about PTO, the first paycheck and the benefits deadline. HR answers the same ones every week, and sensitive questions arrive mixed in with routine ones.**

This project does two things:

1. **Process design.** Breaks the end-to-end onboarding process into a [process flow](docs/process_flow.md), 7 [scope items](docs/scope_items.md) and 5 sprint-ready [user stories](docs/user_stories.md) with acceptance criteria.
2. **AI assistant.** A retrieval-augmented (RAG) assistant that sends each question down one of four routes:

| Route | When | What the new hire gets |
|---|---|---|
| `answer` | A policy covers the question | An answer taken only from that policy, with the document and section cited |
| `escalate` | Harassment, medical or accommodation, visa, compensation change, discipline, legal | No AI answer. A handoff to an HR specialist with a category |
| `checklist` | "What do I need to do?" | A dated onboarding plan, grouped by scope item, each task linked to its policy |
| `abstain` | No policy really covers it | "I couldn't find this, please ask HR", instead of a guess |

The policies in [`policies/`](policies) are for **Example Co.**, a made-up company: 8 documents, 39 sections.

## Results

Measured on 84 labeled questions. Tuning used only the 52-question dev set. The 32-question holdout set was written **before** any tuning and scored once.

| Metric | Dev (52) | Holdout (32) |
|---|---|---|
| End-to-end correct (right route and right source) | 88.5% | **81.2%** |
| Retrieval hit@1 | 84.2% | **91.7%** |
| Retrieval hit@3 | 92.1% | **95.8%** |
| Sensitive questions escalated | 100% (8/8) | **75% (3/4)** |
| Routine questions wrongly escalated | 0 | 1 |
| Out-of-scope questions correctly declined | 100% | **100%** |

Starting point before tuning: 65.4% end-to-end on the first dev half.

**What changed during tuning:** a short HR synonym list ("vacation" means PTO, "baby" means a qualifying life event), and an abstain rule. If a question only matches words found in many policies, such as "office" or "work", the assistant declines instead of guessing.

**Known misses on the holdout set**, left as found:
- *"Someone at work keeps sending me sexual messages"* was **not** escalated. Keyword guardrails miss new wording, and a real deployment would need a trained classifier or an LLM check in front of them. This is the most important limitation.
- *"Is retaliation allowed if I report something?"* was escalated even though policy answers it. That's the safer kind of mistake.
- Questions that mix two topics, like *"payday lands on a holiday"*, sometimes retrieve the wrong section.

## Run it

```bash
pip install -r requirements.txt
python -m assistant "When does my health insurance start?"
python -m assistant "Give me my onboarding checklist"
python -m eval.run_eval          # dev and holdout report, writes eval/results.json
pytest -q                        # 8 tests, including a quality floor on the dev set
```

By default answers are the most relevant sentences from the cited policy section, so results are repeatable. If `ANTHROPIC_API_KEY` is set and `use_llm=True`, Claude rewrites the answer using **only** the retrieved policy text. The evaluation above uses the default mode.

## Project layout

```
docs/             process flow, scope items, user stories
policies/         sample HR policies (fictional company)
assistant/
  retriever.py    section-level TF-IDF retrieval with HR synonyms and a generic-word check
  guardrails.py   sensitive-topic categories that always go to a person
  checklist.py    dated onboarding plan by scope item
  agent.py        routes each question and returns cited responses
eval/             84 labeled questions, dev/holdout split, evaluation script
tests/            pytest suite run in GitHub Actions
```

## Next steps

- Replace keyword guardrails with an LLM or trained classifier, and measure recall on a larger set of sensitive questions.
- Swap TF-IDF for embedding retrieval and compare on the same holdout set.
- Connect to an HR platform's onboarding module so checklist tasks are created as real assignments.
