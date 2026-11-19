# Onboarding Process Flow

End-to-end new-hire onboarding at Example Co., from signed offer to the 90-day check-in, with the points where the AI assistant helps and where a person stays in charge.

```mermaid
flowchart LR
    A[Offer accepted] --> B[OB-01 Pre-boarding<br/>accounts, laptop, login email]
    B --> C[OB-02 Day One Setup<br/>MFA, buddy, office tour]
    C --> D[OB-03 Payroll Setup<br/>direct deposit, W-4]
    C --> E[OB-04 Benefits Enrollment<br/>within 30 days]
    C --> F[OB-05 Learning & Compliance<br/>training within 30 days]
    C --> G[OB-06 Workplace Setup<br/>hybrid schedule, stipend]
    D & E & F & G --> H[30 / 60 / 90 day check-ins]
    Q{{New hire question}} --> R{AI assistant}
    R -->|policy answer with citation| S[New hire]
    R -->|sensitive topic| T[HR specialist]
    R -->|not in policies| U[Ask HR]
```

## Current state pain points

| # | Pain point | Effect |
|---|---|---|
| 1 | New hires email HR the same questions: PTO, first paycheck, benefits deadline | HR spends time on repeat questions |
| 2 | Deadlines live in different policies (benefits 30 days, training 30 days, stipend 60 days) | Missed deadlines, such as losing the benefits window |
| 3 | No single onboarding plan per person | Managers and new hires track tasks by memory |
| 4 | Sensitive questions arrive mixed with routine ones | Risk of a generic answer to a harassment or medical question |

## Target state

- Routine policy questions are answered at once, with the exact policy section cited.
- Every new hire gets a dated checklist grouped by scope item.
- Sensitive topics never get an AI answer. They go to an HR specialist with a category.
- If no policy covers the question, the assistant says so instead of guessing.
