"""Check package structure and local skill links. Run from any directory."""
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "pstack-codex"


def check():
    manifest = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "pstack"
    assert (PLUGIN / manifest["skills"]).is_dir()
    assert (PLUGIN / manifest["interface"]["logo"]).is_file()
    assert "agents" not in manifest
    hooks = json.loads((PLUGIN / manifest["hooks"]).read_text(encoding="utf-8"))
    assert set(hooks["hooks"]) == {"SessionStart", "UserPromptSubmit"}
    assert (PLUGIN / "hooks/mode.py").is_file()
    for groups in hooks["hooks"].values():
        for group in groups:
            for handler in group["hooks"]:
                assert handler["type"] == "command" and handler["timeout"] == 5
                assert 'python "${PLUGIN_ROOT}/hooks/mode.py"' == handler["commandWindows"]
    marketplace = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    assert (ROOT / marketplace["plugins"][0]["source"]["path"]).resolve() == PLUGIN
    skills = list((PLUGIN / "skills").glob("*/SKILL.md"))
    assert len(skills) == 50, f"Expected 50 skills, found {len(skills)}"
    assert len(list((PLUGIN / "skills/poteto-mode/playbooks").glob("*.md"))) == 23
    for skill in skills:
        text = skill.read_text(encoding="utf-8")
        front = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        assert front, f"Missing frontmatter: {skill}"
        name = re.search(r"^name: (.+)$", front[1], re.M)
        assert name and name[1] == skill.parent.name, f"Skill name mismatch: {skill}"
        assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name[1])
        assert re.search(r"^description: \S", front[1], re.M)
        assert not re.search(r"^(?:paths|mode|reminder|icon|color|disable-model-invocation):", front[1], re.M)
        assert "[Codex runtime](../../references/codex-runtime.md)" in text
    for path in PLUGIN.rglob("*.md"):
        if "node_modules" in path.relative_to(PLUGIN).parts:
            continue
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\b(?:claude-(?:opus|fable)-[\w.-]+|grok-[\w.-]+|gpt-5\.6-sol-max)\b", text), path
        assert "~/.cursor/" not in text, path
        prose = re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[^\n]*(?:\n|$)", "", text)
        prose = re.sub(r"`[^`\n]+`", "", prose)
        for target in re.findall(r"\]\(([^)\n]+)\)", prose):
            target = target.split("#", 1)[0].strip("<>")
            if not target or target == "url" or re.match(r"[a-z]+:", target):
                continue
            assert (path.parent / unquote(target)).exists(), f"Broken link: {path}: {target}"
    for filename in ("LICENSE", "LICENSE.cursor-team-kit"):
        assert "MIT License" in (PLUGIN / filename).read_text(encoding="utf-8")
    assert (PLUGIN / "references/agents/comment-sicko.md").is_file()
    assert (PLUGIN / "references/agents/poteto-agent.md").is_file()
    policies = list((PLUGIN / "skills").glob("*/agents/openai.yaml"))
    assert len(policies) == 46
    assert all("allow_implicit_invocation: false" in p.read_text(encoding="utf-8") for p in policies)
    print("PASS: 50 skills, 23 playbooks, manifests, local links, runtime references, and licenses")


if __name__ == "__main__":
    check()
