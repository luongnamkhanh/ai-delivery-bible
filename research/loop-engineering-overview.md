# Loop Engineering — The Full Picture

A self-contained synthesis material: what loop engineering is, how the loop actually works,
how to build one, and how it connects to the research. Personal research / side-project reference.

Companion files in this folder:
- `loop-engineering-notes.md` — condensed takeaways from the IEEE working note
- `2511.00592-summary.md` + PDF — the ComPilot paper (empirical grounding)
- `Loop-Engineering-IEEE.pdf` — the working-note source

---

## 0. First, disambiguate the word "loop"

Two unrelated concepts share the word. Don't confuse them.

- **Compiler loop optimization** — "loop" = a `for`/`while` loop in code; the craft of reshaping
  those loops (tiling, fusion, parallelization) to run faster on hardware. *(This is the ComPilot
  paper's domain.)*
- **Loop engineering (this doc)** — "loop" = an AI agent's **control loop**; designing the
  autonomous *act → observe → decide → repeat* system that drives a coding agent.

They are homonyms — but they intersect: ComPilot is a *loop-engineering system* (sense 2) whose job
happens to be *loop optimization* (sense 1). That intersection is why it's such useful evidence (§9).

---

## 1. The one-sentence definition

> **Loop engineering is replacing yourself as the person who prompts the agent. You design the
> system that does it instead.** — Addy Osmani, June 2026

You stop feeding the agent line by line. You build a system that decides *what* to prompt, *when*,
and *whether the result is acceptable* — then runs itself.

### Origin & why it's trending (mid-2026)
The term surfaced in one week of June 2026, catalyzed by three people saying the same thing:
- **Boris Cherny** (Claude Code, Anthropic): *"I don't prompt Claude anymore. I have loops running…
  My job is to write loops."*
- **Peter Steinberger**: *"You shouldn't be prompting coding agents anymore. You should be designing
  loops that prompt your agents."* (~5M views in 24h)
- **Addy Osmani** named the practice and gave it an anatomy.

The deeper driver: by 2026 agents can run autonomously for *hours*, so the human typing prompts
became the bottleneck. The lineage isn't new — ReAct (2022) → AutoGPT (2023) → one-line "Ralph"
bash loops (2025) → productized `/loop` and `/goal` commands (2026). What changed is the
**abstraction level** you operate at.

---

## 2. Where it sits: the four-layer stack

Each layer minds something larger than the one below it.

| Layer | Optimizes | Core question |
|---|---|---|
| Prompt eng. | The words in one instruction | What should I tell the model? |
| Context eng. | Everything in the window right now | What to retrieve / summarize / clear? |
| Harness eng. | One agent run (tools, actions, "done") | Which tools, what counts as done? |
| **Loop eng.** | Scheduling *on* the harness | How to make it run itself over and over? |

Three verbs separate a **loop** from a **harness**: it **runs on a timer**, it **spawns helpers**,
and it **feeds itself** (this turn's output becomes next turn's input, via external state).

---

## 3. How the loop actually works — one turn

A turn is concrete: it finds work, hands it to an agent, verifies the result, saves state, then
schedules the next round. Five moves, in order:

```
        ┌──────────────────────────────────────────────────────┐
        │                                                        │
        ▼                                                        │
   ① DISCOVERY ──▶ ② HANDOFF ──▶ ③ VERIFICATION ──▶ ④ PERSISTENCE ──▶ ⑤ SCHEDULING
   find the work   isolated      a SEPARATE agent    write state       trigger next
   on its own      worktree      that can say "NO"   outside the chat   round on a timer
                                  (the hard part)     (memory on disk)
```

| Move | What it does | Realized by |
|---|---|---|
| ① Discovery | Find this turn's work itself (read CI, issues, commits) | a **Skill** (`SKILL.md`) |
| ② Handoff | Move the task to an isolated agent | a **Worktree** (git) |
| ③ Verification | A different agent judges "does it *run* right" | **Sub-agents** (maker ≠ checker) |
| ④ Persistence | Record progress where it survives | **Memory** (markdown / board on disk) |
| ⑤ Scheduling | Make one run into a loop | **Automations** (cron / trigger) + **Connectors** (MCP) |

**Key reframe:** the loop's memory cannot live in the context window (it's flushed every round).
*The agent forgets; the repo doesn't.* State must be on disk.

---

## 4. The engine: Generator / Evaluator separation

This is the heart of why loops work — and the part most people get wrong.

- An agent grading its **own** output praises it. It sees the chain of self-persuasion that produced
  the code, not the code's real quality. This is **structural**, not a wording problem.
- The fix is not a better self-critique prompt. It's a **separate evaluator** — ideally a
  **different model** — instructed to **assume the output is BROKEN until proven otherwise**.
  (Borrowed from GANs: one network generates, one finds faults.)
- **The evaluator must ACT, not READ.** Wire it to tools so it judges *"does it run right"* — execute
  tests, click the button, screenshot, inspect — not *"does it look right."*
- In Claude Code this is the `/goal` stop condition: a **fresh small model** checks the condition
  after each turn. Maker ≠ checker — the centuries-old four-eyes principle, applied to the
  loop's "done."

> **A loop without a real check is just an agent nodding at itself.**

---

## 5. The central intuition (worth memorizing)

> **The cost of a mistake scales with the number of turns it survives before someone catches it.**

A loop is, by construction, a machine for **maximizing turns**. So every safety mechanism — the
evaluator, the human checkpoint, the budget cap — exists for *one* purpose: **shorten the distance
between a mistake and its discovery.** Same bug caught at the prompt layer = one bad exchange; left to
the loop layer = written into the state file as fact and built upon for days.

---

