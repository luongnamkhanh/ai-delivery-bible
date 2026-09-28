# Loop Engineering — High-Signal Notes

Personal research notes. Source: `Loop-Engineering-IEEE.pdf` (an independent "working note" by
*HuaShu* reformatting the *Orange Book* guide, built on **Addy Osmani's** framework, with technical
findings from **Prithvi Rajasekaran / Anthropic** and the enterprise case from **Steve Kaliski /
Stripe**). Note: *not* an official Anthropic publication despite the title — treat as a strong
secondary source.

---

## TL;DR

**Loop engineering = replacing yourself as the person who prompts the agent; you design the system
that prompts it instead.** It's the 4th layer above prompt/context/harness engineering. The hard
part isn't getting the agent to *run* — it's putting something in the loop that can say **"no"**.
Generation is now nearly free; **judgment is the scarce resource**, and the loop amplifies whatever
judgment (or laziness) the builder brings.

---

## 1. The four-layer stack

Each layer "minds" something larger than the one below it.

| Layer | What it optimizes | Core question |
|---|---|---|
| Prompt eng. | The words in one instruction | What should I tell the model? |
| Context eng. | Everything in the window right now | What to retrieve / summarize / clear out? |
| Harness eng. | Arming a single agent run (tools, actions, "done") | Which tools, which actions, what counts as done? |
| **Loop eng.** | Scheduling *on* the harness | How to make it run itself over and over? |

Three verbs separate a loop from a harness: it **runs on a timer**, it **spawns helpers**, and it
**feeds itself** (this turn's output becomes next turn's input via external state).

## 2. The central intuition

> **The cost of a mistake scales with the number of turns it survives before someone catches it.**

A loop is, by construction, a machine for maximizing turns. Therefore everything else —
the evaluator, the human checkpoint, the budget cap — exists for one job: **shorten the distance
between a mistake and its discovery.** Same bug at the prompt layer = caught in one exchange; at the
loop layer = written into the state file as fact and built upon for days.

## 3. The five moves of one turn (and the five ways it fails)

Drop any one move and the loop won't turn — or turns in place.

| Move | What it does | Skip it → anti-pattern |
|---|---|---|
| **Discovery** | Find this turn's work on its own | **Blind loop** — human still decides what to work on |
| **Handoff** | Hand the task to an isolated agent | **Tangled loop** — parallel agents collide in one dir |
| **Verification** | Swap in another agent to say "no" | **Nodding loop** — self-approved output at machine speed (most common) |
| **Persistence** | Write state outside the conversation | **Amnesiac loop** — no cumulative progress |
| **Scheduling** | Make it run again next round | **Manual loop** — it's a script you rerun by hand |

**The trap:** hasty builders install only the two moves that produce *visible output* (discovery +
handoff) and skip the three that produce *safety* (verification, persistence, scheduling) → "a loop
nobody watches and nobody can stop."

## 4. Generator / Evaluator separation (the deepest point)

- An agent grading its own work **praises it** — it sees the chain of self-persuasion that led there,
  not the result. This is structural, not a wording problem.
- Fix: a **separate evaluator**, ideally a **different model**, told to **assume the code is BROKEN
  until proven otherwise**. (Borrowed from GANs: one network writes, one finds faults.)
- Tuning a skeptical standalone judge is far more tractable than making a generator self-critical.
- **The evaluator should ACT, not READ.** Hook it to tools (e.g. Playwright MCP) so it judges
  *"does it run right"* — click the button, screenshot, inspect the DOM — not *"does it look right."*
- In Claude Code this is the `/goal` stop condition: a **fresh small model** checks the condition
  after each turn. Maker ≠ checker (the old four-eyes principle, applied to the stop condition).

## 5. The four silent costs (a reinforcing cycle, not a checklist)

```
verification debt → comprehension rot → cognitive surrender → token blowout ─┐
        ^                                                                     │
        └─────────────────────── (more unverified output) ───────────────────┘
```

- **Verification debt** — unverified output piling up in the gap between "runs" and "right."
- **Comprehension rot** — the faster it ships code you didn't write, the wider the gap between what
  exists and what you understand.
