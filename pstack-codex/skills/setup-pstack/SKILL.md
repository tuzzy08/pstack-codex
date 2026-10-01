---
name: setup-pstack
description: Configure pstack model roles, reasoning effort, and a supplied Codex gateway for models from different providers. Use for setup-pstack, configure pstack models, connect a gateway, or changing pstack's budget.
---

Read [Codex runtime](../../references/codex-runtime.md) before using this skill.

# Setup pstack

For models from different providers, read [Gateway setup](references/gateway.md).
Configure the supplied gateway with Codex's native provider settings, then
continue with role selection below. Do not change providers for ordinary
OpenAI model selection. Without connection details, prepare the configuration
workflow and report live activation as pending.

Write `<project>/.codex/pstack-models.md`, or the user-level file if the user
requests personal settings. Each pstack skill reads this file explicitly.

1. Inspect the current agent tool's supported model IDs and effort fields.
   Default to `inherit-parent`. Never guess a model ID.
2. Read existing project and user role settings. Keep unrelated content and
   choices the user did not ask to change.
3. Use the requested model and budget. Ask with the available question tool
   if a missing choice matters. Offer parent inheritance as the default.
   Do not change effort inside a model ID.
4. Validate explicit models and efforts against the current tool schema.
   Show unavailable choices as unresolved. Parent inheritance needs no ID.
5. Write one line per changed role. Panel lists set the seat count. A missing
   panel uses three parent-model attempts. A missing single role inherits.
6. Report the path, changed roles, and any limits on model diversity.

Supported roles are below. This is an example, not a file to overwrite on
every run.

```text
# effort: inherit-parent
feature, refactoring: inherit-parent
bug-fix: inherit-parent
perf-issue: inherit-parent
hillclimb: inherit-parent
judgment and prose: inherit-parent
hardest tasks: inherit-parent
how explorer: inherit-parent
how explainer: inherit-parent
why investigators: inherit-parent
why synthesizer: inherit-parent
reflect tooling: inherit-parent
reflect judgment, divergent, synthesizer: inherit-parent
arena runners: inherit-parent, inherit-parent, inherit-parent
arena cross-judge pool: inherit-parent
swarm workers: inherit-parent
architect runners: inherit-parent, inherit-parent, inherit-parent
interrogate reviewers: inherit-parent, inherit-parent, inherit-parent
```

If the user requests a verification skill, use the bundled
`create-verification-skill` workflow. Model setup alone does not create one.
