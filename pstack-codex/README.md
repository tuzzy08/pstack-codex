# Pstack for Codex

This is a local, unofficial port of pstack 0.15.5. It contains the original
47 skills and 23 playbooks, with changes for Codex. It also contains `deslop`,
`control-cli`, and `control-ui` from Cursor Team Kit. Both MIT licenses are included.

The source is `cursor/plugins` at commit
`2eb7ed4613cfc8f098dfe464a23680ea44d84c5e`.
The review is saved as `REVIEW.md` at the repository root.

## Install

The repository has a local marketplace at `.agents/plugins/marketplace.json`.
After you review the files, these CLI commands can register and install it:

```powershell
codex plugin marketplace add 'C:\Users\Lenovo\Documents\ChatGPT\Poteto'
codex plugin add pstack@pstack-codex-local
```

Version `0.15.5-codex.2` is installed and enabled in the local Codex plugin cache.
Codex discovers all 50 skills. The command hooks pass the installed CLI's parser.
A fresh CLI test uses a per-run model override; the desktop model setting is unchanged.

Both reminder hooks were reviewed and trusted through the CLI `/hooks` menu.
A live CLI chat confirmed mode activation, reminder delivery, and cancellation.
On another computer, or after a hook definition changes, open `/hooks` and
review the two **pstack** definitions. Installation alone does not trust them. See the
[Codex hook trust rules](https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks).
Start a new desktop chat to load the installed skills.

## Use

```text
$pstack:setup-pstack
$pstack:poteto-mode Fix this bug. Reproduce it first, then verify the fix.
$pstack:interrogate Review the current change.
$pstack:deslop Clean the code diff.
```

Pstack reads its own bundled dependencies by path. This prevents another
installed `tdd`, `how`, or control skill from replacing its workflow.
The original manual-invocation policy is kept in Codex metadata.
Start a prompt with `$pstack:poteto-mode` to select the mode for this chat.
Use `$pstack:poteto-mode off` or `stop poteto mode` to turn it off.
Trusted hooks restore reminders on later turns, resume, and compaction.
A new chat starts with the mode off. If hooks are skipped, only the current
chat context keeps the mode. The hook stores one boolean per chat; it does
not read transcript archives.

Models inherit the current chat by default. `$pstack:setup-pstack` can write
`.codex/pstack-models.md` in your project. It uses model IDs and effort fields
from the available agent tool. It does not assume access to Claude or Grok.

For models from different providers, setup now supports one supplied Codex
gateway. A Python helper prepares a native configuration layer without API
keys or overwriting existing files. The CLI uses a profile; desktop activation
uses the user configuration and an app restart. Role models still use the
same file and native agent tools. Read [Gateway setup](skills/setup-pstack/references/gateway.md)
for connection details, catalog checks, and live verification. This port does
not deploy a gateway or supply provider credentials.

Read [Codex runtime](references/codex-runtime.md) for agent tools, history,
permissions, scheduled tasks, and Windows commands. This core port does not
include the optional Benny event automation pack. `make-bot-ui` needs a
separate webhook executor.

## Native helper commands

With Node.js 24.2 or newer and the declared commander dependency installed:

```powershell
node pstack-codex/skills/poteto-mode/scripts/watch-pr/watch-pr --owner tuzzy08 --repo pstack-codex --pr 1 --status-only
node pstack-codex/skills/poteto-mode/scripts/orch/orch.ts --help
```

These commands start the real entry points. `watch-pr/cli.ts` only exports
functions. Node does not install packages automatically. Bun keeps its
frozen-lockfile dependency bootstrap. Graphite is needed only for the
task-record helper's frontier discovery, not for GitHub PR checks.

## Check the files

From the repository root:

```powershell
python tools/validate_port.py
python tools/check_runtime.py
```

For the retained Bun helper suite:

```powershell
Set-Location pstack-codex/skills/poteto-mode/scripts
bun install --frozen-lockfile
bun test --timeout 30000 orch watch-pr
bun run typecheck
```

The helper suite passed all 52 tests on Windows. The TypeScript check passed.
The 30-second test deadline allows compilation and execution of the Windows
Graphite test fixture. The original 5-second deadline was too short.
The decision logger and worktree audit use Python's standard library and pass
checks on Windows. The audit preserves untracked and ignored files and does
not fetch or delete. Thin Bash launchers remain for POSIX hosts.
