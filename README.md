<p align="center">
  <img src="docs/img/banner.svg" alt="HR Onboarding AI Assistant" width="100%">
</p>

<p align="center">
  <a href="https://github.com/achux11/hr-onboarding-ai-assistant/actions/workflows/ci.yml"><img src="https://github.com/achux11/hr-onboarding-ai-assistant/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white" alt="Python 3.11">
  <img src="https://img.shields.io/badge/RAG-scikit--learn-F7931E?logo=scikitlearn&logoColor=white" alt="RAG with scikit-learn">
  <img src="https://img.shields.io/badge/tests-10%20passing-2ea44f" alt="8 tests passing">
  <img src="https://img.shields.io/badge/LLM-Claude%20(optional)-D97757" alt="Claude optional">
</p>

<p align="center">
  <b>New hires ask HR the same questions every week, and sensitive questions arrive mixed in with routine ones.</b><br>
  This project maps the onboarding process the way an HR platform team would, then adds an AI assistant that answers<br>
  routine questions with sources, hands sensitive ones to a person, and never guesses.
</p>

<p align="center">
  <a href="#-how-it-works">How it works</a> ·
  <a href="#-results">Results</a> ·
  <a href="#-process-design">Process design</a> ·
  <a href="#-quick-start">Quick start</a> ·
  <a href="#-whats-next">What's next</a>
</p>

---

## 💬 See it in action

<p align="center">
  <img src="docs/img/demo.svg" alt="Sample conversation: an answer with a source, a visa question handed to HR, and an out-of-scope question declined" width="85%">
</p>

## 🧭 How it works

Every message goes down exactly one of four routes:

```mermaid
flowchart LR
    Q([New hire question]) --> G{Sensitive topic?}
    G -- yes --> E[🛑 escalate<br/>handoff to HR specialist]
    G -- no --> C{Asking for a plan?}
    C -- yes --> L[📅 checklist<br/>dated tasks by scope item]
    C -- no --> R[🔎 retrieve best policy section]
    R --> S{Specific match?}
    S -- yes --> A[✅ answer<br/>with source cited]
    S -- no --> X[🤷 abstain<br/>please ask HR]
```

| Route | When | What the new hire gets |
|:--|:--|:--|
| ✅ **answer** | A policy covers the question | An answer drawn only from that policy, citing the document and section |
| 🛑 **escalate** | Harassment, medical or accommodation, visa, pay changes, discipline, legal | No AI answer. A handoff to HR with a category |
| 📅 **checklist** | "What do I need to do?" | A dated onboarding plan grouped by scope item, each task linked to its policy |
| 🤷 **abstain** | No policy really covers it | "I couldn't find this, please ask HR" instead of a guess |

The knowledge base is **8 HR policies, 39 sections** for *Example Co.*, a made-up company ([`policies/`](policies)).

## 📊 Results

84 labeled questions. All tuning used the **dev** set. The **holdout** set was written *before* any tuning and scored once.

| Metric | Dev (52) | Holdout (32) |
|:--|:--:|:--:|
| End-to-end correct (right route **and** right source) | 88.5% | **81.2%** |
| Retrieval hit@1 | 84.2% | **91.7%** |
| Retrieval hit@3 | 92.1% | **95.8%** |
| Sensitive questions escalated | 8 / 8 | **3 / 4** |
| Routine questions wrongly escalated | 0 | 1 |
| Out-of-scope questions declined | 4 / 4 | **3 / 3** |

> Baseline before tuning: **65.4%** end-to-end on the first dev half. Tuning added a short HR synonym list ("vacation" means PTO, "baby" means a qualifying life event) and an abstain rule: if a question only matches words that appear in many policies, like *office* or *work*, the assistant declines.

### ✍️ Answer generation

Retrieval picks the policy section; a **generator** writes the answer from that section only. Every generated answer is checked against a hand-written answer key (62 answerable questions) and for **unsupported numbers**: any number in the answer that is not in the retrieved policy or the question counts as a hallucination.

| Generator | Holdout answers correct | Correct when retrieval is right | Answers with unsupported numbers |
|:--|:--:|:--:|:--:|
| **Extractive baseline (no model)** | **79.2%** | **100%** | **0%** |
| Open model: Qwen2.5-1.5B-Instruct (Colab T4) | 66.7% | 84.2% | 9.5% |
| Claude | *not run yet* | | |

**Finding: the small open model did worse than the extractive baseline, so extractive stays the default.** Reading its holdout answers shows why:

- *"If I start on the 15th, when does medical coverage begin?"* → "the following day, which is the 16th". Policy: the first day of the next month.
- *"What happens if payday lands on a holiday?"* → "employees may need to work overtime". Not in any policy.
- *"Will I get a paper check before direct deposit is ready?"* → "No". Policy says yes. The keyword answer key still marked this **correct**, because the right words appear in a wrong sentence. Keyword grading misses contradictions, so generated answers also need a human review or an LLM judge.

