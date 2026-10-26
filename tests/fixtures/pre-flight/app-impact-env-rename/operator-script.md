# Operator script

What the operator types, in order. Answer only when asked.

**Opening message**

"Can you pre-flight this? Platform team is standardising env var names across services. Plan is in `plan-output.txt`, code in `infra/`. Account 444455556666, ap-northeast-1, workspace `prod`, CI applies on merge."

**Scope confirmation (when asked)**

"Correct."

**L2 answers (when asked)**

1. Active incident: no
2. Deploy freeze: no
3. Peak traffic: no
4. Changed this service before: first time
5. Used Terraform before: experienced
6. Cost impact: negligible
7. Other context: "It's only renaming variables, the values are the same."

**L3 (when asked)**

"No, I don't have prod read access from this laptop today."

**Application source (when asked)**

"The app is on GitHub, `acme-billing/invoicesvc`, the deployed version is tag `v3.8.2`. I can use `gh`, it's logged in."

**Gate decision (when asked)**

"Let me read it first."
