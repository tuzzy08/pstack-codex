"""Create a Codex gateway configuration layer. Never reads or writes API keys."""
import argparse
import ipaddress
import json
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlsplit


def render(url, model, env_key, provider="pstack-gateway", catalog=None, check_models=()):
    address = urlsplit(url)
    try:
        local = address.hostname == "localhost" or ipaddress.ip_address(address.hostname).is_loopback
    except ValueError:
        local = False
    if (not address.hostname or address.username is not None or address.password is not None
            or address.query or address.fragment or any(c.isspace() for c in url)
            or not (address.scheme == "https" or address.scheme == "http" and local)):
        raise ValueError("Use HTTPS, or HTTP on a loopback address, without credentials, query, or fragment")
    address.port  # Check invalid ports before writing configuration.
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", env_key):
        raise ValueError("Use an environment variable name, not an API key")
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", provider) or provider in {
        "openai", "ollama", "lmstudio", "amazon-bedrock"
    }:
        raise ValueError("Use a custom provider ID, not a built-in provider ID")
    models = [model, *check_models]
    if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", item) for item in models):
        raise ValueError("Use model names supplied by the gateway owner")
    lines = [f"model = {json.dumps(model)}", f"model_provider = {json.dumps(provider)}",
             'web_search = "disabled"']
    if catalog:
        path = Path(catalog).expanduser().resolve(strict=True)
        content = json.loads(path.read_text(encoding="utf-8"))
        entries = content.get("models") if isinstance(content, dict) else None
        if not isinstance(entries, list) or not entries or any(
            not isinstance(entry, dict) or not isinstance(entry.get("slug"), str) for entry in entries
        ):
            raise ValueError("The catalog must contain a nonempty models list with slug values")
        missing = set(models) - {entry["slug"] for entry in entries}
        if missing:
            raise ValueError("Models absent from the catalog: " + ", ".join(sorted(missing)))
        lines.append(f"model_catalog_json = {json.dumps(str(path))}")
    lines += ["", f"[model_providers.{provider}]", 'name = "Pstack Gateway"',
              f"base_url = {json.dumps(url.rstrip('/'))}", 'wire_api = "responses"',
              f"env_key = {json.dumps(env_key)}"]
    text = "\n".join(lines) + "\n"
    tomllib.loads(text)
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--env-key", required=True)
    parser.add_argument("--provider", default="pstack-gateway")
    parser.add_argument("--catalog", help="Existing gateway model catalog; metadata must match the upstream models")
    parser.add_argument("--check-model", action="append", default=[], help="Additional role model to check in the catalog")
    parser.add_argument("--output", type=Path, help="Create a new configuration layer; existing files are never overwritten")
    args = parser.parse_args()
    try:
        text = render(args.url, args.model, args.env_key, args.provider, args.catalog, args.check_model)
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
            print(f"Created {args.output}. Connection and model routing are not yet verified.")
        else:
            print(text, end="")
        return 0
    except (OSError, ValueError) as error:
        print(f"Gateway configuration error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