Dev split, same model: 81.6% correct, 2.6% with unsupported numbers.

Run the open-model and Claude evaluations for free in Colab: [`notebooks/generation_eval_colab.ipynb`](notebooks/generation_eval_colab.ipynb) <a href="https://colab.research.google.com/github/achux11/hr-onboarding-ai-assistant/blob/main/notebooks/generation_eval_colab.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open in Colab"></a>

<details>
<summary><b>⚠️ Known misses on the holdout set (left as found)</b></summary>

<br>

- *"Someone at work keeps sending me sexual messages"* was **not** escalated. Keyword guardrails miss new wording, so a real deployment needs a trained classifier or an LLM check in front of them. **This is the most important limitation.**
- *"Is retaliation allowed if I report something?"* was escalated even though policy answers it. That's the safer kind of mistake.
- Questions that mix two topics, such as *"payday lands on a holiday"*, sometimes pull the wrong section.

</details>

## 🗺️ Process design

The onboarding process, broken down before any code was written:

| Document | What's inside |
|:--|:--|
| [Process flow](docs/process_flow.md) | End-to-end flow from offer to 90-day check-in, current-state pain points, target state |
| [Scope items](docs/scope_items.md) | 7 discrete scope items (OB-01 to OB-07) with trigger, owner, steps and output |
| [User stories](docs/user_stories.md) | 5 sprint-ready stories with acceptance criteria, each mapped to a scope item |

<details>
<summary><b>📅 Sample checklist for a January 4, 2027 start</b></summary>

```text
Jan 03  [OB-01 Pre-boarding]          Receive login instructions at personal email
Jan 04  [OB-02 Day One Setup]         Set up multi-factor authentication
Jan 04  [OB-02 Day One Setup]         Meet onboarding buddy
Jan 08  [OB-03 Payroll Setup]         Set up direct deposit
Jan 11  [OB-03 Payroll Setup]         Complete W-4 before first payday
Feb 03  [OB-04 Benefits Enrollment]   Enroll in medical, dental and vision
Feb 03  [OB-05 Learning & Compliance] Complete security, privacy and conduct training
Feb 03  [OB-05 Learning & Compliance] 30-day check-in with manager
Mar 05  [OB-06 Workplace Setup]       Claim home office stipend (hybrid/remote)
Mar 05  [OB-05 Learning & Compliance] 60-day check-in with manager
Apr 04  [OB-05 Learning & Compliance] 90-day check-in with manager
```

</details>

## 🚀 Quick start

```bash
git clone https://github.com/achux11/hr-onboarding-ai-assistant
cd hr-onboarding-ai-assistant
pip install -r requirements.txt

python -m assistant "When does my health insurance start?"
python -m assistant "Give me my onboarding checklist"

python -m eval.run_eval   # routing + retrieval report → eval/results.json
python -m eval.run_generation_eval --backend extractive   # answer quality
pytest -q                 # 10 tests, including a quality floor on the dev set
```

Generators live in `assistant/generate.py`: `extractive` (default, no model, repeatable), `hf` (any open instruct model through Hugging Face transformers) and `claude` (needs `ANTHROPIC_API_KEY`). All three get the same instruction: answer only from the retrieved policy, keep exact numbers, and say "I don't know, please ask HR" when the policy does not cover the question.

## 🧱 Project structure

```text
├── docs/            process flow · scope items · user stories · images
├── policies/        8 sample HR policies (fictional company)
├── assistant/
│   ├── retriever.py     section-level TF-IDF retrieval, HR synonyms, generic-word check
│   ├── guardrails.py    sensitive-topic categories that always go to a person
│   ├── checklist.py     dated onboarding plan by scope item
│   ├── generate.py      answer generators: extractive, open model, Claude
│   └── agent.py         routes each question, returns cited responses
├── eval/            84 labeled questions with answer keys, routing and generation evaluations
├── notebooks/       Colab notebook for the open-model and Claude generation runs
└── tests/           pytest suite, run on every push by GitHub Actions
```

## 🔭 What's next

- [ ] Replace keyword guardrails with an LLM or trained classifier and measure recall on a larger sensitive-question set
- [ ] Swap TF-IDF for embedding retrieval and compare on the same holdout set
- [ ] Run Claude on the same holdout set, and fall back to the extractive answer whenever a generated answer contains a number not found in the policy
- [ ] Grade generated answers for contradictions, not just keywords
- [ ] Connect to an HR platform's onboarding module so checklist tasks become real assignments

<p align="center"><sub>Built by <a href="https://github.com/achux11">Achintya Vamshi Nudurupati</a> · Policies are fictional and for demonstration only</sub></p>
