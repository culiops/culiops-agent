---
state-schema: 2
service-takeover-version: 0.6.0
service: payments
account: "123456789012"
region: us-east-1
run-started-at: 2026-05-12T14:00:00Z
run-completed-at: 2026-05-12T16:10:00Z
operator: arn:aws:iam::123456789012:user/alice
---

# Workflow State — payments takeover

## Run identity

- **Operator:** arn:aws:iam::123456789012:user/alice
- **Run started:** 2026-05-12T14:00:00Z
- **Run completed:** 2026-05-12T16:10:00Z
- **Skill version:** service-takeover v0.6.0
- **Intake:** service `payments`, account 123456789012, region us-east-1, intent `takeover`; Pay Team -> Platform Team; handoff 2026-06-15

---

## Step status

| Step | Description | Status | Started | Completed | Gate sign-off |
|---|---|---|---|---|---|
| 1 | Intake — accept operator inputs | done | 2026-05-12T14:00:00Z | 2026-05-12T14:03:00Z | alice at 2026-05-12T14:03:00Z |
| 1.5 | Information audit — identity probe, execution plan | done | 2026-05-12T14:03:00Z | 2026-05-12T14:12:00Z | alice approved plan at 2026-05-12T14:12:00Z |
| 2 | Discovery — one `service-discovery` real-discovery delegation (diagrams + live APIs) | done | 2026-05-12T14:12:00Z | 2026-05-12T14:30:00Z | alice at 2026-05-12T14:30:00Z |
| 3 | Discovery snapshot — validate, same-target check, snapshot | done | 2026-05-12T14:30:00Z | 2026-05-12T14:33:00Z | alice at 2026-05-12T14:33:00Z |
| 4 | Runtime profile — `runtime-trace` (its own 7 gates: 1, 1a, 2–6) | done | 2026-05-12T14:33:00Z | 2026-05-12T15:05:00Z | alice at 2026-05-12T15:05:00Z |
| 5 | Interview — emit questionnaire; ingest filled version | done | 2026-05-12T15:05:00Z | 2026-05-12T15:45:00Z | alice at 2026-05-12T15:45:00Z; sections: 11 complete / 0 partial / 0 empty |
| 6 | Readiness scorecard — auto-mark, Step 6 verification batch, attestations | done | 2026-05-12T15:45:00Z | 2026-05-12T16:05:00Z | alice at 2026-05-12T16:05:00Z; verdict: not-ready |
| 7 | Handoff package assembly | done | 2026-05-12T16:05:00Z | 2026-05-12T16:10:00Z | alice at 2026-05-12T16:10:00Z |

---

## Artifact paths

Package-relative names; the fixture keeps the snapshots under `mock-artifacts/` and `filled-interview.md`.

| Artifact | Package file | Snapshotted at | Notes |
|---|---|---|---|
| service-discovery catalog | service-catalog.md | 2026-05-12T14:33:00Z | copied as-is; `service-discovery-schema: 1`; `Live verification: performed 2026-05-12` |
| runtime-trace profile | runtime-profile.md | 2026-05-12T15:05:00Z | copied as-is; `runtime-profile-schema: 2` |
| Filled interview | interview-questionnaire.md | 2026-05-12T15:45:00Z | snapshot of `filled-interview.md` (variant A: incoming role not yet permitted, 3-5 deploys/week, DR to us-west-2) |
| Readiness scorecard | readiness-scorecard.md | 2026-05-12T16:05:00Z | authored by the skill |
| Open questions | open-questions.md | 2026-05-12T16:05:00Z | authored by the skill |
| Execution plan | execution-plan.md | 2026-05-12T14:12:00Z | Step 6 addendum added at 2026-05-12T15:50:00Z |
| Handoff README | README.md | 2026-05-12T16:10:00Z | authored by the skill |

---

## Same-target checks (run at every snapshot)

