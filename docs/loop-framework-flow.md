# Loop Framework & Flow — Agentic Data-Platform Build (Slack-native)

The working flow (WoW) for building the hybrid Data Platform via loop engineering, with **Slack as
the control plane**. This is the *process* layer — how a request moves through the loop — independent
of the data-stack choices (those live in a separate architecture doc). Grounded in
`../research/loop-engineering-overview.md`.

> **Design principle:** the loop generates freely, but **nothing high-impact happens without a
> deterministic gate and a human door.** The model proposes; gates and you dispose.
>
> **Slack rule:** Slack is the **cockpit** (commands, status, approvals) — **not** the data plane.
> Control flows through Slack; data and real logs stay on-prem.

> **v2 — 2026-09-28. What changed since 02/07 and why.** This design was run for three months on a real
> platform (annamgt: Kafka/Flink/Doris on K8s, GitOps). Two things did not survive contact: prose state
> (`state/*.md`, tickets) drifted and got trusted stale; and gates that were not proven to run were not
> gates. What replaced them is in **§4.1** (contract layer: `rules` / `runtime` / `ratchet` / spike / map)
> and **§4.2** (app projects: OpenAPI as the FE↔BE contract, MCP as a generated + curated adapter for agent
> clients only). §5 adds autonomy-by-role; §11 records design-vs-as-run with evidence. The Slack sections
> (§7) are kept as the multi-front option; the daily loop ran in a Claude Code session + git MRs.

---

## 1. The actors

| Actor | Role in loop terms | Model tier | Slack identity | Can it touch prod? |
|---|---|---|---|---|
| **You** | Orchestrator-of-record + the human door | — | your user | Yes (approval only) |
| **Primary Agent** | Orchestrator: decompose, dispatch, synthesize | Opus (judgment) | 🟦 the bot | No |
| **Code Agent** | Worker / *generator* — app + ETL code | Cheaper (Haiku) | 🟩 bot (Code) | No |
| **Infra Agent** | Worker / *generator* — Helm, K8s, Terraform | Cheaper (Haiku) | 🟧 bot (Infra) | Only via gated apply |
| **Reviewer Agent** | *Evaluator* — the "say no" | **Different model**, "assume broken" | 🟥 bot (Reviewer) | No (judges by acting) |
| **Deterministic Gates** | NOT an agent — hard-coded checks | n/a (code) | 🚦 CI posts results | They are the safety rail |

The Code/Infra/Reviewer split is the **generator/evaluator** pattern: the reviewer must be a
*different* agent (ideally a different model) and must **verify by acting** (run the lint, the
dry-run, query the catalog) — not by re-reading the code that just persuaded itself it was right.

---

## 2. The flow of one request (one loop turn)

Everything below happens **inside one Slack thread** (`thread_ts` = the loop instance ID).

