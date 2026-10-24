"""Bounded artifact/preservation checks; no scientific or runtime certification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote


FOLDER = Path(__file__).resolve().parent
ROOT = FOLDER.parents[2]


def verify() -> dict:
    errors = []
    checks = {}

    def require(ok, message):
        if not ok:
            errors.append(message)

    baseline = json.loads((FOLDER / "baseline.json").read_text(encoding="utf-8"))
    changed = []
    for relative, expected in baseline["files_sha256"].items():
        path = ROOT / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            changed.append(relative)
    checks["preexisting_files"] = len(baseline["files_sha256"])
    checks["changed_preexisting_files"] = changed
    require(not changed, "Preexisting files changed: " + repr(changed))

    inventory = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
        text=True, encoding="utf-8"
    ).splitlines()
    prefix = FOLDER.relative_to(ROOT).as_posix() + "/"
    unexpected = sorted({p for p in inventory if p not in baseline["files_sha256"]
                         and not p.startswith(prefix) and "__pycache__" not in p})
    checks["unexpected_new_files"] = unexpected
    require(not unexpected, "Unexpected new files: " + repr(unexpected))

    local_links = 0
    for path in sorted(FOLDER.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        require(not any(line.rstrip() != line for line in content.splitlines()),
                "Trailing whitespace: " + path.name)
        require(content.endswith("\n"), "Missing final newline: " + path.name)
        for target in re.findall(r"\]\(([^)]+)\)", content):
            target = unquote(target.strip("<>"))
            if target.startswith(("https://", "http://", "mailto:")):
                continue
            file_part, _, fragment = target.partition("#")
            dest = Path(file_part) if Path(file_part).is_absolute() else path.parent / file_part
            if not file_part:
                dest = path
            local_links += 1
            require(dest.is_file(), f"Missing link: {path.name}: {target}")
            if fragment and dest.is_file() and dest.suffix == ".md":
                headings = re.findall(r"^#+\s+(.+)$", dest.read_text(encoding="utf-8"), re.M)
                anchors = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}
                require(fragment in anchors, f"Missing anchor: {path.name}: {target}")
    checks["local_links_checked"] = local_links

    state = json.loads((FOLDER / "research-state.json").read_text(encoding="utf-8"))
    require({r["id"] for r in state["requirements"]} == {f"R{i}" for i in range(1, 8)},
            "Missing mandatory research requirement")
    require(all(r["status"] == "VERIFIED" and r.get("evidence") for r in state["requirements"]),
            "Unverified research requirement")
    require(all(c["status"] in {"SATISFIED", "NOT_APPLICABLE"} and c.get("evidence")
                for c in state["controls"].values()), "Unresolved control")
    require(state["active_control"] is None, "A control is still active")
    manifest_path = Path(state["control_manifest"])
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = {s["name"] for s in manifest["plugin_skills"]} | {"never-stop"}
        expected.discard("all-the-medicine")
        require(set(state["controls"]) == expected, "Control inventory differs from manifest")
    else:
        errors.append("Control manifest unavailable; cannot reverify inventory")
    checks["requirements"] = len(state["requirements"])
    checks["controls"] = len(state["controls"])
    sources = (FOLDER / "SOURCES.md").read_text(encoding="utf-8")
    source_ids = re.findall(r"^\| ([AV]\d+) —", sources, re.M)
    require(set(source_ids) == {f"A{i}" for i in range(1, 8)} | {f"V{i}" for i in range(1, 9)},
            "Source inventory mismatch")
    checks["primary_sources"] = len(source_ids)
    diff = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True)
    checks["git_diff_check_exit"] = diff.returncode
    require(diff.returncode == 0, diff.stdout + diff.stderr)
    return {"status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors,
            "limits": ["Links checked locally, not remote uptime or source truth",
                       "Control/requirement metadata checked structurally, not proof of their claims",
                       "No scientific, model, economic or security certification"]}


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
