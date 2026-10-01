# Gateway setup

Use one Codex provider connection for all pstack roles. The gateway routes each
model name to its upstream provider. Keep the existing native agent workflow.
This plugin configures a supplied gateway; it does not deploy a gateway service.

## Get the connection details

Read the active user configuration and profile before creating a provider.
Reuse an existing gateway when it meets the request. Get the following missing
values from the user or gateway owner:

- HTTPS base URL with the API path. HTTP is allowed only on a loopback address.
- The parent model and model names for code, judgment, and each review seat.
- The name of the credential environment variable, or the installed credential
  helper or custom header configuration. Do not request the credential itself.
- A local model catalog, if the model names are not in the client catalog.

The gateway must support the Responses API, incremental streaming, function
calls, and follow-up turns. A Chat Completions endpoint alone is insufficient.
Do not assume a provider's direct endpoint meets this contract.
See [connection setup](https://learn.chatgpt.com/docs/enterprise/connect-to-a-gateway)
and [compatibility requirements](https://learn.chatgpt.com/docs/enterprise/gateway-compatibility).

## Prepare the native configuration

The helper uses Python 3.11 or newer. It prints a validated TOML layer by default.
Replace these example values with the supplied connection details:

```sh
python <plugin>/skills/setup-pstack/scripts/gateway.py --url https://gateway.example.com/v1 --model parent-model --env-key CODEX_GATEWAY_API_KEY
```

With a supplied catalog, add `--catalog <absolute-path>` and repeat
`--check-model <role-model>` for each selected code, judgment, and review model.
The helper checks catalog membership; it does not invent model metadata or
verify a connection. Use the gateway owner's metadata for tools, context limits,
and supported effort. Never label a different upstream model as an OpenAI model
to get past the client's model list.

For the CLI, use `--output <CODEX_HOME>/pstack-gateway.config.toml` to create a
profile, then start `codex --profile pstack-gateway`. Use `~/.codex` when
`CODEX_HOME` is unset. Existing output files are refused; inspect and merge an
existing profile when an update is requested. Provider settings belong in the
user configuration, not project `.codex/config.toml`.
If the provider ID already exists in the base configuration, inspect its merged
authentication settings. Reuse that connection, or choose an unused custom
provider ID with `--provider`; do not combine old auth settings with a new method.

For the desktop app, back up the user's `config.toml`, then merge the prepared
layer into it when gateway activation is part of the request. Preserve other
settings. Put `model`, `model_provider`, `web_search`, and optional
`model_catalog_json` before the first table. Merge an existing provider table
without duplicate keys. Restart the app after the user has saved their work.
Do not restart it automatically during setup. A CLI profile alone does not
activate the desktop connection.

The helper covers environment-variable bearer authentication. For a supplied
custom header or installed credential helper, use Codex's documented
`env_http_headers` or `[model_providers.<id>.auth]` settings instead of `env_key`.
Use only one authentication method. The credential must reach the process that
launches Codex; a terminal variable may not reach a desktop launch.

## Select and verify the role models

After the connection is active, inspect the current agent tool's model choices.
Write the confirmed gateway model names into `.codex/pstack-models.md`, using
the existing setup workflow. No provider field belongs in that role file.
The main chat keeps its selected parent model; role settings apply to delegated
work. If the host's tool schema does not expose a selected model, report that
role as unavailable. Do not bypass the schema or substitute silently.

Use a fresh chat to test the parent and each distinct role model:

1. Check the active provider and model in CLI `/status` or desktop settings.
2. Ask for the exact reply `gateway-ok` to test the initial connection.
3. Run a harmless read-only command through the agent, then send a follow-up
   that uses its result. Check successful stream completion and tool results.
4. When delegation is available and requested, create a read-only worker for
   each distinct role model. Check completion through the native agent tools.
5. Verify each alias's upstream provider and model through gateway records.
   A model's own name claim is not route evidence.

Separate configuration checks from live evidence. Record which parent, worker,
streaming, tool, follow-up, and upstream-route checks passed. If the gateway or
credentials are missing, leave activation and live verification pending; do not
change the user's current provider. Preserve the existing model-rejection
fallback and disclose any reduction in model diversity.