```
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │  ① TRIGGER ── @bot mention / slash cmd / thread reply ──────────────────────  │ Discovery
 │     "Deploy Helm chart for the catalog"                                       │
 │                              ▼                                                │
 │  ② DECOMPOSE  — Primary Agent splits into sub-tasks, assigns workers ───────  │ Handoff
 │     posts 🧩 plan in thread · each worker gets its OWN git worktree           │
 │                              ▼                                                │
 │  ③ GENERATE   — Code / Infra Agents produce artifacts, commit to branch ────  │ (generator)
 │     post 🔧 progress in thread                                                │
 │                              ▼                                                │
 │  ④ DETERMINISTIC GATES  (no LLM, run in CI)  ──────────────────────────────  │ ┐
 │     helm lint → kubeconform → conftest/OPA → tests → kubectl --dry-run=server │ │ Verification
 │     CI posts 🚦 PASS/FAIL to thread · fail → back to ③ (bounded retries)      │ │  (machine)
 │                              ▼ pass                                           │ │
 │  ⑤ REVIEWER AGENT  (the "say no")  ────────────────────────────────────────  │ │ Verification
 │     different model · assume BROKEN · ACTS · posts 🔎 PASS / REJECT+why       │ ┘  (judgment)
 │                              ▼                                                │
 │  ⑥ PERSIST   — open PR + write state/<feature>.md to repo ──────────────────  │ Persistence
 │     post 📦 PR link to thread (state lives on DISK + repo, not the thread)    │  (memory)
 │                              ▼                                                │
 │  ⑦ STOP CHECK (/goal, fresh model)  ───────────────────────────────────────  │ Scheduling /
 │     gates ✓ AND reviewer ✓ AND acceptance criteria ✓ ?                        │  stop
 │       NO  → next turn (back to ③), within retry + budget caps                 │
 │       YES → ⑧                                                                 │
 │                              ▼                                                │
 │  ⑧ HUMAN DOOR 🚪  — Block Kit buttons in thread: [Approve merge] [Apply]      │ the open door
 │     [Reject].  Click recorded (who+when) = four-eyes audit trail.             │
 │     NEVER auto-merge · NEVER auto-apply prod.                                 │
 └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. The five moves → this project

| Move | In this loop | Realized by |
|---|---|---|
| **Discovery** | `@bot` mention / `/loop` (MVP) → later a triage skill | Slack event / `SKILL.md` |
| **Handoff** | Primary Agent assigns workers | Task tool / Agent Teams + one **worktree per worker** |
| **Verification** | Gates (machine) + Reviewer (judgment) | Conftest/kubeconform/tests + a different-model reviewer that acts |
| **Persistence** | PR + `state/*.md` committed to repo + thread↔run registry | git, not the Slack thread alone |
| **Scheduling** | Slack trigger now; cron/CI later | headless run + `/goal` stop condition |

---

## 4. Deterministic vs probabilistic (the reliability rule)

Reliability comes from constraints, not model size. Keep anything that *can* be hard-coded out of
the model.

- **Probabilistic (agents decide):** decomposition, writing code/Helm/manifests, reviewing &
  reasoning, summarizing for Slack.
- **Deterministic (hard-coded, never trusted to the model):** `helm lint`, schema validation
  (`kubeconform`), policy (OPA/Conftest), test execution, `kubectl --dry-run=server`, the
  merge/apply step itself (a CI action triggered by the Slack button), and the data-residency check.

### 4.1 Contract layer — the loop's memory is machine-checkable files (v2, proven on annamgt 08→09/2026)

The 07/2026 design put memory in `state/*.md` + tickets. Three months of running the loop showed prose
state drifts within weeks, and a compacted agent (or a new human) trusts stale prose. What held:
**facts live in files a machine can check; decisions live in an append-only dated ledger; prose is a
snapshot with a banner.** Per repo:

| File | Answers | Checked by |
|---|---|---|
| `contracts/rules.yml` | what is invariant — rule id + why + lineage to the incident | `ci/check_*.py`, exit 1 on every MR (step ④) |
| `contracts/runtime.yml` | is the live system still conforming | `ci/check_runtime.py` — `cmd` + `expect_*`; a check without `cmd` is reported SKIP, never silent |
| `contracts/ratchet.yml` | why we decided X, with evidence; what is deliberately on hold | humans + reviewer; append-only; OPEN entries carry a reopen condition |
| `docs/spikes/YYYY-MM-DD-*.md` | is this assumption true | throwaway experiment, timeboxed, one question, evidence captured, cleanup recorded |
| `CLAUDE.md` / `AGENTS.md` | what to trust, known drift in docs, house rules | read before any doc; ≤ 15 lines |

How it plugs into the flow above: **④ gates = the evaluators** (the OPA/kubeconform line becomes
`check_infra.py` on rendered charts, `check_contracts.py` on manifests, `check_doris.py` on values);
**⑤ reviewer or a spike catches something the rules missed → one ratchet entry + one new rule** (the
metric is catch-outside-rule → 0); **⑥ persist = ratchet, not the chat**; **⑦ stop check reads ratchet
status**; **⑧ door = show the state-changing command before running it**. Two loop rules bought with
incidents, not theory: **verify state after every merge/PUT** (an MR reported "merged" that never landed,
26/08) and **one variable per change** (DB upgrade ≠ operator upgrade, ratchet data #1). Write-up with
dated quotes: `../case-studies/annamgt-2026.md`.

### 4.2 App projects: OpenAPI is the FE↔BE contract, MCP is the agent↔BE adapter (v2, 2026-09)

Splitting FE/BE "via OpenAPI/MCP" is neither a framework nor new. What is current in 2026 is
**spec-driven**: the spec is a gate the loop runs, not a document (Thoughtworks' ladder: spec-first →
spec-anchored → spec-as-source; aim for the second rung, where CI fails on drift). Layering that
survives an AI-built codebase:

```
  Web / mobile FE ──HTTP──► OpenAPI  (build-time contract, the single source of truth)
  Agent client    ──MCP───► MCP server = thin adapter GENERATED from the same OpenAPI, then CURATED
                                 │            (5–10 intent-shaped tools, not 1 tool per endpoint)
                                 ▼
                    shared, protocol-neutral operations layer  →  business logic lives here once
```

Deterministic gates for this layer (all step ④, no LLM): spec lint · **breaking-change diff against
main** (a break opens the human door, §8.2) · contract tests (implementation vs spec, and mock vs spec so
the FE mock cannot drift) · generated clients/mocks regenerated in CI, never hand-edited · MCP tool
input schema = the OpenAPI schema, validated at the gateway before any call reaches the backend.

Rules — each is a `rules.yml` line, not a guideline:
- **No MCP for a single non-agent consumer.** The web FE talks REST. MCP exists only when an LLM client
  is the caller; with one consumer it is a liability.
- **Generate, then prune.** Teams cut 60–93% of auto-generated tools before agents behaved reliably; a
  200-endpoint API is not a 200-tool server. Prefer workflow-shaped tools, or dynamic discovery
  (search catalog → fetch schema → invoke) when the surface is large.
- **Descriptions are rewritten for agents** (when to use, what the result means, edge cases). AutoMCP
  measured 76.5% raw call success → 99.9% after ~19 lines of spec edits per API.
- **Identity passes through.** MCP ships no auth/audit; the backend must see the end user, not the MCP
  server's service account (OAuth pass-through or per-user enforcement inside the server + gateway
  audit). Roles that exist in the data layer (e.g. `report_reader` vs `ops_monitor`) must survive the hop.
- **Spec change = interface change** → ratchet entry + door, exactly like a schema migration.

Sources: arXiv 2602.00180 (spec-driven development), Specmatic MCP guardrails for coding agents, WorkOS
"MCP vs REST", Speakeasy / Neon / Xata on OpenAPI→MCP generation, arXiv 2603.07473 (caller-identity
confusion in MCP systems). Spec revision 2026-07-28 made MCP stateless; the "stateful" objection is dated.

---

## 5. Autonomy ladder — start small, widen only after gates catch real mistakes

| Level | What runs unattended | Human gate (in Slack) | Use when |
|---|---|---|---|
| **L0** | nothing — you approve each handoff | every step | first week, learning the loop |
| **L1** ⭐ | generate + gates + reviewer | PR **merge** + **cluster apply** | **MVP default** |
| **L2** | + auto-merge to **dev/non-prod** namespace | prod apply only | once gates proven on 20–30 tasks |
| **L3** | + scheduled discovery opens its own work | prod apply only | mature, observable loop |
| **never** | autonomous **prod** apply | — | banking residency + blast radius |

**Autonomy by role, not only by level (v2).** The levels gate *steps*; what was actually exercised on
annamgt, and what the 09/2026 agent-host plan encodes, gates *roles*:

| Role | Autonomy | Why it is safe |
|---|---|---|
| Spike agent (local, throwaway) | near-full | scratchpad + docker, `down -v` after; output is evidence, not code on main |
| Test / gate agent | full | deterministic; failing is the point |
| Builder (code in repo / worktree) | full inside git, self-merge when delegated | undo is `git`; the MR is the boundary; verify state after merge |
| Prod / deploy / sudo / credential | human door; command shown first | not undoable; residency + blast radius |

---

## 6. Stop & failure semantics (so the loop can't spin or run away)

- **Bounded retries:** stop after N failed gate→fix cycles (e.g. 3) → escalate to human in Slack.
- **Budget caps:** per-run + daily token cap + max-retry, set **before** the first unattended run.
- **Uncertain → halt and ask** (post to thread), never "act anyway." Define "uncertain" up front.
- **Recursion guard:** restrict which subagents the orchestrator may spawn (`Agent(code, infra,
  reviewer)`); no sub-sub-agent fan-out without a hard cap.
- **Log at the point of failure**; post a short note to the thread, attach the full log as a file.

---

## 7. Slack integration — making the loop Slack-native

### 7.1 Two ways to put agents in Slack

| | **Option A — Claude in Slack (official)** | **Option B — Custom bot (Agent SDK + Bolt + MCP)** ⭐ |
|---|---|---|
| How | `@Claude` mention in a channel; it runs and replies | Your service runs the orchestrator + workers, posts as the bot |
| Multi-agent loop | limited (one agent per mention) | full (Primary + workers + reviewer in one thread) |
| Approval buttons | no | yes (Block Kit interactive) |
| Setup effort | minutes | a small service (container on your K8s) |
| Use for | L0 / quick experiments | **the real loop (L1+)** |

Recommendation: prototype with **A**, build the loop on **B**. Option B is a Slack app driving the
**Claude Agent SDK** (same agent loop / subagents as Claude Code) with **MCP servers** for K8s,
Helm, AWS, MinIO, OpenMetadata, and GitHub. Run it as a container on the on-prem cluster.

### 7.2 Slack app setup (Option B)

- **Socket Mode** (the bot opens an *outbound* WebSocket to Slack) → **no inbound public endpoint
  needed**, firewall- and on-prem-friendly. Preferred over Events-API webhooks here.
- **Bot scopes:** `app_mentions:read`, `chat:write`, `channels:history`, `groups:history`,
  `reactions:read`, `reactions:write`, `files:write`, `commands` (optional), `users:read`.
- **Event subscriptions:** `app_mention` (trigger) + `message.channels` & `message.groups` (catch
  follow-up replies inside an active thread). **Filter out the bot's own messages** (check `bot_id`)
  or the loop will feed itself. **Dedupe by `event_id`** — Slack *retries* delivery.
- **Optional slash command:** `/loop deploy <feature>` for clean triggers.
- **Identity model:** start with a **shared bot identity** (fine for this internal tooling). Only
  move to per-user OAuth if agents must respect each person's individual Slack access.

### 7.3 Thread = loop instance (the key design decision)

`thread_ts` is the loop's primary key. Keep a small **registry**:
`thread_ts → { branch, worktree, state_file, status, budget_spent }`. Because subagents have **no
cross-session memory**, this registry + `state/*.md` *is* the loop's memory — the Slack thread is the
view, not the source of truth. *(v2: `state/*.md` prose is a dated snapshot only; the durable memory is
the repo's `contracts/{rules,runtime,ratchet}.yml` + the `CLAUDE.md` map — §4.1.)*

### 7.4 Step → Slack mapping

| Step | Slack event / action | Who posts | Message |
|---|---|---|---|
| ① Trigger | `app_mention` / `/loop` / thread reply | you | 🎯 request |
| ② Decompose | `chat.postMessage` (thread) | 🟦 Primary | 🧩 plan + worker assignment |
| ③ Generate | threaded updates | 🟩/🟧 workers | 🔧 branch, artifact, what changed |
| ④ Gates | CI → incoming webhook to thread | 🚦 CI | PASS/FAIL per check |
| ⑤ Review | `chat.postMessage` (thread) | 🟥 Reviewer | 🔎 PASS / REJECT + reasons |
| ⑥ Persist | `chat.postMessage` (thread) | 🟦 Primary | 📦 PR link |
| ⑦ Stop check | (internal) | — | — |
| ⑧ Human door | **Block Kit buttons** + `block_actions` handler | 🟦 Primary → you | ⏸️ [Approve merge] [Apply] [Reject] |
| done/halt | `chat.postMessage` + ✅/❌ reaction | 🟦 Primary | final state → `state/*.md` |

### 7.5 The human door = Block Kit buttons (four-eyes in Slack)

At step ⑧ the bot posts an interactive block:

```json
{ "blocks": [
  { "type": "section", "text": { "type": "mrkdwn",
      "text": "*PR #42* passed gates + reviewer. Apply to *dev*?" } },
  { "type": "actions", "elements": [
      { "type": "button", "style": "primary", "text": {"type":"plain_text","text":"Approve merge"},
        "action_id": "approve_merge", "value": "pr-42" },
      { "type": "button", "text": {"type":"plain_text","text":"Apply to cluster"},
        "action_id": "apply_cluster", "value": "pr-42:dev" },
      { "type": "button", "style": "danger", "text": {"type":"plain_text","text":"Reject"},
        "action_id": "reject", "value": "pr-42" } ] } ] }
```

The `block_actions` handler runs the **deterministic** CI action (merge / `helm upgrade --install`)
— never the LLM. It records **who clicked and when** → a maker/checker audit trail (the agent is the
maker, the human approver is the checker). Emoji-reaction (✅ on the PR message) is an acceptable
lighter-weight gate for low-risk steps.

### 7.6 The visible protocol (legible at a glance)

```
🎯  request           (you)            → "Deploy Helm chart for the catalog"
🧩  decomposition     (🟦 Primary)     → sub-tasks + worker assignment
🔧  worker update     (🟩/🟧)          → branch, artifact, what changed
🚦  gate results      (CI, not LLM)    → lint/validate/dry-run/test: PASS/FAIL
🔎  reviewer verdict  (🟥 Reviewer)    → PASS or REJECT + explicit reasons
📦  PR opened         (🟦 Primary)     → link; never auto-merged
⏸️  awaiting approval (→ you)          → [Approve merge] [Apply] [Reject]
✅  done / ❌ halted    (🟦 Primary)     → final state written to state/*.md
```

### 7.7 Residency & data boundary (don't skip this)

Slack is a US SaaS; message content transits Slack's cloud. Given the platform's data-residency
requirement: **Slack carries control + status + approvals only.** Do **not** paste data rows, query
results, real logs, PII, account/card numbers, or secrets into Slack — use **placeholders** and
**links** to artifacts that live on-prem (object store / repo). Long logs → attach as a file *in the
repo* and link, or `files.upload` only sanitized excerpts. This keeps Slack as the cockpit without
violating residency.

### 7.8 Operational limits (Slack-specific)

- **Rate limits:** ~1 `chat.postMessage`/sec per channel → **batch** status updates; don't narrate
  every token. One concise message per loop step.
- **Message size:** ~3000 chars per text block → long output goes to a **file/link**, not the thread.
- **Idempotency:** dedupe on `event_id`; acknowledge events within 3s (Bolt handles ack).
- **Self-loop guard:** always filter the bot's own messages before reacting.
- **Degradation:** if Slack is unreachable, the loop continues server-side and posts a catch-up
  summary when reconnected — Slack is the view, not the engine.

### 7.9 Minimal handler sketch (Bolt, Socket Mode — Python)

```python
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=BOT_TOKEN)                 # xoxb- ; Socket Mode uses xapp- app token

@app.event("app_mention")                  # ① TRIGGER
def on_mention(event, say):
    if event.get("bot_id"):                # self-loop guard
        return
    thread = event.get("thread_ts", event["ts"])
    registry.start(thread, request=event["text"])
    say(thread_ts=thread, text="🧩 Decomposing…")
    run_orchestrator(thread, event["text"])   # Agent SDK: Primary → workers → gates → reviewer
                                              # streams 🔧/🚦/🔎/📦 back into `thread`

@app.action("apply_cluster")               # ⑧ HUMAN DOOR
def on_apply(ack, body, say):
    ack()
    who = body["user"]["id"]; pr = body["actions"][0]["value"]
    audit.record(pr, approver=who)         # four-eyes trail
    ci.trigger("helm-apply", pr)           # DETERMINISTIC action, not the LLM
    say(thread_ts=body["message"]["thread_ts"], text=f"🚀 <@{who}> approved → applying {pr}")

SocketModeHandler(app, APP_TOKEN).start()
```

---

## 8. Production hardening — what the 2026 mainstream adds

The flow above matches how real teams ship this (Devin, Cursor Background Agents, OpenAI Codex,
Tembo all use Slack/ticket → agent → PR → human review). These four upgrades are what production
teams add on top — steal them.

### 8.1 Durable execution (the orchestrator's backbone)

**Problem:** a loop runs an hour, the pod restarts for a patch → state + token spend gone.
**Fix:** wrap the orchestrator in a durable-execution engine (Temporal / Inngest / Cloudflare
Workflows). The loop = a **deterministic workflow**; each LLM / tool / CI call = an **activity**
whose result is journaled. Crash → replay from the last checkpoint, *without re-running side
effects*. (OpenAI Codex and Replit Agent both run on Temporal.)

- **Human door = suspend/resume.** The loop pauses for hours/days waiting on the Slack approval
  *without holding a live process*; the ⑧ button becomes a Signal that resumes the workflow.
- **Idempotency is non-negotiable** — every side effect (open PR, `helm apply`, post message) must
  be safe to run twice; key each by `(thread_ts, step)`.
- **Run-level budget** — the retry cap + token budget from §6 must be tracked at the *whole-run*
  level, not per-call (a model loop spawns its own retries).
- **Continue-as-new** — very long loops blow history limits; periodically restart the workflow with
  compacted state.
- *MVP note:* "state on disk" (§7.3) is the instinct; a durable engine is the professional version.
  Disk-state + idempotency is fine to start — add the engine when loops get long/expensive.

### 8.2 Gate humans by RISK, not everything

Blanket "review every PR" → **rubber-stamp** (people approve because it looks right + tests pass) →
illusion of safety. Instead, hard-gate humans **only at high-blast-radius boundaries** — interface
changes (an OpenAPI breaking-change diff or an MCP tool-surface change counts, §4.2), schema/catalog
migrations, cross-service contracts, anything touching prod or residency —
and let the agent run free elsewhere. Concretely: the ⑧ door fires automatically for
`{prod helm apply, schema/catalog change, cross-namespace}`; low-risk work (docs, dev namespace)
auto-merges after gates + reviewer (that's L2). Plus two supports:
- **Hard-fail test gates**, never soft warnings — an agent *will* exploit a skippable/flaky test.
- **DoD-restate-first** — the worker echoes back the ticket's DoD *before* editing, catching intent
  misreads before they become a 600-line diff.

### 8.3 A trustworthy evaluator (calibrate it; judge the trajectory)

- **Split checks:** deterministic (compile/tests/lint/policy) as hard gates FIRST; the LLM reviewer
  only for the *subjective* parts.
- **Calibrate the reviewer** against a human gold set (aim TPR/TNR > 90%) *before* it gates anything.
  Don't gate a build on an uncalibrated judge.
- **Judge the trajectory, not just the final output** — score intermediate steps (did it skip
  verification? reach a right answer via wrong reasoning?).
- **Measure with pass^k, not pass@k** — a 70%/run agent is ~97% on pass@3 but only ~34% on pass^3.
  pass^k (all k runs succeed) is the honest number for "does it work *every* time."

### 8.4 A continuous eval loop (the golden set grows)

Every real production failure → a **new eval/test case**; run the same scorers in CI *and* on
sampled live traffic. For your catalog MVP the eval set = **golden crawl results across MinIO+S3,
expected schema/lineage, Helm-deploy acceptance checks** — this is the "DoD made runnable" at the
domain level, and (per the field's pushback) it is the **ceiling on the whole loop's quality**.

### 8.5 Reality check — why all of this exists

Gartner (25 Jun 2025): **over 40% of agentic-AI projects will be canceled by end of 2027** — driven
by escalating costs, unclear value/ROI, and inadequate risk controls (plus "agent washing").
The lesson is not "don't build" — it's: **start at L1 on one real ticket, prove value, and let the
four upgrades above be what earns production trust.** Reliability comes from the verifier + the
checkpoint design, *not* a bigger model.
[Gartner press release](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027)

---

## 9. Why this shape — empirical backing

ComPilot (arXiv 2511.00592) is the same loop: generator (LLM proposes) + evaluator that **acts**
(compiler runs and measures) + default-reject. Two measured results justify the design above:
- removing the feedback/verification loop cost **23–40%** of performance → keep steps ⑤ and ⑦;
- letting the generator **self-certify** produced **17.6% wrong** "successful" outputs → the
  reviewer **must** be a separate agent (step ⑤), and the merge/apply **must** be gated (step ⑧).

---

## 10. What to remember

1. **Slack is the cockpit, not the data plane** — control + approvals through Slack; data stays on-prem.
2. One **thread = one loop instance**; persist state on disk (subagents forget).
3. The hard part is the **"no"** — a separate, skeptical, *acting* reviewer + deterministic gates.
4. The **human door is a Block Kit button** that triggers a deterministic CI action = four-eyes audit.
5. Start at **L1**; widen only after the gates have caught real mistakes.
6. **Harden for production (§8):** durable execution, risk-based human gates, a *calibrated* evaluator,
   and a growing eval set — this is what separates a demo from the ~60% of agentic projects that survive.
7. **Memory is machine-checkable files, not prose** — `rules` / `runtime` / `ratchet` / spike evidence per
   repo; `CLAUDE.md` is the map an agent reads before trusting any doc (§4.1).
8. **Verify state after every merge/PUT; one variable per change** — two rules bought with incidents.
9. **App projects: OpenAPI is the contract, MCP is a generated + curated adapter for agent clients only**;
   a spec change goes through the door like a schema migration (§4.2).

---

## 11. Field notes — design (02/07) vs as-run on annamgt (07→09/2026)

| Design (02/07) | As-run | Evidence |
|---|---|---|
| Slack thread = loop instance, Block Kit door | Claude Code session + git MRs became the control plane; Slack/Telegram fronts exist in `loopkit`, the daily loop ran in-terminal | annamgt sessions 06→09; `loopkit/BUILD-MAP.md` §7 |
| `state/*.md` on disk as memory | prose drifted within weeks; replaced by `contracts/{rules,runtime,ratchet}.yml` + `CLAUDE.md` map (03/09) | `annamgt/CLAUDE.md`; data-deployments ratchet #1–#8 |
| Tickets T01–T25 with DoD as the unit of work | DoD turned into rules (I6/I7 written before the chart existed = DoD of T2); tickets became a ledger | streaming-deployments `rules.yml` header |
| Deterministic gates in CI (④) | evaluators existed from 24/08, were wired into CI on 17/09, and the runner had been dead since 17/08 — a gate without proof of running is not a gate | streaming-deployments ratchet #5 |
| Reviewer "acts, not reads" (⑤) | the cheapest acting reviewer was a **spike**: 15 min of docker settled what a design debate could not (Debezium DELETE under REPLICA IDENTITY DEFAULT) | `analytics-agent/docs/spikes/2026-08-24-debezium-wire-format.md` |
| Human door on merge/apply (⑧) | door moved to "show the state-changing command first"; merges inside repos were delegated (*"t trao quyền m làm hết"*, 26/08) | `~/.claude/CLAUDE.md`; session 02b9a3d7 |
| Bounded retries / budget (§6) | rarely hit; the real runaway was **scope**, stopped by one-line interrupts (*"ê thế khỏi đi -> tập trung vào phần report trước đã"*, 03/09) | session 02b9a3d7 |
| Reviewer calibration, pass^k (§8.3) | not done; the substitute was negative tests per rule (a rule ships with the case it must fail) | `ci/test_check_infra.py`, `ci/test_check_contracts.py` |