Each snapshot is compared with the intake values (service `payments`, account 123456789012, region us-east-1) and its age is recorded against the snapshot time. A mismatch stops the run; an age over 30 days, or any artifact reused on resume, triggers the use / verify / re-run offer.

| Artifact | Account | Region | Service | Matches intake | Age at snapshot | Offer |
|---|---|---|---|---|---|---|
| service-catalog.md | 123456789012 | us-east-1 | payments | yes | 3 min (generated 14:30Z, snapshotted 14:33Z) | none (no pre-existing artifact; < 30 d) |
| runtime-profile.md | 123456789012 | us-east-1 | payments | yes | 5 min (generated 15:00Z, snapshotted 15:05Z) | none (< 30 d) |
| catalog vs profile | — | — | — | yes: catalog inventory (8 names) = profile resolved set (8 names) | — | — |

---

## Step 1.5 probe results (derived facts only — raw command output is never recorded)

| Probe | Command (projected) | Derived fact | Timestamp |
|---|---|---|---|
| identity-probe-result | `aws sts get-caller-identity --profile prod-main --query Account` | caller account = intake account (123456789012): yes | 2026-05-12T14:05:00Z |
| cloudtrail-event-history | `aws cloudtrail lookup-events --max-results 1 --profile prod-main --region us-east-1 --query 'Events[0].EventTime'` | Event history readable: yes | 2026-05-12T14:06:00Z |
| resource-explorer-index | `aws resource-explorer-2 list-indexes --profile prod-main --region us-east-1 --query 'Indexes[].{Region:Region,Type:Type}'` | aggregator index in us-east-1: yes | 2026-05-12T14:07:00Z |

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
1
2
T
1
4
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
1
2
T
1
4
:
0
3
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
1
2
T
1
4
:
0
3
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
1
2
T
1
4
:
0
5
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
1
2
T
1
4
:
0
6
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
1
2
T
1
4
:
0
7
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
1
2
T
1
4
:
0
9
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
1
2
T
1
4
:
1
2
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
1
2
T
1
4
:
1
2
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
1
2
T
1
4
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
1
2
T
1
4
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
1
2
T
1
4
:
3
3
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
 
3
 
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
1
2
T
1
4
:
3
3
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
1
2
T
1
4
:
3
3
:
0
0
Z
 
 
S
t
e
p
 
4
 
s
t
a
r
t
e
d
 
—
 
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
t
a
g
:
s
e
r
v
i
c
e
=
p
a
y
m
e
n
t
s
,
 
i
n
t
e
n
t
 
t
a
k
e
o
v
e
r
,
 
-
-
r
e
d
a
c
t
 
n
o
t
 
s
e
t
)


2
0
2
6
-
0
5
-
1
2
T
1
5
:
0
5
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
p
r
o
f
i
l
e
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
 
5
 
m
i
n
;
 
r
e
s
o
l
v
e
d
 
s
e
t
 
=
 
c
a
t
a
l
o
g
 
i
n
v
e
n
t
o
r
y
 
(
8
 
=
 
8
)
 
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
1
2
T
1
5
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
 
4
 
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
 
r
u
n
t
i
m
e
-
p
r
o
f
i
l
e
.
m
d
 
(
s
c
h
e
m
a
 
2
)
;
 
G
a
t
e
 
4
 
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
1
2
T
1
5
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
 
5
 
s
t
a
r
t
e
d
 
—
 
q
u
e
s
t
i
o
n
n
a
i
r
e
 
e
m
i
t
t
e
d
;
 
a
w
a
i
t
i
n
g
 
o
u
t
g
o
i
n
g
 
t
e
a
m


2
0
2
6
-
0
5
-
1
2
T
1
5
:
4
0
:
0
0
Z
 
 
F
i
l
l
e
d
 
i
n
t
e
r
v
i
e
w
 
r
e
c
e
i
v
e
d
 
f
r
o
m
 
B
o
b
 
