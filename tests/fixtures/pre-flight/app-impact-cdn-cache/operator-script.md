# Operator script

What the operator types, in order. Answer only when asked.

**Opening message**

"Pre-flight please. Marketing wants the catalog pages faster, so I'm adding a cache behavior for `/api/catalog/*`. Plan is in `plan-output.txt`, code in `infra/`. Account 777788889999, CloudFront is global but the stack lives in us-west-2, workspace `prod`. CI applies on merge."

**Scope confirmation (when asked)**

"Yes."

**L2 answers (when asked)**

1. Active incident: no
2. Deploy freeze: no
3. Peak traffic: no
4. Changed this service before: many times
5. Used Terraform before: experienced
6. Cost impact: it should go down
7. Other context: "The catalog is all public product data, there's a note about it in the service catalog."

**L3 (when asked)**

"Yes."

**Application source (when asked)**

"Local checkout at `../shopfront-api`, it's on the deployed tag."

**Gate decision (when asked)**

"I'll read it first."
