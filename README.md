# .invariants

A watcher agent that reads a `.invariants` file, fetches data from declared
sources, evaluates each assert, and outputs a structured pass/fail report
with evidence.

The watcher contains no hardcoded org logic. The `.invariants` file is the
program. The watcher is the runtime.

---
## State of the project
This is an early-stage open source project. The signal quality of current watchers is limited. GitHub activity is one narrow proxy for organizational health. The value today is the .invariants primitive itself (the concept of machine-evaluable organizational claims) not the accuracy of any specific score.

However, the design is intentionally open so that organizations can model their own invariants with whatever precision their instrumentation supports.

---
## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env                   # add your GITHUB_TOKEN (no scopes needed for public orgs)
cp .invariants .invariants.yourorg     # edit for your org, then run:
python watcher.py .invariants.yourorg
```

---

## The .invariants file

**`.invariants` in this repo is the canonical example.** Read it before writing your own.

It is not just a config file — it is a structured claim about what must remain
true about your organization. Each assert has:

- `claim` — a plain-English statement of the invariant
- `condition` — a machine-evaluable metric, operator, and threshold
- `evidence_template` — what gets printed when the assert runs
- `why` — the reasoning behind the assert (for you and anyone reading it)

### Tiers

Asserts are annotated with a tier:

| Tier | Meaning |
|------|---------|
| `external` | Fetched automatically from public sources. No org participation needed. |
| `internal` | Requires your org to push verified signals. Not yet automated. |
| `manual` | Requires human input. Future tier. |

Start with `external` asserts. Leave `internal` ones commented — they are your
instrumentation roadmap.

### UNKNOWN is not failure

If a metric is not available (watcher not yet implemented, source unreachable),
the assert returns `UNKNOWN`. `UNKNOWN` scores 1 point out of 2. It means
*unproven*, not *failing*.

The commented-out asserts in `.invariants` show you what to build toward.
UNKNOWN is the honest state for asserts you cannot yet support.

### Why the example matters

The `.invariants` file shipped in this repo is the most complete description of
what the system *can* check. It includes asserts across:

- Founding team activity
- Engineering velocity
- Learning signals (AI tooling, open source health)
- Financial health proxies *(internal push, commented)*
- People health *(partial external, partial internal)*
- Delivery integrity
- Identity coherence

Do not strip the commented asserts out of your org's file. They are the
roadmap. Every assert you eventually uncomment and prove is a day of verified
history added to your ledger.

---

## Configuration reference

```yaml
version: 1.0
entity: "Your Company Name"     # human-readable name, used in report header
org: "your-github-org"          # GitHub org slug
since: "YYYY-MM-DD"             # proof history start date — set once, never change

watchers:
  - github_activity             # currently the only implemented watcher

suite: engineering_led_v1       # built-in assert bundle (suites/)

sample_size: 10                 # repos sampled for author/PR metrics
                                # defaults to 10 if org < 50 repos, else 5

founding_team_handles:          # GitHub handles of technical founders
  - handle1
  - handle2

custom_asserts: [...]           # org-specific asserts (see .invariants for examples)

disclosure:
  default: private
  on_request: selective
  verified_claims: off          # set to on_chain when proof layer is ready
  chain: starknet

schedule: daily
alert_on_fail: true
```

---

## Scoring

| Result | Points |
|--------|--------|
| PASS | 2 |
| UNKNOWN | 1 |
| FAIL | 0 |

Score = (earned / max) × 100. Reported at the top of every run.

---

## Project structure

```
.
  watcher.py                    # entry point
  report.py                     # output formatter and scorer
  fetchers/
    github.py                   # github_activity watcher implementation
  suites/
    engineering_led_v1.yml      # built-in assert bundle
  .invariants                   # the canonical example file — read this
  .env.example                  # copy to .env and add GITHUB_TOKEN
  requirements.txt
```

---

## What this does not do yet

- zkproof generation
- on-chain storage
- multi-watcher support beyond `github_activity`
- historical result storage

These are explicitly out of scope for the current version.
