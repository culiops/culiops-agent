---
state-schema: 2
service-takeover-version: 0.6.0
service: search-api
account: "123456789012"
region: eu-west-1
run-started-at: 2026-05-12T13:30:00Z
run-completed-at: 2026-05-12T16:00:00Z
operator: arn:aws:iam::123456789012:user/alice
---

# Workflow State — search-api takeover

## Run identity

- **Operator:** arn:aws:iam::123456789012:user/alice
- **Run started:** 2026-05-12T13:30:00Z
- **Run completed:** 2026-05-12T16:00:00Z
- **Skill version:** service-takeover v0.6.0
- **Intake:** service `search-api`, account 123456789012, region eu-west-1, intent `takeover`; Search Team -> Platform Team; handoff 2026-06-22

---

## Step status

| Step | Description | Status | Started | Completed | Gate sign-off |
|---|---|---|---|---|---|
| 1 | Intake — accept operator inputs | done | 2026-05-12T13:30:00Z | 2026-05-12T13:33:00Z | alice at 2026-05-12T13:33:00Z |
| 1.5 | Information audit — identity probe, execution plan | done | 2026-05-12T13:33:00Z | 2026-05-12T13:42:00Z | alice approved plan at 2026-05-12T13:42:00Z |
| 2 | Discovery — one `service-discovery` real-discovery delegation (diagram + AWS + Kubernetes) | done | 2026-05-12T13:42:00Z | 2026-05-12T14:28:00Z | alice at 2026-05-12T14:28:00Z |
| 3 | Discovery snapshot — validate, same-target check, snapshot | done | 2026-05-12T14:28:00Z | 2026-05-12T14:30:00Z | alice at 2026-05-12T14:30:00Z |
| 4 | Runtime profile — `runtime-trace` (its own 7 gates: 1, 1a, 2–6) | done | 2026-05-12T14:30:00Z | 2026-05-12T15:00:00Z | alice at 2026-05-12T15:00:00Z |
| 5 | Interview — emit questionnaire; ingest filled version | done | 2026-05-12T15:00:00Z | 2026-05-12T15:30:00Z | alice at 2026-05-12T15:30:00Z; sections: 11 complete / 0 partial / 0 empty |
| 6 | Readiness scorecard — auto-mark, Step 6 verification batch, attestations | done | 2026-05-12T15:30:00Z | 2026-05-12T15:55:00Z | alice at 2026-05-12T15:55:00Z; verdict: partial |
| 7 | Handoff package assembly | done | 2026-05-12T15:55:00Z | 2026-05-12T16:00:00Z | alice at 2026-05-12T16:00:00Z |

---

## Artifact paths

Package-relative names; the fixture keeps the snapshots under `mock-artifacts/` and `filled-interview.md`.

| Artifact | Package file | Snapshotted at | Notes |
|---|---|---|---|
| service-discovery catalog | service-catalog.md | 2026-05-12T14:30:00Z | copied as-is; `service-discovery-schema: 1`; `Live verification: performed 2026-05-12` |
| runtime-trace profile | runtime-profile.md | 2026-05-12T15:00:00Z | copied as-is; `runtime-profile-schema: 2`; spend = account context |
| Filled interview | interview-questionnaire.md | 2026-05-12T15:30:00Z | snapshot of `filled-interview.md` |
| Readiness scorecard | readiness-scorecard.md | 2026-05-12T15:55:00Z | authored by the skill |
| Open questions | open-questions.md | 2026-05-12T15:55:00Z | authored by the skill |
| Execution plan | execution-plan.md | 2026-05-12T13:42:00Z | Step 6 addendum added at 2026-05-12T15:33:00Z |
| Handoff README | README.md | 2026-05-12T16:00:00Z | authored by the skill |

---

## Same-target checks (run at every snapshot)

Each snapshot is compared with the intake values (service `search-api`, account 123456789012, region eu-west-1) and its age is recorded against the snapshot time. A mismatch stops the run; an age over 30 days, or any artifact reused on resume, triggers the use / verify / re-run offer.

| Artifact | Account | Region | Service | Matches intake | Age at snapshot | Offer |
|---|---|---|---|---|---|---|
| service-catalog.md | 123456789012 | eu-west-1 | search-api (context platform-eks, ns search) | yes | 2 min (generated 14:28Z, snapshotted 14:30Z) | none (< 30 d) |
| runtime-profile.md | 123456789012 | eu-west-1 | search-api | yes | 2 min (generated 14:58Z, snapshotted 15:00Z) | none (< 30 d) |
| catalog vs profile | — | — | — | yes: catalog AWS rows (7) = profile resolved set (7) | — | — |

---

## Step 1.5 probe results (derived facts only — raw command output is never recorded)

