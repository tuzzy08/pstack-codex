---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
---

Read [Codex runtime](../../references/codex-runtime.md) before using this skill. Apply its tool, model, permission, and history rules to the workflow below.

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

## When to invoke

Invoke when the user says "reflect" or "$reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

### 1. Locate the active record

Use the current chat context. If a complete transcript was supplied in this
session, use that exact file. For another named chat, use Codex `read_thread`
within the requested project. Give reviewers a scoped digest when there is
no export. Report missing action-level evidence instead of guessing a path.

### 2. Spawn three reviewers in parallel

One message, three Codex agent calls, a general Codex worker prompt, with `model` set as below, agent mode (a prompt with an explicit read or write scope). Reviewers need MCP access for context lookups (tickets, chat threads, observability traces referenced in the transcript). Use the tools actually exposed to the worker.

Read the model policy in Codex runtime. Resolve each named role there. Default to the parent model.

| Lens | Role line | Default `model` | Prompt template |
|---|---|---|---|
| Judgment | `reflect judgment, divergent, synthesizer` | `inherit-parent` | `references/judgment-reviewer.md` |
| Tooling | `reflect tooling` | `inherit-parent` | `references/tooling-reviewer.md` |
| Divergent | `reflect judgment, divergent, synthesizer` | `inherit-parent` | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in the the Codex agent tool response body.

### 3. Synthesize

One the Codex agent tool call, a general Codex worker prompt, with `model` from the `reflect judgment, divergent, synthesizer` line (default `inherit-parent`), agent mode (a prompt with an explicit read or write scope). The synthesizer's quality check includes spot-verifying citations, which can require MCP access. Use the tools actually exposed to the worker. Use `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. The synthesizer returns a structured Accepted / Rejected / Backlog list.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. See the **encode-lessons-in-structure** principle skill.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent in the org. Do not auto-apply.

Keep backlog items in the report unless the user authorized tracker writes. Apply accepted edits when the user has already authorized them; otherwise present the concrete edits for approval.

For each approved Accepted item, follow the Routing field exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent does directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to Codex's `skill-creator` skill and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to `skill-creator` and run its description-optimization loop.
- `new skill via skill-creator: <kebab-name>`: hand creation to `skill-creator`. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done. Skip this step if it doesn't.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