L
.
 
(
P
a
y
 
T
e
a
m
)
 
—
 
f
i
l
l
e
d
-
i
n
t
e
r
v
i
e
w
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
1
2
T
1
5
:
4
5
:
0
0
Z
 
 
S
t
e
p
 
5
 
i
n
g
e
s
t
:
 
1
1
 
c
o
m
p
l
e
t
e
 
/
 
0
 
p
a
r
t
i
a
l
 
/
 
0
 
e
m
p
t
y
;
 
G
a
t
e
 
5
 
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
1
2
T
1
5
:
4
5
:
0
0
Z
 
 
S
t
e
p
 
6
 
s
t
a
r
t
e
d
 
—
 
a
u
t
o
-
m
a
r
k
i
n
g
 
s
c
o
r
e
c
a
r
d
 
f
r
o
m
 
a
r
t
i
f
a
c
t
s


2
0
2
6
-
0
5
-
1
2
T
1
5
:
4
6
:
0
0
Z
 
 
O
p
e
r
a
t
o
r
 
c
o
n
f
i
r
m
e
d
 
d
e
p
l
o
y
 
r
o
l
e
 
p
a
y
m
e
n
t
s
-
d
e
p
l
o
y
-
r
o
l
e
 
(
i
t
e
m
 
2
:
 
◐
 
-
>
 
✓
 
v
e
r
i
f
i
e
d
)


2
0
2
6
-
0
5
-
1
2
T
1
5
:
4
8
:
0
0
Z
 
 
S
t
e
p
 
6
 
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
 
b
a
t
c
h
 
p
r
o
p
o
s
e
d
:
 
3
 
r
e
a
d
-
o
n
l
y
 
A
W
S
 
c
o
m
m
a
n
d
s
 
(
i
t
e
m
s
 
1
0
,
 
2
4
,
 
1
5
)
 
+
 
a
r
t
i
f
a
c
t
 
c
o
m
p
a
r
i
s
o
n
s


2
0
2
6
-
0
5
-
1
2
T
1
5
:
5
0
:
0
0
Z
 
 
B
a
t
c
h
 
a
p
p
r
o
v
e
d
 
b
y
 
a
l
i
c
e
;
 
i
d
e
n
t
i
t
y
 
r
e
-
c
h
e
c
k
e
d
 
(
a
c
c
o
u
n
t
 
1
2
3
4
5
6
7
8
9
0
1
2
)


2
0
2
6
-
0
5
-
1
2
T
1
5
:
5
2
:
1
0
Z
 
 
B
a
t
c
h
 
1
/
3
 
d
e
s
c
r
i
b
e
-
a
l
a
r
m
s
:
 
5
 
a
l
a
r
m
s
,
 
n
a
m
e
s
 
m
a
t
c
h
 
t
h
e
 
i
n
t
e
r
v
i
e
w
,
 
a
l
l
 
w
i
t
h
 
a
c
t
i
o
n
s
 
-
>
 
i
t
e
m
 
1
0
 
✓
 
v
e
r
i
f
i
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
1
2
T
1
5
:
5
2
:
4
0
Z
 
 
B
a
t
c
h
 
2
/
3
 
d
e
s
c
r
i
b
e
-
c
o
n
t
i
n
u
o
u
s
-
b
a
c
k
u
p
s
:
 
P
I
T
R
 
E
N
A
B
L
E
D
 
-
>
 
i
t
e
m
 
2
4
 
s
t
a
y
s
 
◐
 
(
r
e
s
t
o
r
e
 
t
e
s
t
 
u
n
a
t
t
e
s
t
e
d
)


2
0
2
6
-
0
5
-
1
2
T
1
5
:
5
3
:
2
0
Z
 
 
B
a
t
c
h
 
3
/
3
 
s
i
m
u
l
a
t
e
-
p
r
i
n
c
i
p
a
l
-
p
o
l
i
c
y
 
