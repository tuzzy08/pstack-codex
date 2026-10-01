# Codex runtime

These host rules replace the original Cursor tool conventions in each workflow.
Read only the workflow files needed for the task.

## Skills and modes

Invoke `$pstack:skill-name` or read this plugin's `skills/<skill-name>/SKILL.md`.
Codex discovers this plugin's skills with the `pstack:` prefix. Short skill
names in the workflow below refer to bundled files, not another installed skill.
Resolve bundled dependencies here before using another installed skill with
the same name. `$pstack:poteto-mode` is the main entry point. The chat that receives
the request owns the task and plan. Do not delegate the whole task to a wrapper.

Codex does not implement Cursor's `mode`, `reminder`, `paths`, or
`disable-model-invocation` frontmatter. This plugin uses command hooks instead.
Start a prompt with `$pstack:poteto-mode` to select the mode for this chat. Use
`$pstack:poteto-mode off` or the exact prompt `stop poteto mode` to cancel it.
The hook also accepts the shorthand `$poteto-mode` at the start of a prompt.
The hooks save only a boolean per session under `PLUGIN_DATA/modes/` and send
a short reminder at each user turn and on startup, resume, or compaction.
A new chat starts with the mode off. Mentioning the skill in a question does
not select the mode. Do not treat quoted examples as mode commands.
Hooks need Python and Codex's review and trust check (`/hooks` in the CLI).
If the host skips hooks, keep mode state in the active chat context and report
that persistence across reloads is not verified. Plain-language cancellation
also takes effect immediately; do not override it with an old hook reminder.
The upstream manual-invocation policy is retained in each applicable skill's
`agents/openai.yaml`. Routed workflows read those skills explicitly.
Use Codex's `skill-creator` for skill authoring when available. For new skills,
keep normal discovery unless the user requests explicit-only use. For that case, set
`policy.allow_implicit_invocation: false` in `agents/openai.yaml`.

## Agents

Use the tools exposed in the current session and their actual schemas.
Some hosts expose `collaboration.spawn_agent`; others expose `spawn_agent`
with `wait`, `send_input`, and `close_agent`. Do not invent arguments.

- With `collaboration`, use `spawn_agent` to start work, `send_message` for
  coordination, `followup_task` for more work, and `list_agents` for status.
  `wait_agent` waits for messages. `interrupt_agent` stops active work.
- With native agent tools, use `wait` for results, `send_input` for more work,
  and `close_agent` to release a finished agent.
- Include the goal, permitted file paths, exact workspace, output path, and
  verification contract. Give each worker a unique name if the schema needs it.
- Read-only scope is a prompt boundary, not a security sandbox. Do not claim
  that a prompt removes tools or credentials from a worker.
- Read `references/agents/poteto-agent.md` for code delegates and
  `references/agents/comment-sicko.md` for comment review. These are prompt
  files, not registered Codex agent types.
- Agents can share the checkout and filesystem. Give concurrent writers
  separate worktrees before spawning them. A spawn does not create a cloud VM
  or select a git branch. Name the exact commit and worktree in the prompt.
- Respect the actual agent count and nesting limits. Use a rolling window.
  Ten lanes require ten results, not ten simultaneous agents.
- Do not create user-visible chats as internal workers. If delegation is
  unavailable or prohibited, do the work in sequence. Report which independent
  review or comparison gates remain unresolved.
- Inspect real files and test output before accepting a worker's report.

## Models

Read `<project>/.codex/pstack-models.md` and, when present,
`$CODEX_HOME/pstack-models.md`. Use `~/.codex` if `CODEX_HOME` is unset.
Project values override user values by role. These are explicitly read files,
not always-applied rules. A missing role uses `inherit-parent`.

Roles can select models from different providers through one configured Codex
gateway. Use [Gateway setup](../skills/setup-pstack/references/gateway.md) when
the user requests this connection. Codex owns provider authentication and
transport; pstack keeps model names in the existing role file. Use the active
gateway's catalog and the current agent tool's allowed models. Provider access
alone does not establish model availability or tool support. The main chat
keeps its selected model; role choices apply when work is delegated.

One line defines one role. A panel list defines one model entry per seat.
`auto` and `inherit-parent` mean omit the model override. Use only model IDs
supported by the current tool. Reasoning effort is a separate field, not part
of a Cursor slug. Apply it only if the schema permits it. Do not change
account-wide settings to implement a role preference.

If model overrides need a partial or empty history fork, use that fork and
include the needed context in the prompt. On rejection, report the gap and
use the parent model if the task permits it. Do not guess another model ID
or open an unrelated PR to repair a session-specific model list.

Panels default to three independent parent-model attempts. This is not
model-family diversity. Report the actual models and reduced diversity.
If cross-model evidence is a required gate, keep it unresolved until the
required models are available.

