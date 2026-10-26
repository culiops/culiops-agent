---
state-schema: 2
service-takeover-version: 0.6.0
service: payments
account: "123456789012"
region: us-east-1
run-started-at: 2026-05-05T09:00:00Z
run-completed-at: in progress — paused 2026-05-05T10:30:00Z
operator: arn:aws:iam::123456789012:user/alice
---

# Workflow State — payments takeover

## Run identity

- **Operator:** arn:aws:iam::123456789012:user/alice
- **Run started:** 2026-05-05T09:00:00Z
- **Run completed:** in progress — paused 2026-05-05T10:30:00Z
- **Skill version:** service-takeover v0.6.0
- **Intake:** service `payments`, account 123456789012, region us-east-1, intent `takeover`; Pay Team -> Platform Team; handoff 2026-06-15

---

## Step status

| Step | Description | Status | Started | Completed | Gate sign-off |
|---|---|---|---|---|---|
| 1 | Intake — accept operator inputs | done | 2026-05-05T09:00:00Z | 2026-05-05T09:05:00Z | alice at 2026-05-05T09:05:00Z |
| 1.5 | Information audit — identity probe, execution plan | done | 2026-05-05T09:05:00Z | 2026-05-05T09:20:00Z | alice approved plan at 2026-05-05T09:20:00Z |
| 2 | Discovery — one `service-discovery` real-discovery delegation (diagrams + live APIs) | done | 2026-05-05T09:20:00Z | 2026-05-05T10:20:00Z | alice at 2026-05-05T10:20:00Z |
| 3 | Discovery snapshot — validate, same-target check, snapshot | done | 2026-05-05T10:20:00Z | 2026-05-05T10:30:00Z | alice at 2026-05-05T10:30:00Z; session paused at Gate 4 (Day 1) |
| 4 | Runtime profile — `runtime-trace` | pending | — | — | — |
| 5 | Interview — emit questionnaire; ingest filled version | pending | — | — | — |
| 6 | Readiness scorecard | pending | — | — | — |
| 7 | Handoff package assembly | pending | — | — | — |

---

## Artifact paths

Package-relative names; the fixture keeps the snapshots under `mock-artifacts/` and `filled-interview.md`.

| Artifact | Package file | Snapshotted at | Notes |
|---|---|---|---|
| service-discovery catalog | service-catalog.md | 2026-05-05T10:30:00Z | copied as-is on Day 1; `service-discovery-schema: 1`; `Live verification: performed 2026-05-05` |
| Execution plan | execution-plan.md | 2026-05-05T09:20:00Z | authored by the skill |

---

## Same-target checks (run at every snapshot)

Each snapshot is compared with the intake values (service `payments`, account 123456789012, region us-east-1) and its age is recorded against the snapshot time. A mismatch stops the run; an age over 30 days, or any artifact reused on resume, triggers the use / verify / re-run offer.

| Artifact | Account | Region | Service | Matches intake | Age at snapshot | Offer |
|---|---|---|---|---|---|---|
| service-catalog.md (Day 1 snapshot) | 123456789012 | us-east-1 | payments | yes | 10 min (generated 2026-05-05T10:20Z, snapshotted 10:30Z) | none on Day 1 (no pre-existing artifact) |

---

## Step 1.5 probe results (derived facts only — raw command output is never recorded)

| Probe | Command (projected) | Derived fact | Timestamp |
|---|---|---|---|
| identity-probe-result | `aws sts get-caller-identity --profile prod-main --query Account` | caller account = intake account (123456789012): yes | 2026-05-05T09:08:00Z |
| cloudtrail-event-history | `aws cloudtrail lookup-events --max-results 1 --profile prod-main --region us-east-1 --query 'Events[0].EventTime'` | Event history readable: yes | 2026-05-05T09:09:00Z |
| resource-explorer-index | `aws resource-explorer-2 list-indexes --profile prod-main --region us-east-1 --query 'Indexes[].{Region:Region,Type:Type}'` | aggregator index in us-east-1: yes | 2026-05-05T09:10:00Z |

---

## Pause note

Operator paused at Gate 4 on 2026-05-05T10:30:00Z. Resume by re-invoking `service-takeover` for service `payments`; the skill reads this file first, offers use / verify / re-run for the Day-1 catalog, and asks the operator to confirm the resume point.

---

## Audit trail

