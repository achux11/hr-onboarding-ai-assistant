from datetime import date

from assistant import checklist, guardrails
from assistant.agent import OnboardingAgent
from assistant.retriever import load_sections
from eval.run_eval import evaluate, load

BOT = OnboardingAgent()


def test_every_policy_has_sections():
    sections = load_sections()
    assert len(sections) >= 35
    assert all(s.text for s in sections)


def test_answer_has_citation():
    r = BOT.ask("How many sick days do I get?")
    assert r.route == "answer"
    assert r.citations == ["time_off.md > Sick leave"]
    assert "6 paid sick days" in r.text


def test_sensitive_question_is_never_answered():
    r = BOT.ask("Will the company sponsor my H-1B visa?")
    assert r.route == "escalate" and r.category == "immigration_or_visa"


def test_unknown_question_abstains():
    assert BOT.ask("Is there free parking at the office?").route == "abstain"


def test_guardrail_does_not_flag_routine_question():
    assert guardrails.check("When is payday?") is None


def test_checklist_dates_follow_policy():
    plan = checklist.build(date(2027, 1, 4), remote=True)
    due = {r["task"]: r["due"] for r in plan}
    assert due["Enroll in medical, dental and vision"] == date(2027, 2, 3)
    assert due["Receive shipped laptop (remote hires)"] == date(2027, 1, 1)


def test_checklist_skips_remote_steps_for_office_hires():
    assert not any("remote hires" in r["task"] for r in checklist.build(date(2027, 1, 4)))


def test_quality_floor_on_dev_set():
    m = evaluate(load("dev"), BOT)
    assert m["escalation_recall_%"] == 100.0
    assert m["false_escalations"] == 0
    assert m["end_to_end_correct_%"] >= 85.0


def test_generation_eval_checks_facts_and_numbers():
    from eval.run_generation_eval import has_facts, unsupported_numbers

    assert has_facts("You get 15 days of PTO.", [["15 days", "fifteen"]])
    assert not has_facts("You get PTO.", [["15 days"]])
    assert unsupported_numbers("You get 20 days.", "You accrue 15 days.", "How many?") == ["20"]


def test_extractive_answers_are_correct_when_retrieval_is_right():
    from eval.run_generation_eval import evaluate

    summary, _ = evaluate("dev", BOT)
    assert summary["correct_given_hit_%"] == 100.0
    assert summary["unsupported_number_%"] == 0.0