- **Cognitive surrender** — you stop having an opinion and just take what it hands back.
- **Token blowout** — an idle bug burns compute all night; the only cost that hits the bill directly.

*Worked example:* 20 green-test PRs overnight, 3 hide subtle bugs the tests don't cover. Merge all 20
unread → your mental map lags 20 changes, you've stopped reading, it ran all night → all four costs,
one failure wearing four faces.

## 6. Operational discipline (three standing practices)

1. **Read a sample, always.** Not everything (defeats the purpose) — a regular, genuinely-examined
   sample, and force yourself to explain each change. Inability to explain = your mental map has
   fallen behind. Defense against comprehension rot.
2. **Cap before you ship.** Set per-run budget, daily budget, and max-retry *before* the first
   unattended run. These are circuit breakers that convert open-ended risk into bounded risk.
3. **Keep one door open.** Build at least one human checkpoint into the loop — structural, not
   attitudinal. "The day it's removed is the day comprehension rot begins in earnest." Defense
   against cognitive surrender.

## 7. Reliability comes from constraints, not model size (Stripe Minions)

1,300 machine-written PRs/week. The pipeline interleaves **deterministic hard-coded gates** with LLM
steps:

```
human trigger (Slack emoji) → deterministic orchestrator assembles context (NOT the LLM)
  → LLM writes code → hard-coded linter gate → LLM fixes → hard-coded git commit → human review
```

Principle: **anything deterministic should be hard-coded and kept *out* of the probabilistic model.**
Reliability is in the quality of the constraints, not the size of the model.

## 8. Scheduling: local vs cloud (they're different capabilities)

| | Local `/loop` | Cloud / CI trigger |
|---|---|---|
| Machine on? | Yes (must stay awake) | No |
| Min interval | ~1 min | ~1 hour |
| Sees local files? | Yes | No |
| Real autonomy | "run a few rounds while I'm here" | "run even when I'm not" |

Don't conflate *local rerun* with *running while you sleep*. Mature loops use both: local for the
tight inner checks, cloud for the overnight sweep.

## 9. Build your first loop SMALL — the minimal complete recipe

Start with one finding handled end-to-end; widen only after the checks have caught real mistakes.
Add **parallelism last**. A real loop needs all six elements:

```yaml
# 1. SCHEDULING — a real trigger (.github/workflows/triage.yml)
on:
  schedule:
    - cron: '0 6 * * *'        # 06:00 daily, cloud

# 2. DISCOVERY — a skill, not a wall of text
run: claude --skill morning-triage

# 3. PERSISTENCE — the skill writes ./state/triage.md and commits it back to the repo

# 4. HANDOFF — one worktree per finding
for finding in $(parse ./state/triage.md); do
  claude --worktree "fix/$finding" --goal "tests pass and lint is clean" "draft a fix for $finding"
done

# 5. VERIFICATION — /goal's stop check runs after each turn; a second reviewer agent picks holes

# 6. HUMAN REVIEW — the open door: PRs are opened, never auto-merged; anything uncertain → ./inbox/
```

First-loop checklist: **Discovery source / State file / Evaluator that can say "no" / Isolation
(worktree per agent) / Token cap / Human review door.** First two decide whether it *runs*; last four
decide whether it gets into *trouble*.

## 10. Cross-link: empirical backing from the ComPilot paper

The ComPilot paper (`2511.00592`) is a textbook generator/evaluator loop: LLM = generator, compiler =
separate evaluator that **acts** (runs code, measures speed) and **defaults to reject** illegal
schedules. Its **RQ7** result is hard-numbers proof of takeaway #4: when the LLM was allowed to
**self-certify** its own generated code, **17.6% of "successful" outputs were actually wrong** — i.e.
"an agent grading its own work praises it." One paper asserts the principle; the other measures the
cost of violating it.

---

## What to actually remember

1. The hard part is the **"no"** — install a separate, skeptical, *acting* evaluator (different model).
2. **Cap the budget and keep one human door open** before the first unattended run.
3. **Start small**, add parallelism last.
4. The loop multiplies the builder's judgment — so **stay the engineer**, not the one who presses go.
