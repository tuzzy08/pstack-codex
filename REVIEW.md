# Pstack review and Codex port

Reviewed on 1 October 2026. Source version 0.15.5. Source commit
`2eb7ed4613cfc8f098dfe464a23680ea44d84c5e`.

Pstack can work in Codex without an application rewrite. Most of the package
is Markdown. It has 47 skills, 23 playbooks, two agent prompt files, and helper
scripts. It has no bundled MCP server or lifecycle hooks. The helpers cover
PR status, task records, plan checks, worktree inspection, and decision logs.

The local core port is in [pstack-codex](pstack-codex/README.md).
It has 50 skills after the three Cursor Team Kit skills were added.
The original workflow content is kept where it does not depend on Cursor.

## Changes needed for Codex

| Source dependency | Change in this port |
|---|---|
| `.cursor-plugin/plugin.json` | A Codex manifest and a local marketplace entry. |
| Cursor skill names and UI fields | Valid folder-matched names. Unsupported fields removed. Manual-invocation policy moved to `agents/openai.yaml`. |
| `Task` and named Cursor agent types | Current Codex agent tools. Original personas are prompt files, not registered agent types. |
| Cloud worker placement | Explicit worktrees and the actual session limits. No claim that a spawn creates a cloud VM. |
| Claude and Grok defaults | Parent-model inheritance. Explicit choices must match available Codex models. Effort is a separate field. |
| `pstack-models.mdc` | An explicitly read project or user Markdown file. No always-applied Cursor rule. |
| Cursor `create-skill` | Codex `skill-creator`, when available. |
| Cursor transcript paths | In-scope Codex chat tools or a supplied export. Exact action audits require exact traces. |
| Cursor `/loop` | Codex scheduled follow-up tools, when available and requested. |
| Broad external-action permission | The user's actual task scope and authorization. |
| Windows test assumptions | The native path delimiter, a portable child process, and an executable Graphite test fixture. |

Every skill links to [Codex runtime](pstack-codex/references/codex-runtime.md).
That file defines the host rules. The 23 playbooks remain available.

