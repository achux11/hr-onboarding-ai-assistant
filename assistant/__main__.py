"""Command line: python -m assistant "How many PTO days do I get?" """
import sys
from datetime import date

from .agent import OnboardingAgent

if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Give me my onboarding checklist"
    r = OnboardingAgent().ask(question, start=date.today())
    print(f"[{r.route}{' / ' + r.category if r.category else ''}]\n{r.text}")
    for c in r.citations:
        print(f"  source: {c}")
