# User Stories

Sprint-ready stories with acceptance criteria. Each story maps to a scope item.

### US-01 Policy answers with sources (OB-07)
**As a** new hire, **I want** quick answers to policy questions **so that** I don't wait on HR for routine information.
- Given a question covered by a policy, when I ask it, then I get an answer drawn only from that policy and the document and section it came from.
- Given a question no policy covers, when I ask it, then the assistant says it could not find the answer and points me to HR.

### US-02 Sensitive topic handoff (OB-07)
**As an** HR specialist, **I want** sensitive questions routed to me **so that** employees get help from a person, not a generated answer.
- Given a question about harassment, discrimination, medical needs, accommodations, visas, compensation changes, discipline or legal action, then the assistant does not answer and creates a handoff with a category.
- Escalation recall is measured on a labeled test set before each release.

### US-03 Dated onboarding checklist (OB-01 to OB-06)
**As a** new hire, **I want** a checklist with due dates **so that** I don't miss deadlines like benefits enrollment.
- Given my start date, then I get every onboarding task with a due date, its scope item and the policy it comes from.
- Remote hires see the laptop shipping step and hybrid hires see the home office stipend.

### US-04 Benefits deadline reminder (OB-04)
**As a** benefits specialist, **I want** new hires reminded of the 30-day enrollment window **so that** fewer people miss it.
- The checklist shows the enrollment due date as start date plus 30 days.

### US-05 Release quality check (all)
**As the** HR systems owner, **I want** every change tested against labeled questions **so that** quality never drops without anyone noticing.
- The test suite runs on every push and fails if routing or escalation quality falls below the agreed floor.