Codex supports packaged skills and a compatibility manifest at
`.codex-plugin/plugin.json`. This port uses that supported layout.
[OpenAI plugin packaging guide](https://developers.openai.com/plugins/build/plugins).

## Deslop and the other referenced skills

`deslop` is public. It is part of Cursor Team Kit, not a private Cursor feature.
It checks the code diff for unnecessary comments, abnormal defensive code,
`any` casts, nesting, and style drift. It asks for small edits and stable
behavior. The port includes its instructions and Cursor's MIT license.
[Official deslop source](https://github.com/cursor/plugins/blob/2eb7ed4613cfc8f098dfe464a23680ea44d84c5e/cursor-team-kit/skills/deslop/SKILL.md).

`deslop` cleans code. Pstack's separate `unslop` skill cleans prose.
Both are included. `control-cli` and `control-ui` are also public skill files.
They reuse local tools and do not need a Cursor backend. The port includes
them so a separate Cursor Team Kit installation is not required.

## Limits that remain

- The available Codex agent tools do not guarantee access to Claude or Grok.
  Independent parent-model attempts do not provide model-family diversity.
- Mode reminders now use two Codex command hooks. They keep an explicit
  selection for one chat and restore it on later turns, resume, or compaction.
  They need Python and Codex hook trust. This machine has trusted both hooks.
  Cursor frontmatter itself remains unsupported.
- Chat tools can return recorded command and MCP call items. The runtime
  now directs audits to use those records and their exit status when present.
  A host that returns only summaries still needs a selected trace or export.
- The optional Benny pack depends on Slack events, tracker access, media,
  secrets, and a tested trigger adapter. It is not included in the core port.
  A timer alone does not preserve its event-triggered behavior.
- `make-bot-ui` needs a supplied webhook executor. The Codex scheduler exposed
  here does not provide Cursor's Grok Bot webhook or sender-key card.
- The TypeScript helpers now run with Node.js 24.2 or newer, or Bun, and
  their declared commander dependency. Node never installs packages silently.
  Graphite frontier
  operations still need a working `gt` executable. The worktree audit and
  decision logger now use Python standard-library implementations. They pass
  Windows checks. The audit preserves tracked, untracked, and ignored files,
  uses local refs, and never fetches or deletes. POSIX launchers remain.

The integration limits require specific services or tools. They do not justify a rewrite
of the core skills. The original optional pack remains in the pinned
[upstream source](https://github.com/cursor/plugins/tree/2eb7ed4613cfc8f098dfe464a23680ea44d84c5e/pstack/automations/benny).

## Checks and installation state

- All 50 skills passed the Codex `skill-creator` validator.
- The package check passed for manifests, names, local links, runtime references,
  agent prompts, invocation policies, and both MIT licenses.
- All 52 retained helper tests passed on Windows after the fixture changes
  and Node compatibility update. The default five-second deadline failed
  two compiled Graphite fixture tests. They passed with a longer deadline;
  the test command now allows 30 seconds per test.
- The watcher TypeScript check passed.
- Both real Node entry points pass the help check. A temporary task store
  passed initialization and unit add/update/read. The dependency guard fails
  clearly without installing packages when commander is missing.
- The Windows watcher instructions previously pointed to `cli.ts`, which
  only exports functions. They now use the real `watch-pr` entry point.
- The live watcher read public pstack PR #476 in check mode and polling mode.
  It returned `READY` with CI, review threads, and GitHub merge state clear.
  It made no changes to that upstream PR.
- Benny and the webhook bot UI are outside the current scope, at the user's
  request. No Slack, webhook, or scheduled-task action was performed.
- The portable helper checks pass for append-only logging, formula cells,
  chat isolation, cancellation, paths with spaces, scoped history matching,
  and file preservation during a real Git worktree audit.
- The Codex app server discovers all 50 installed skills and both hooks.
  Hook metadata reports both definitions as enabled and trusted.
- A live CLI chat confirmed that UserPromptSubmit saves mode activation,
  delivers the reminder, and saves cancellation. Resume and compaction
  behavior passed the local checks; desktop delivery remains unverified.
- A fresh CLI test read the pstack deslop instructions and reported a code
  cleanup rule. It did not edit files or use external integrations.
- The CLI rejected the configured `gpt-6.1-sol` and a `gpt-5.4` test override.
  A per-run `gpt-5.5` override succeeded. The account-wide model setting was
  kept. An earlier test with all configured integrations also failed a
  512 MiB allocation; the successful test used temporary isolated settings.
  The user supplied `tuzzy08/pstack-codex` for a dedicated PR test. The
  repository was empty; a minimal main branch was initialized. The port and
  Windows/Linux validation workflow are on `codex/pstack-port`.
  [Draft PR #1](https://github.com/tuzzy08/pstack-codex/pull/1) is open.
  Its first Ubuntu check passed. Its Windows check found a short-path alias
  in the temporary test directory. The check now resolves that directory
  before Git creates the worktrees. The watcher detected the failed check
  and returned `BLOCKER` with exit code 4.
  Desktop reminder delivery still needs a real user mode-selection message.
- CLI plugin discovery first stopped at an invalid feature value in
  `C:\Users\Lenovo\.codex\config.toml`. On follow-up, the single unsupported
  `context_management.experimental_mode = true` entry was commented out.
  A complete backup was saved as `config.toml.before-pstack-fix.bak` beside it.
  All other settings were checked against the original and are unchanged.
  `codex features list` and `codex plugin list` now succeed. The local
  marketplace is registered and version `0.15.5-codex.2` is installed and
  enabled. The dedicated GitHub PR workflow test is in progress.

The local plugin is installed and enabled. Use `$pstack:poteto-mode` in a new
chat. Codex exposes plugin skills with the `pstack:` prefix. The installed
CLI rejects the optional top-level hook `description` field, so this package
omits it. Both command hooks parse without warnings.
