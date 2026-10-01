"""Keep explicit Poteto mode selection in this Codex chat. No transcript scans."""
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path


def handle(event, data_dir, plugin_root):
    session = event.get("session_id")
    kind = event.get("hook_event_name")
    if not isinstance(session, str) or not session or kind not in {"SessionStart", "UserPromptSubmit"}:
        return None
    key = hashlib.sha256(session.encode()).hexdigest()
    state = Path(data_dir) / "modes" / (key + ".json")
    active = json.loads(state.read_text(encoding="utf-8")) if state.exists() else False
    if not isinstance(active, bool):
        raise ValueError("invalid pstack mode state")
    if kind == "UserPromptSubmit":
        prompt = event.get("prompt", "")
        if not isinstance(prompt, str):
            raise ValueError("invalid hook prompt")
        command = re.match(r"^\s*\$(?:pstack:)?poteto-mode\b(.*)", prompt, re.S)
        if command or prompt.strip().lower() == "stop poteto mode":
            active = bool(command) and not re.match(r"\s*off\b", command[1], re.I)
            state.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile("w", dir=state.parent, delete=False, encoding="utf-8") as stream:
                json.dump(bool(active), stream)
                temporary = Path(stream.name)
            try:
                os.replace(temporary, state)
            finally:
                temporary.unlink(missing_ok=True)
            if not active:
                return {"hookSpecificOutput": {"hookEventName": kind, "additionalContext":
                    "Poteto mode is off for this chat. Do not apply its ongoing style or workflow triggers."}}
    if not active:
        return None
    skill = Path(plugin_root) / "skills/poteto-mode/SKILL.md"
    runtime = Path(plugin_root) / "references/codex-runtime.md"
    return {"hookSpecificOutput": {"hookEventName": kind, "additionalContext":
        f"Poteto mode is active for this chat. For a relevant task, read {skill} and {runtime} "
        "before applying the workflow. Keep casual replies brief. Follow current user and host rules. "
        "The mode grants no extra permission. The user can turn it off with $pstack:poteto-mode off or stop poteto mode."}}


if __name__ == "__main__":
    try:
        result = handle(json.load(sys.stdin), os.environ["PLUGIN_DATA"], os.environ["PLUGIN_ROOT"])
        if result:
            print(json.dumps(result))
    except (OSError, ValueError, KeyError) as error:
        print(f"pstack mode hook: {error}", file=sys.stderr)
        sys.exit(1)