```
2
0
2
6
-
0
5
-
0
5
T
0
9
:
0
0
:
0
0
Z
 
 
S
t
e
p
 
1
 
s
t
a
r
t
e
d
 
—
 
o
p
e
r
a
t
o
r
 
i
n
p
u
t
s
 
a
c
c
e
p
t
e
d


2
0
2
6
-
0
5
-
0
5
T
0
9
:
0
5
:
0
0
Z
 
 
S
t
e
p
 
1
 
g
a
t
e
 
s
i
g
n
-
o
f
f
 
b
y
 
a
l
i
c
e


2
0
2
6
-
0
5
-
0
5
T
0
9
:
0
5
:
0
0
Z
 
 
S
t
e
p
 
1
.
5
 
s
t
a
r
t
e
d
 
—
 
i
n
f
o
r
m
a
t
i
o
n
 
a
u
d
i
t


2
0
2
6
-
0
5
-
0
5
T
0
9
:
0
8
:
0
0
Z
 
 
P
r
o
b
e
 
i
d
e
n
t
i
t
y
-
p
r
o
b
e
-
r
e
s
u
l
t
:
 
c
a
l
l
e
r
 
a
c
c
o
u
n
t
 
m
a
t
c
h
e
s
 
i
n
t
a
k
e
 
(
d
e
r
i
v
e
d
 
f
a
c
t
 
o
n
l
y
)


2
0
2
6
-
0
5
-
0
5
T
0
9
:
0
9
:
0
0
Z
 
 
P
r
o
b
e
 
c
l
o
u
d
t
r
a
i
l
-
e
v
e
n
t
-
h
i
s
t
o
r
y
:
 
E
v
e
n
t
 
h
i
s
t
o
r
y
 
r
e
a
d
a
b
l
e
 
(
l
o
o
k
u
p
-
e
v
e
n
t
s
 
-
-
m
a
x
-
r
e
s
u
l
t
s
 
1
;
 
d
e
r
i
v
e
d
 
f
a
c
t
 
o
n
l
y
)


2
0
2
6
-
0
5
-
0
5
T
0
9
:
1
0
:
0
0
Z
 
 
P
r
o
b
e
 
r
e
s
o
u
r
c
e
-
e
x
p
l
o
r
e
r
-
i
n
d
e
x
:
 
a
g
g
r
e
g
a
t
o
r
 
i
n
d
e
x
 
p
r
e
s
e
n
t
 
i
n
 
u
s
-
e
a
s
t
-
1
 
(
d
e
r
i
v
e
d
 
f
a
c
t
 
o
n
l
y
)


2
0
2
6
-
0
5
-
0
5
T
0
9
:
1
2
:
0
0
Z
 
 
E
x
e
c
u
t
i
o
n
 
p
l
a
n
 
e
m
i
t
t
e
d
 
t
o
 
e
x
e
c
u
t
i
o
n
-
p
l
a
n
.
m
d


2
0
2
6
-
0
5
-
0
5
T
0
9
:
2
0
:
0
0
Z
 
 
S
t
e
p
 
1
.
5
 
g
a
t
e
 
s
i
g
n
-
o
f
f
 
b
y
 
a
l
i
c
e
 
—
 
p
l
a
n
 
a
p
p
r
o
v
e
d


2
0
2
6
-
0
5
-
0
5
T
0
9
:
2
0
:
0
0
Z
 
 
S
t
e
p
 
2
 
s
t
a
r
t
e
d
 
—
 
O
N
E
 
s
e
r
v
i
c
e
-
d
i
s
c
o
v
e
r
y
 
d
e
l
e
g
a
t
i
o
n
 
p
r
i
n
t
e
d
 
(
r
e
a
l
-
d
i
s
c
o
v
e
r
y
:
 
2
 
d
i
a
g
r
a
m
s
 
+
 
l
i
v
e
 
A
P
I
s
)


2
0
2
6
-
0
5
-
0
5
T
1
0
:
2
0
:
0
0
Z
 
 
S
t
e
p
 
2
 
c
o
m
p
l
e
t
e
d
 
—
 
o
p
e
r
a
t
o
r
 
r
e
t
u
r
n
e
d
 
.
c
u
l
i
o
p
s
/
s
e
r
v
i
c
e
-
d
i
s
c
o
v
e
r
y
/
p
a
y
m
e
n
t
s
-
c
a
t
a
l
o
g
.
m
d
;
 
G
a
t
e
 
2
 
s
i
g
n
-
o
f
f
 
b
y
 
a
l
i
c
e


2
0
2
6
-
0
5
-
0
5
T
1
0
:
2
0
:
0
0
Z
 
 
S
t
e
p
 
3
 
s
t
a
r
t
e
d
 
—
 
c
a
t
a
l
o
g
 
s
n
a
p
s
h
o
t
 
v
a
l
i
d
a
t
i
o
n


2
0
2
6
-
0
5
-
0
5
T
1
0
:
3
0
:
0
0
Z
 
 
S
a
m
e
-
t
a
r
g
e
t
 
c
h
e
c
k
 
(
c
a
t
a
l
o
g
)
:
 
a
c
c
o
u
n
t
/
r
e
g
i
o
n
/
s
e
r
v
i
c
e
 
=
 
i
n
t
a
k
e
;
 
a
g
e
 
1
0
 
m
i
n
;
 
L
i
v
e
 
v
e
r
i
f
i
c
a
t
i
o
n
 
p
e
r
f
o
r
m
e
d
 
2
0
2
6
-
0
5
-
0
5
 
-
>
 
O
K


2
0
2
6
-
0
5
-
0
5
T
1
0
:
3
0
:
0
0
Z
 
 
S
t
e
p
 
3
 
c
o
m
p
l
e
t
e
d
 
—
 
s
n
a
p
s
h
o
t
 
s
e
r
v
i
c
e
-
c
a
t
a
l
o
g
.
m
d
;
 
G
a
t
e
 
3
 
s
i
g
n
-
o
f
f
 
b
y
 
a
l
i
c
e


2
0
2
6
-
0
5
-
0
5
T
1
0
:
3
0
:
0
0
Z
 
 
S
t
e
p
 
4
 
i
n
v
o
c
a
t
i
o
n
 
p
r
i
n
t
e
d
 
(
r
u
n
t
i
m
e
-
t
r
a
c
e
)
;
 
o
p
e
r
a
t
o
r
 
t
y
p
e
d
 
"
p
a
u
s
e
"
 
—
 
s
e
s
s
i
o
n
 
p
a
u
s
e
d
 
a
t
 
G
a
t
e
 
4
.
 
S
t
a
t
e
 
w
r
i
t
t
e
n
.
```