f
o
r
 
p
l
a
t
f
o
r
m
-
t
e
a
m
-
d
e
p
l
o
y
:
 
6
/
6
 
i
m
p
l
i
c
i
t
D
e
n
y
 
-
>
 
i
t
e
m
 
1
5
 
✗


2
0
2
6
-
0
5
-
1
2
T
1
5
:
5
8
:
0
0
Z
 
 
I
t
e
m
 
3
 
a
t
t
e
s
t
e
d
 
b
y
 
a
l
i
c
e
 
(
c
o
n
s
o
l
e
 
+
 
C
L
I
)


2
0
2
6
-
0
5
-
1
2
T
1
6
:
0
0
:
0
0
Z
 
 
I
t
e
m
 
1
1
 
a
t
t
e
s
t
e
d
 
b
y
 
a
l
i
c
e
 
(
P
a
g
e
r
D
u
t
y
 
r
o
t
a
t
i
o
n
 
v
i
s
i
b
l
e
)


2
0
2
6
-
0
5
-
1
2
T
1
6
:
0
2
:
0
0
Z
 
 
I
t
e
m
 
1
2
 
a
t
t
e
s
t
e
d
 
b
y
 
a
l
i
c
e
 
(
t
e
s
t
 
p
a
g
e
 
r
e
c
e
i
v
e
d
)


2
0
2
6
-
0
5
-
1
2
T
1
6
:
0
5
:
0
0
Z
 
 
S
c
o
r
e
c
a
r
d
 
w
r
i
t
t
e
n
:
 
1
2
 
✓
 
v
e
r
i
f
i
e
d
,
 
3
 
✓
 
a
t
t
e
s
t
e
d
,
 
6
 
◐
,
 
1
 
✗
,
 
3
 
✗
 
c
o
n
f
l
i
c
t
,
 
0
 
?
,
 
0
 
N
/
A
.
 
V
e
r
d
i
c
t
:
 
n
o
t
-
r
e
a
d
y


2
0
2
6
-
0
5
-
1
2
T
1
6
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
 
6
 
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
1
2
T
1
6
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
 
7
 
s
t
a
r
t
e
d
 
—
 
h
a
n
d
o
f
f
 
p
a
c
k
a
g
e
 
a
s
s
e
m
b
l
y


2
0
2
6
-
0
5
-
1
2
T
1
6
:
1
0
:
0
0
Z
 
 
H
a
n
d
o
f
f
 
p
a
c
k
a
g
e
 
a
s
s
e
m
b
l
e
d
:
 
8
 
f
i
l
e
s
 
(
5
 
w
r
i
t
t
e
n
 
b
y
 
t
h
e
 
s
k
i
l
l
 
i
n
 
e
x
p
e
c
t
e
d
-
h
a
n
d
o
f
f
/
;
 
3
 
s
n
a
p
s
h
o
t
s
 
f
r
o
m
 
m
o
c
k
-
a
r
t
i
f
a
c
t
s
/
 
a
n
d
 
f
i
l
l
e
d
-
i
n
t
e
r
v
i
e
w
.
m
d
)


2
0
2
6
-
0
5
-
1
2
T
1
6
:
1
0
:
0
0
Z
 
 
R
e
m
i
n
d
e
r
 
p
r
i
n
t
e
d
:
 
p
r
i
v
a
t
e
 
r
e
p
o
 
o
n
l
y
;
 
c
h
e
c
k
 
b
r
a
n
c
h
 
a
n
d
 
r
e
m
o
t
e
 
v
i
s
i
b
i
l
i
t
y
 
b
e
f
o
r
e
 
c
o
m
m
i
t
t
i
n
g


2
0
2
6
-
0
5
-
1
2
T
1
6
:
1
0
:
0
0
Z
 
 
S
t
e
p
 
7
 
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
.
 
R
u
n
 
c
o
m
p
l
e
t
e
```