## 6. How loops fail — five anti-patterns (each = one move skipped)

| Skipped move | Anti-pattern | Symptom |
|---|---|---|
| Verification | **Nodding loop** (most common) | self-approved output at machine speed |
| Persistence | **Amnesiac loop** | no cumulative progress; redoes/conflicts each run |
| Discovery | **Blind loop** | human still decides what to work on every morning |
| Handoff | **Tangled loop** | parallel agents collide editing the same files |
| Scheduling | **Manual loop** | not a loop — a script you rerun by hand until you forget |

**The trap:** hasty builders install only the two moves that produce *visible output*
(discovery + handoff) and skip the three that produce *safety* (verification, persistence,
scheduling) → "a loop nobody watches and nobody can stop."

---

## 7. The four silent costs (a reinforcing cycle)

```
   verification debt ──▶ comprehension rot ──▶ cognitive surrender ──▶ token blowout ──┐
          ▲                                                                            │
          └──────────────────────── more unverified output ◀──────────────────────────┘
```

- **Verification debt** — unverified output piling up between "runs" and "right."
- **Comprehension rot** — the faster it ships code you didn't write, the wider the gap between what
  exists and what you understand.
- **Cognitive surrender** — you stop having an opinion and take whatever it returns.
- **Token blowout** — an idle bug burns compute all night; the only cost that hits the bill directly.

*Example:* 20 green-test PRs overnight; 3 hide bugs the tests don't cover. Merge all 20 unread → your
mental map lags 20 changes, you've stopped reading, it ran all night — one failure wearing four faces.

---

## 8. The discipline: how to operate a loop safely

Three standing practices (set up **before** the first unattended run):

1. **Read a sample, always.** Not everything — a regular, genuinely-examined sample, forcing yourself
   to explain each change. Can't explain it = your mental map has fallen behind. *(vs comprehension rot)*
2. **Cap before you ship.** Per-run budget + daily budget + max-retry. Circuit breakers that turn
   open-ended risk into bounded risk. *(vs token blowout)*
3. **Keep one door open.** At least one human checkpoint, built in structurally. "The day it's
   removed is the day comprehension rot begins in earnest." *(vs cognitive surrender)*

**Reliability comes from constraints, not model size** (Stripe's 1,300-PRs/week pipeline): interleave
**deterministic hard-coded gates** (context assembly, linter, commit) with LLM steps. Anything
deterministic should be kept *out* of the probabilistic model.

**Scheduling — local vs cloud are different capabilities:** local `/loop` (machine must stay on,
~1-min interval, sees local files) = "run while I'm here"; cloud/CI trigger (machine off, ~1-hr
interval) = "run while I'm not." Mature loops use both.

---

## 9. Build your first loop — start SMALL

Start with one finding handled end-to-end; widen only after the checks catch real mistakes. **Add
parallelism last.** A real loop needs all six organs:

```yaml
# ⑤ SCHEDULING — a real trigger
on:
  schedule:
    - cron: '0 6 * * *'              # 06:00 daily

# ① DISCOVERY — a skill, not a wall of text
run: claude --skill morning-triage    # reads CI fails, new issues, recent commits

# ④ PERSISTENCE — skill writes ./state/triage.md and commits it back

# ② HANDOFF — one worktree per finding
for finding in $(parse ./state/triage.md); do
  claude --worktree "fix/$finding" \
         --goal "tests pass and lint is clean" \    # ③ VERIFICATION: fresh model judges
         "draft a fix for $finding"
done

# ⑥ HUMAN REVIEW — the open door: open PRs, never auto-merge; uncertain → ./inbox/
```

**First-loop checklist:** Discovery source · State file · Evaluator that can say "no" · Isolation
(worktree per agent) · Token cap · Human-review door. *First two decide whether it runs; last four
decide whether it gets into trouble.*

---

## 10. Empirical grounding — the ComPilot paper (arXiv 2511.00592)

ComPilot is a real, measured loop-engineering system: the LLM proposes loop-optimization schedules
(**generator**); the Tiramisu compiler checks legality and runs the code (**evaluator that ACTS**,
defaulting to reject illegal schedules). Results that validate this whole playbook:

- **Feedback loop beats one-shot:** removing the feedback loop dropped performance **~23–40%** (the
  measured case for §3 and against the "Blind/Nodding loop").
- **Self-grading is dangerous (RQ7):** when the LLM was allowed to **self-certify** its own generated
  code, **17.6% of "successful" outputs were actually wrong**. Hard-numbers proof of §4 — *an agent
  grading its own work praises it.*
- **Diminishing returns** in iterations/runs — match the "start small, cap it" discipline of §8.

One document asserts the principle; the other measures the cost of ignoring it.

---

## 11. The takeaway in four lines

1. The hard part is the **"no"** — install a separate, skeptical, *acting* evaluator (different model).
2. **Cap the budget and keep one human door open** before the first unattended run.
3. **Start small; add parallelism last.**
4. The loop is a **faithful multiplication sign** — it amplifies whatever judgment the builder brings.
   So *stay the engineer*, not the one who presses go.

---

## Sources
- Addy Osmani, *Loop Engineering* (addyosmani.com / Substack, Jun 2026)
- *Loop Engineering: The Anthropic Playbook…* — HuaShu working note (independent synthesis; **not**
  an official Anthropic paper)
- Prithvi Rajasekaran (Anthropic), generator/evaluator pattern · Steve Kaliski (Stripe), "Minions"
- Merouani, Kara Bernou, Baghdadi, *Agentic Auto-Scheduling* (arXiv 2511.00592, PACT 2025)
- GitHub ecosystem: `cobusgreyling/loop-engineering`, `valkor-ai/loom`, `agentic-in/inferoa`
