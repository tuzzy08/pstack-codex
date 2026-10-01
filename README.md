# Pstack for Codex

An unofficial Codex port of the pstack plugin from cursor/plugins.
The port keeps the upstream workflows and both MIT licenses.

It contains 50 skills, 23 playbooks, portable helpers, and per-chat mode
reminders. The original Cursor workflows remain in place where the host
supports them. `deslop`, `control-cli`, and `control-ui` are bundled.

## Install

Clone this repository, then register the local marketplace:

```sh
git clone https://github.com/tuzzy08/pstack-codex.git
cd pstack-codex
codex plugin marketplace add .
codex plugin add pstack@pstack-codex-local
```

Review and trust the two pstack hooks in Codex's `/hooks` menu. They need
Python. Start a new chat and use `$pstack:poteto-mode Your task here`.
Use `$pstack:poteto-mode off` to cancel the mode.

Use `$pstack:setup-pstack` to select role models. For models from different
providers, it can prepare one native Codex gateway connection, then use that
gateway's model names for code, judgment, and review. Supply a compatible
gateway URL, model routes, and a credential environment variable name.
See [gateway setup](pstack-codex/skills/setup-pstack/references/gateway.md).

Read the [package guide](pstack-codex/README.md) for commands and checks.
The [review](REVIEW.md) records the changes, evidence, and remaining limits.

## Runtime

The PR watcher and task-record helper run with Node.js 24.2 or newer, or Bun,
after their declared dependencies are installed. Python helpers use the
standard library. Only Graphite frontier discovery requires `gt`.

GitHub Actions checks the package, runtime behavior, retained helper tests,
and watcher types on Windows and Linux. Benny and the webhook bot service
are outside the current scope.

Both [upstream MIT licenses](pstack-codex/LICENSE) are kept, including the
[Cursor Team Kit license](pstack-codex/LICENSE.cursor-team-kit).
