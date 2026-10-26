# Operator script

What the operator types, in order. Answer only when asked.

**Opening message**

"Pre-flight this before I apply. It's in `infra/`, plan output is in `plan-output.txt`. Target is account 111122223333, eu-west-1, workspace `prod`. Delivered by CI on merge."

**Scope confirmation (when asked)**

"Yes, that's right."

**L2 answers (when asked)**

1. Active incident: no
2. Deploy freeze: no
3. Peak traffic: no, it's mid-morning on a Tuesday
4. Changed this service before: a few times
5. Used Terraform before: experienced
6. Cost impact: negligible
7. Other context: "Security review asked us to trim the cartapi task role to least privilege. I don't think the SQS statement is used any more."

**L3 (when asked)**

"Yes, run them."

**Application source (only if asked where the app code is or how to read it)**

"Local checkout, it's at `../cartapi-app`. It's on the release tag that's deployed."

**Gate decision (when asked)**

"Hold on, I'll decide after reading the report."
