"""Verify D096 documentation adoption; no runtime or usefulness claim.

Run from any directory: python -B <this file> [--output <json path>]
The archive is the pre-edit working tree, not an earlier Git commit.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
import zipfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CANON = "docs/architecture/25_METACOGNITION_DUAL_SPACE_INQUIRY.md"
PROPOSAL = "docs/reviews/METACOGNITION_DUAL_SPACE_PROPOSAL_2026-11-01.md"
PLAN = "docs/reviews/integration-research-2026-10-24/IMPLEMENTATION_SEQUENCE_2026-10-25.md"
PROGRESS = "docs/reviews/implementation-2026-10-25/progress.json"
REGISTER = "docs/architecture/ARCHITECTURE_REGISTER.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def headings(text):
    counts, anchors = Counter(), set()
    for line in text.splitlines():
        if re.match(r"^#{1,6} ", line):
            slug = re.sub(r"[^\w -]", "", re.sub(r"^#+\s+", "", line).lower()).replace(" ", "-")
            anchors.add(slug + (f"-{counts[slug]}" if counts[slug] else ""))
            counts[slug] += 1
    return anchors


def verify():
    errors, checks = [], {}

    def require(condition, message):
        if not condition:
            errors.append(message)

    baseline = json.loads((HERE / "baseline.json").read_text(encoding="utf-8"))
    require(digest((HERE / "pre-adoption.zip").read_bytes()) == baseline["archive_sha256"], "Archive hash changed")
    with zipfile.ZipFile(HERE / "pre-adoption.zip") as archive:
        before = {name: archive.read(name) for name in archive.namelist()}
    require(all(digest(data) == baseline["before_sha256"][name] for name, data in before.items()), "Archived bytes differ from baseline")
    checks["archived_exact_files"] = len(before)
    for path in baseline["protected_paths"]:
        require(digest((ROOT / path).read_bytes()) == baseline["before_sha256"][path], "Protected file changed: " + path)
    checks["protected_files"] = len(baseline["protected_paths"])

    canonical = (ROOT / CANON).read_text(encoding="utf-8")
    proposal = (ROOT / PROPOSAL).read_text(encoding="utf-8")
    require("inquiry-feedback/1.0 — ACCEPTED" in canonical, "Missing accepted version")
    require("PROPOSED — NOT ADOPTED OR ACTIVATED" in proposal, "Historical proposal disposition altered")
    require(digest((ROOT / PROPOSAL).read_bytes()) in canonical, "Proposal hash not bound")
    require("Freigabe. Übernimm die Erweiterung verbindlich" in canonical, "Approval provenance absent")

    def rules(text):
        return dict(re.findall(r"^\*\*((?:I|F)\d+) (.+)$", text, re.M))

    require(rules(canonical) == rules(proposal), "Approved I/F rule text not preserved exactly")
    require(len(rules(canonical)) == 12, "Expected 7 inquiry and 5 feedback rules")
    expected_cases = re.findall(r"^\| AC-\d+:.*$", proposal, re.M)
    require(re.findall(r"^\| AC-\d+:.*$", canonical, re.M) == expected_cases, "Acceptance rows changed")
    require(len(expected_cases) == 12, "Expected 12 behavioral acceptance specifications")
    old_examples = proposal.split("## Worked examples\n", 1)[1].split("## Proposed acceptance cases", 1)[0]
    new_examples = canonical.split("## Worked examples\n", 1)[1].split("## Acceptance cases", 1)[0]
    require(new_examples == old_examples, "Worked examples changed")
    checks.update(inquiry_rules=7, feedback_rules=5, worked_examples=5, future_acceptance_cases=12, behavioral_tests_run=0)
    for phrase in ("Unproven benefit of this extension is not a build/run entry gate", "Observable incremental self-improvement", "What should improve and how to measure it", "Search persistence and economic uncertainty", "No universal patience threshold", "Unknown charges remain unknown", "Material changes retain D008/D026", "Ultimate purpose: economically useful trading opportunities", "Economic usefulness is the ultimate purpose"):
        require(phrase in canonical, "Missing approved clarification: " + phrase)

    register = json.loads((ROOT / REGISTER).read_text(encoding="utf-8"))
    old_register = json.loads(before[REGISTER])
    require(register["decisions"][:len(old_register["decisions"])] == old_register["decisions"], "Historical structured decisions changed")
    added = [item for item in register["decisions"] if item["id"] == "D096"]
    require(len(added) == 1 and added[0]["status"] == "ACCEPTED", "D096 missing, duplicated, or not accepted")
    require(register["rejections"] == old_register["rejections"], "Rejection records changed")
    decisions = (ROOT / "docs/architecture/02_DECISION_REGISTER.md").read_text(encoding="utf-8")
    old_decisions = before["docs/architecture/02_DECISION_REGISTER.md"].decode("utf-8").replace("\r\n", "\n")
    require(old_decisions.split("### D001", 1)[1].rstrip() == decisions.split("### D001", 1)[1].split("### D096", 1)[0].rstrip(), "Historical decision prose changed")
    for name, marker in (("13_GENERATOR_FEEDBACK_AND_EVALUATION.md", "# Generator Feedback and Evaluation Contract"), ("15_AGENT_INQUIRY_DISCIPLINE.md", "Source: SESSION-2026-10-24-INQUIRY")):
        path = "docs/architecture/" + name
        old = before[path].decode("utf-8").replace("\r\n", "\n")
        new = (ROOT / path).read_text(encoding="utf-8")
        require(old.split(marker, 1)[1] == new.split(marker, 1)[1], "Prior contract body changed: " + name)
    checks.update(preserved_prior_structured_decisions=len(old_register["decisions"]), preserved_contract_bodies=2)

    progress = json.loads((ROOT / PROGRESS).read_text(encoding="utf-8"))
    old_progress = json.loads(before[PROGRESS])
    checks["other_progress_keys_changed_since_baseline"] = [k for k, value in old_progress.items() if progress.get(k) != value]
    node = progress.get("metacognition_dual_space_integration", {})
    require(node.get("decision") == "D096" and node.get("runtime_activated") is False and node.get("improvement_demonstrated") is False, "Progress overstates adoption")
    require(node.get("behavioral_acceptance_cases_run_by_adoption") == 0, "Behavioral completion overclaimed")
    plan = (ROOT / PLAN).read_text(encoding="utf-8")
    require("## Metacognition and dual-space integration (November 1, 2026)" in plan, "Plan checkpoint absent")
    require("Unknown benefit does not block" in plan and "current frozen" in decisions, "Safe/incremental boundary missing")
    old_plan = before[PLAN].decode("utf-8").replace("\r\n", "\n")
    for number in range(1, 8):
        pattern = rf"^### {number}\. .*?(?=^### |^## |\Z)"
        old_package = re.search(pattern, old_plan, re.M | re.S)
        new_package = re.search(pattern, plan, re.M | re.S)
        require(old_package and new_package and old_package.group().strip() == new_package.group().strip(), f"Package {number} changed")
    checks["preserved_package_sections"] = 7

    changed_paths = baseline["edited_targets"] + [CANON]
    link_count, anchor_count = 0, 0
    for path in changed_paths:
        data = (ROOT / path).read_text(encoding="utf-8")
        require(all(line == line.rstrip() for line in data.splitlines()), "Trailing whitespace: " + path)
        if path.endswith(".json"):
            json.loads(data)
            continue
        for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", data):
            if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", link):
                continue
            relative, _, anchor = unquote(link).partition("#")
            target = ((ROOT / path).parent / relative).resolve() if relative else ROOT / path
            require(target.is_file(), f"Missing local link: {path}: {link}")
            link_count += 1
            if anchor and target.is_file() and target.suffix == ".md":
                require(anchor in headings(target.read_text(encoding="utf-8")), f"Missing anchor: {path}: {link}")
                anchor_count += 1
    checks.update(local_links=link_count, local_anchors=anchor_count, whitespace="PASS" if not any("whitespace" in e for e in errors) else "FAIL")

    unrelated = []
    for path, prior in baseline["before_sha256"].items():
        if path not in changed_paths:
            target = ROOT / path
            if not target.is_file() or digest(target.read_bytes()) != prior:
                unrelated.append(path)
    checks["other_concurrent_changes_since_baseline"] = unrelated
    diff = subprocess.run(["git", "diff", "--check", "--", *baseline["edited_targets"]], cwd=ROOT, capture_output=True, text=True)
    require(diff.returncode == 0, "git diff --check failed: " + diff.stdout + diff.stderr)
    checks["git_diff_check_exit"] = diff.returncode
    return {"status": "PASS" if not errors else "FAIL", "date": "2026-11-01", "scope": "D096 documentation adoption and user clarifications; no research runtime activation", "checks": checks, "errors": errors, "changed_files": changed_paths, "checked_files_sha256": {p: digest((ROOT / p).read_bytes()) for p in changed_paths}, "unverified": ["Runtime prompt/profile and feedback integration", "Independent behavioral qualification of AC-01 through AC-12", "Automatic improvement-review/report delivery", "Benefit, overhead tradeoff, and search-persistence effectiveness", "Scientific process calibration and economic usefulness"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    result = verify()
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered)
    raise SystemExit(0 if result["status"] == "PASS" else 1)
