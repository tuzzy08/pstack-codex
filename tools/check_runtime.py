"""Run with python tools/check_runtime.py. Uses temporary files and a local Git repo."""
import importlib.util
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "pstack-codex"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check():
    log = load("decision_log", PLUGIN / "skills/show-me-your-work/scripts/log.py")
    mode = load("mode", PLUGIN / "hooks/mode.py")
    audit = load("audit", PLUGIN / "skills/poteto-mode/scripts/worktree-audit.py")
    with tempfile.TemporaryDirectory(prefix="pstack-check-") as folder:
        root = Path(folder).resolve()
        if shutil.which("node"):
            scripts = PLUGIN / "skills/poteto-mode/scripts"
            watcher = scripts / "watch-pr/watch-pr"
            orch = scripts / "orch/orch.ts"
            for entry in (watcher, orch):
                result = subprocess.run(["node", str(entry), "--help"], capture_output=True, text=True)
                assert result.returncode == 0 and "Usage:" in result.stdout, result.stderr
            store = root / "node store"
            def node_orch(*args):
                result = subprocess.run(["node", str(orch), "--store", str(store), "--json", *args], capture_output=True, text=True)
                assert result.returncode == 0, result.stderr
                return json.loads(result.stdout)
            node_orch("init")
            node_orch("unit", "add", "node-check", "--track", "runtime")
            node_orch("unit", "set", "node-check", "--state", "verified")
            assert node_orch("unit", "get", "node-check")["state"] == "verified"
            empty = root / "no dependencies"
            empty.mkdir()
            shutil.copyfile(scripts / "bootstrap.ts", empty / "bootstrap.ts")
            shutil.copyfile(scripts / "package.json", empty / "package.json")
            (empty / "check.ts").write_text('import { ensureDependenciesInstalled } from "./bootstrap.ts"; ensureDependenciesInstalled();')
            result = subprocess.run(["node", str(empty / "check.ts")], capture_output=True, text=True)
            assert result.returncode != 0 and "Install commander 14.0.0" in result.stderr
            assert not (empty / "node_modules").exists(), "Node must not install dependencies silently"
        path = root / "logs/decisions.tsv"
        log.append(path, ["start", "=1+1", "\t@sum\n", "a\rb", "open"])
        first = path.read_bytes()
        log.append(path, ["check", "done", "proof", "path", "pass"])
        assert path.read_bytes().startswith(first), "log must stay append-only"
        rows = path.read_text(encoding="utf-8").splitlines()
        assert len(rows) == 3 and all(len(row.split("\t")) == 6 for row in rows)
        assert rows[1].split("\t")[2:5] == ["'=1+1", "' @sum ", "a b"]
        event = {"session_id": "../chat-a", "hook_event_name": "SessionStart"}
        data = root / "plugin-data"
        assert mode.handle(event, data, PLUGIN) is None
        event.update(hook_event_name="UserPromptSubmit", prompt="What does $poteto-mode do?")
        assert mode.handle(event, data, PLUGIN) is None
        event["prompt"] = "$pstack:poteto-mode Check this file."
        assert "active" in mode.handle(event, data, PLUGIN)["hookSpecificOutput"]["additionalContext"]
        event.update(hook_event_name="SessionStart", source="compact")
        assert mode.handle(event, data, PLUGIN)
        assert mode.handle(dict(event, session_id="chat-b"), data, PLUGIN) is None
        event.update(hook_event_name="UserPromptSubmit", prompt="$poteto-mode off")
        assert "off" in mode.handle(event, data, PLUGIN)["hookSpecificOutput"]["additionalContext"]
        assert mode.handle(dict(event, hook_event_name="SessionStart"), data, PLUGIN) is None
        event["prompt"] = "$poteto-mode on"
        mode.handle(event, data, PLUGIN)
        event["prompt"] = "stop poteto mode"
        mode.handle(event, data, PLUGIN)
        assert mode.handle(dict(event, hook_event_name="SessionStart"), data, PLUGIN) is None
        assert len(list((data / "modes").glob("*.json"))) == 1
        assert all(file.parent == data / "modes" for file in data.rglob("*.json"))
        repo = root / "main repo"
        repo.mkdir()
        def git(*args, cwd=repo):
            return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True)
        git("init", "-b", "main")
        (repo / "tracked.txt").write_text("original\n")
        (repo / ".gitignore").write_text("cache/\n")
        git("add", ".")
        git("-c", "user.name=Pstack Check", "-c", "user.email=pstack-check@example.invalid", "commit", "-m", "base")
        clean = root / "clean tree"
        dirty = root / "dirty tree"
        git("worktree", "add", "-b", "clean", str(clean))
        git("worktree", "add", "-b", "dirty", str(dirty))
        (dirty / "tracked.txt").write_text("changed\n")
        (dirty / "untracked.txt").write_text("keep\n")
        (dirty / "cache").mkdir()
        (dirty / "cache/ignored.txt").write_text("keep too\n")
        exports = root / "exports"
        exports.mkdir()
        (exports / "wrong.txt").write_text(str(clean) + "-other/file")
        assert audit.last_chat(clean, exports) == 0, "do not match sibling paths"
        (exports / "selected.jsonl").write_text(json.dumps({"cwd": str(clean)}) + "\n")
        assert audit.last_chat(clean, exports) > 0
        before = git("status", "--porcelain", "--ignored", cwd=dirty).stdout
        rows = {row["path"]: row for row in audit.audit(repo, exports=exports, with_prs=False)}
        assert rows[str(clean)]["bucket"] == "verify-recent-chat"
        assert rows[str(dirty)]["bucket"] == "hold-wip"
        assert rows[str(dirty)]["dirty"] == "wip:1,untracked:1,ignored:1"
        assert git("status", "--porcelain", "--ignored", cwd=dirty).stdout == before
        git("restore", "tracked.txt", cwd=dirty)
        rows = {row["path"]: row for row in audit.audit(repo, with_prs=False)}
        assert rows[str(dirty)]["bucket"] == "hold-local-files"
        assert rows[str(clean)]["bucket"] == "verify-history"
        assert (dirty / "untracked.txt").read_text() == "keep\n"
        result = subprocess.run(["python", str(PLUGIN / "skills/poteto-mode/scripts/worktree-audit.py"), str(repo), "--skip-prs"], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert "SIZE_BYTES\tAGE" in result.stdout and str(dirty) in result.stdout
    print("PASS: Node entry points and task records, dependency guard, decision log, chat mode isolation and cancellation, worktree paths, retained files, and read-only audit")


if __name__ == "__main__":
    check()
