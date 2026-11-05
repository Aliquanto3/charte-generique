"""Skill `charte` et place de marché du plugin."""
import json
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SKILL = RACINE / "skills" / "charte" / "SKILL.md"


def frontmatter() -> dict[str, str]:
    m = re.match(r"---\n(.*?)\n---\n", SKILL.read_text(encoding="utf-8"), re.DOTALL)
    assert m, "frontmatter absent"
    return dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1), re.MULTILINE))


def test_frontmatter():
    f = frontmatter()
    assert f["name"] == "charte"
    for declencheur in ("appliquer la charte", "mettre ce dépôt à la charte", "audit de charte", "couleurs hors charte",
                        "migrer vers la charte v2", "nouveau projet à la charte"):
        assert declencheur in f["description"], declencheur


def test_corps_court_et_modes():
    corps = SKILL.read_text(encoding="utf-8")
    assert len(corps.splitlines()) < 150
    for mode in ("init", "audit", "migrer"):
        assert f"`{mode}`" in corps


def test_chemins_cites_existent():
    chemins = re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)", SKILL.read_text(encoding="utf-8"))
    assert chemins
    for c in chemins:
        assert (RACINE / c).exists(), c


def test_marketplace_valide():
    m = json.loads((RACINE / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert m["name"] == "charte-generique" and m["owner"]["name"]
    (plugin,) = m["plugins"]
    assert plugin["name"] == "charte" and plugin["source"] == "./" and plugin["description"]
    assert (RACINE / ".claude-plugin" / "plugin.json").is_file()