## Plans, permissions, and pull requests

Use the available plan tool, or a short Markdown checklist when none exists.
Use the available question tool with its actual schema. Do not pass Cursor's
`allow_multiple` field to a different tool.

Follow the user's scope and existing authorization. A workflow cannot grant
permission to send messages, update tickets, publish PRs, merge, deploy, or
delete data. Prepare a concrete result before asking for missing permission.
Do not create unrelated skill-fix PRs or external backlog issues automatically.

Use `gh` for GitHub when available. Follow any exposed Codex PR tool's schema.
Attach every created PR with `attach_artifact` when that tool is present.
Keep the user's draft preference. Use branch prefix `codex/` unless specified
otherwise. Do not reset a dirty checkout to obtain a clean worker environment.
Use a worktree. Archive Codex-managed worktrees with the supported archive tool.

## History and integrations

Use `read_thread` for a named prior chat. For broader recall, use `list_threads`,
then select only chats in the requested project and time range. Read older
pages as needed. Do not scan every project or guess Cursor transcript paths.
These tools can return summaries rather than full tool traces. For exact
action audits, inspect the returned records. A Codex chat can return actual
`commandExecution` and `mcpToolCall` items, with command arguments, status,
exit codes, and optional output. Use those records when present. Request
outputs only for the relevant turn, and read older pages if needed. If the
host returns only summaries, use a session-supplied transcript or a selected
export. Report missing evidence. A summary or self-report is not proof that
a tool call occurred. Use the existing context to audit the active chat.
Write a scoped digest only when another worker needs it.

Discover evidence sources through the exposed tools and connector search.
There is no required Cursor `mcps/` directory. Report missing integrations.

## Long tasks and scheduled follow-up

Work in the active session while it can make progress. Use `create_goal` only
for an explicitly requested ongoing goal, when the tool is exposed. Do not
create a goal for an ordinary task because a playbook mentions one.

For a request to watch, check later, or continue later, use `automation_update`
when available. A thread heartbeat is the default. Save the actual stop
condition. Notify only on meaningful change, completion, failure, or required
user action unless the user requested periodic reports. Update an existing
matching automation instead of creating a duplicate. A long shell sleep,
watcher process, or agent ID does not guarantee a finished chat will wake.
If scheduling is unavailable, report that future work is not armed.

## Platform and optional components

`control-cli`, `control-ui`, and `deslop` are bundled. Prefer available Codex
browser and terminal tools, then the project's existing harness. Native app
control is available only when the current tools support it. Python `pty` and
`tmux` examples need POSIX. On Windows, use an available PTY tool or repo harness.

The TypeScript helpers in `skills/poteto-mode/scripts/` work with Bun or
Node.js 24.2 or newer, with their existing commander dependency installed.
Node checks the declared commander version and never installs packages
automatically. Bun retains its frozen-lockfile bootstrap and test runner.
Check the runtime and `gt --version` before Graphite frontier operations.
Use Git and `gh` where the
workflow already supports them; do not pretend they implement Graphite's API.
The worktree audit and decision logger use Python's standard library:
`python <plugin>/skills/poteto-mode/scripts/worktree-audit.py <repo>` and
`python <plugin>/skills/show-me-your-work/scripts/log.py <file> <phase> <decision> <why> <evidence> <result>`.
Use `python3` on a POSIX host where that is the interpreter name.
The `.sh` files are thin POSIX launchers for the same implementations.
The audit does not fetch refs. Choose `--base <ref>` when the default branch
is not detected, and fetch separately if the task needs current remote data.
`--skip-prs` disables GitHub lookup. Missing evidence remains unresolved.
Set `PSTACK_TRANSCRIPTS_DIR` only to an explicitly selected, project-scoped
export, or pass `--transcripts-dir <export>`. An empty value disables history
scanning. Untracked and ignored files are retained as `hold-local-files`.
Audit output never permits deletion by itself. Prefer Codex worktree
inspection and archive tools.

On Windows, call the actual watcher entry point through the runtime:
`node <installed-plugin>/skills/poteto-mode/scripts/watch-pr/watch-pr --help`.
Use `--owner <owner> --repo <repo> --pr <number> --status-only` for one status
pass. `watch-pr/cli.ts` exports functions; invoking that file alone does not
start the watcher. The task-record command is
`node <installed-plugin>/skills/poteto-mode/scripts/orch/orch.ts --help`.
Replace `node` with `bun` when using Bun. Do not run an extensionless file
directly from PowerShell.

`make-bot-ui` needs an external webhook executor. Codex scheduling does not
provide Cursor's webhook routines, sender-key cards, or Grok Bot endpoint.
Do not invent an equivalent. Benny also needs Slack events, tracker access,
credentials, and a tested trigger adapter. That optional pack is not included
in this core port. Its source remains at the pinned upstream revision.