| Probe | Command (projected) | Derived fact | Timestamp |
|---|---|---|---|
| identity-probe-result | `aws sts get-caller-identity --profile prod-main --query Account` | caller account = intake account (123456789012): yes | 2026-05-12T13:35:00Z |
| cloudtrail-event-history | `aws cloudtrail lookup-events --max-results 1 --profile prod-main --region eu-west-1 --query 'Events[0].EventTime'` | Event history readable: yes | 2026-05-12T13:36:00Z |
| resource-explorer-index | `aws resource-explorer-2 list-indexes --profile prod-main --region eu-west-1 --query 'Indexes[].{Region:Region,Type:Type}'` | aggregator index in eu-west-1: yes | 2026-05-12T13:37:00Z |

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
3
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
3
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
3
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
3
:
3
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
3
:
3
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
 
i
n
 
e
u
-
w
e
s
t
-
1
 
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
3
:
3
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
 
e
u
-
w
e
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
3
:
4
0
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
3
:
4
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
3
:
4
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
 
1
 
d
i
a
g
r
a
m
 
+
 
l
i
v
e
 
A
W
S
 
A
P
I
s
 
+
 
k
u
b
e
 
c
o
n
t
e
x
t
 
p
l
a
t
f
o
r
m
-
e
k
s
,
 
n
a
m
e
s
p
a
c
e
 
s
e
a
r
c
h
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
2
8
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
s
e
a
r
c
h
-
a
p
i
-
p
r
o
d
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
2
8
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
 
c
l
u
s
t
e
r
 
c
o
n
t
e
x
t
 
p
l
a
t
f
o
r
m
-
e
k
s
;
 
a
g
e
 
2
 
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
0
:
0
0
Z
 
 
O
w
n
e
r
s
h
i
p
 
r
e
c
o
g
n
i
s
e
d
 
f
r
o
m
 
t
h
e
 
c
a
t
a
l
o
g
:
 
5
 
r
o
w
s
 
c
l
o
u
d
f
o
r
m
a
t
i
o
n
 
(
s
e
a
r
c
h
-
d
a
t
a
-
s
t
a
c
k
 
|
 
s
e
a
r
c
h
-
i
a
m
-
s
t
a
c
k
)
,
 
3
 
h
e
l
m
 
s
e
a
r
c
h
-
a
p
i
.
 
R
e
c
o
r
d
e
d
;
 
n
o
 
a
c
t
i
o
n
 
t
a
k
e
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
s
c
o
p
i
n
g
:
 
t
h
e
 
c
a
t
a
l
o
g
 
A
W
S
 
r
e
s
o
u
r
c
e
 
s
e
t
;
 
n
o
 
t
a
g
 
-
>
 
s
p
e
n
d
 
w
i
l
l
 
b
e
 
a
c
c
o
u
n
t
 
c
o
n
t
e
x
t
;
 
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
 
2
 
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
 
(
7
)
 
=
 
c
a
t
a
l
o
g
 
A
W
S
 
r
o
w
s
 
(
7
)
 
-
>
 
O
K
.
 
P
r
o
f
i
l
e
 
r
e
c
o
r
d
s
 
"
E
K
S
 
i
n
-
c
l
u
s
t
e
r
 
w
o
r
k
l
o
a
d
s
 
n
o
t
 
t
r
a
c
e
d
"
 
a
s
 
a
 
g
a
p


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
0
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
 
(
i
n
c
l
.
 
4
b
 
I
a
C
 
&
 
o
w
n
e
r
s
h
i
p
)
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
2
5
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
 
L
e
n
a
 
M
.
 
(
S
e
a
r
c
h
 
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
3
2
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
 
2
 
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
3
3
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
3
5
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
2
 
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
 
4
 
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
3
5
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
2
 
d
e
s
c
r
i
b
e
-
r
e
p
l
i
c
a
t
i
o
n
-
g
r
o
u
p
s
:
 
S
n
a
p
s
h
o
t
R
e
t
e
n
t
i
o
n
L
i
m
i
t
 
7
 
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
3
8
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
 
o
p
e
n
e
d
 
3
 
r
u
n
b
o
o
k
 
l
i
n
k
s
,
 
t
h
e
 
r
o
l
l
b
a
c
k
 
r
u
n
b
o
o
k
 
a
n
d
 
t
h
e
 
p
o
s
t
m
o
r
t
e
m
 
(
i
t
e
m
s
 
1
3
,
 
1
4
,
 
1
7
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
2
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
5
:
4
4
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
5
:
4
6
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
5
:
5
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
 
8
 
◐
,
 
0
 
✗
,
 
0
 
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
 
1
 
?
,
 
1
 
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
 
p
a
r
t
i
a
l


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
5
:
5
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
0
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
0
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
