"""Builds a dated onboarding checklist from the policies, grouped by scope item."""
from __future__ import annotations

from datetime import date, timedelta

# (scope item, task, days after start, source policy)
TASKS = [
    ("OB-01 Pre-boarding", "Receive login instructions at personal email", -1, "it_equipment.md > Accounts and login"),
    ("OB-01 Pre-boarding", "Receive shipped laptop (remote hires)", -3, "it_equipment.md > Laptop"),
    ("OB-02 Day One Setup", "Set up multi-factor authentication", 0, "it_equipment.md > Multi-factor authentication"),
    ("OB-02 Day One Setup", "Meet onboarding buddy", 0, "training.md > Onboarding buddy"),
    ("OB-03 Payroll Setup", "Set up direct deposit", 4, "payroll.md > Direct deposit"),
    ("OB-03 Payroll Setup", "Complete W-4 before first payday", 7, "payroll.md > Tax forms"),
    ("OB-04 Benefits Enrollment", "Enroll in medical, dental and vision", 30, "benefits.md > Enrollment deadline"),
    ("OB-05 Learning & Compliance", "Complete security, privacy and conduct training", 30, "training.md > Compliance training"),
    ("OB-05 Learning & Compliance", "30-day check-in with manager", 30, "training.md > 30-60-90 day check-ins"),
    ("OB-06 Workplace Setup", "Claim home office stipend (hybrid/remote)", 60, "remote_work.md > Home office stipend"),
    ("OB-05 Learning & Compliance", "60-day check-in with manager", 60, "training.md > 30-60-90 day check-ins"),
    ("OB-05 Learning & Compliance", "90-day check-in with manager", 90, "training.md > 30-60-90 day check-ins"),
]


def build(start: date, remote: bool = False) -> list[dict]:
    rows = []
    for scope, task, offset, source in TASKS:
        if "remote hires" in task and not remote:
            continue
        rows.append({"scope_item": scope, "task": task, "due": start + timedelta(days=offset), "source": source})
    return sorted(rows, key=lambda r: r["due"])
