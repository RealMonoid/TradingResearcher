"""Documentation integrity checks, not framework or model-comprehension tests.

Run: python docs/reviews/verify_system_model.py
Optional --baseline accepts the pre-edit path/hash inventory for this revision.
The optional inventory mode retains the original revision's CHANGED list.
Current checks also cover the additive generator contract and preserve D001-D068.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
BASE = "2ab0cbedbec47b5bdef5a520b8aa9490baa7ac63"
APPROVED_BASE = "c8c3a523a3916d7bccef7f2a63a5516ba5d34225"
CHANGED = ["AGENTS.md", "README.md"] + ["docs/architecture/" + name for name in (
    "01_PROBLEM_DEFINITION.md", "02_DECISION_REGISTER.md", "05_REQUIREMENTS.md",
    "06_MASTER_ARCHITECTURE.md", "09_IMPLEMENTATION_BLUEPRINT.md",
    "10_IMPLEMENTATION_ROADMAP.md", "11_OPEN_DECISIONS.md",
    "12_TRACEABILITY_MATRIX.md", "ARCHITECTURE_REGISTER.json", "CURRENT_STATE.md",
)]
CHECKED = CHANGED + ["docs/architecture/07_SCIENTIFIC_EVALUATION.md",
                     "docs/architecture/13_GENERATOR_FEEDBACK_AND_EVALUATION.md"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def original(rel, revision=BASE):
    return subprocess.check_output(["git", "show", revision + ":" + rel], cwd=ROOT)


def headings(path):
    counts, result = Counter(), set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^#{1,6} ", line):
            slug = re.sub(r"[^\w -]", "", re.sub(r"^#+\s+", "", line).lower()).replace(" ", "-")
            result.add(slug + (f"-{counts[slug]}" if counts[slug] else ""))
            counts[slug] += 1
    return result


def verify(baseline=None):
    errors, checks = [], {}

    def require(value, description):
        if not value:
            errors.append(description)

    docs = {p: (ROOT / p).read_text(encoding="utf-8") for p in CHECKED if p.endswith(".md")}
    links = 0
    for rel, body in docs.items():
        require(all(line == line.rstrip() for line in body.splitlines()), "Whitespace: " + rel)
        for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", body):
            if re.match(r"^[a-zA-Z][\w+.-]*:", target):
                continue
            local, _, anchor = unquote(target.strip("<>")).partition("#")
            path = ((ROOT / rel).parent / local).resolve() if local else ROOT / rel
            links += 1
            require(path.exists(), f"Missing link: {rel}: {target}")
            if anchor and path.is_file():
                require(anchor in headings(path), f"Missing anchor: {rel}: {target}")
    checks["local_links"] = links

    manifest = json.loads((ROOT / "sources/capture_manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = ROOT / "sources" / item["path"]
        require(digest(path) == item["sha256"] and path.stat().st_size == item["bytes"], "Source altered: " + item["path"])
    checks["source_files"] = len(manifest["files"])

    regpath = "docs/architecture/ARCHITECTURE_REGISTER.json"
    register = json.loads((ROOT / regpath).read_text(encoding="utf-8"))
    old = json.loads(original(regpath))
    approved = json.loads(original(regpath, APPROVED_BASE))
    require(register["decisions"][:len(approved["decisions"])] == approved["decisions"], "Approved structured decisions D001-D068 altered")
    require(register["rejections"] == old["rejections"], "Structured rejections altered")
    decision_text = docs["docs/architecture/02_DECISION_REGISTER.md"]
    old_text = original("docs/architecture/02_DECISION_REGISTER.md").decode("utf-8")
    require(decision_text.split("### D001", 1)[1].split("### D068", 1)[0].strip() == old_text.split("### D001", 1)[1].strip(), "Original decision prose altered")
    approved_text = original("docs/architecture/02_DECISION_REGISTER.md", APPROVED_BASE).decode("utf-8")
    require(decision_text.split("### D068", 1)[1].split("### D069", 1)[0].strip() == approved_text.split("### D068", 1)[1].strip(), "Approved D068 prose altered")
    for rel in ("03_REJECTED_DECISIONS.md", "04_DEFINITIONS.md"):
        require((ROOT / "docs/architecture" / rel).read_bytes() == original("docs/architecture/" + rel), "Protected document altered: " + rel)
    scientific = (ROOT / "docs/architecture/07_SCIENTIFIC_EVALUATION.md").read_bytes()
    require(scientific.startswith(original("docs/architecture/07_SCIENTIFIC_EVALUATION.md")), "Original scientific review altered")
    statuses = dict(re.findall(r"### (D\d{3})[^\n]*\n\n\*\*Status:\*\* ([A-Z_]+)", decision_text))
    require(len(statuses) == len(register["decisions"]) == len(re.findall(r"^### D\d{3} ", decision_text, re.M)), "Duplicate or missing decision IDs")
    require(statuses == {d["id"]: d["status"] for d in register["decisions"]}, "Decision status mismatch")
    counts = Counter(statuses.values())
    require(all(int(n) == counts[s] for s, n in re.findall(r"^\| ([A-Z_]+) \| (\d+) \|$", decision_text, re.M)), "Status counts mismatch")
    refs = {s["id"] for s in register["supplemental_sources"]}
    for decision in register["decisions"][len(old["decisions"]):]:
        require(set(decision["sources"]) <= refs, "Unresolved supplemental source: " + decision["id"])
    for source in register["supplemental_sources"]:
        file, _, anchor = source["record"].partition("#")
        require(anchor in headings(ROOT / "docs/architecture" / file), "Supplemental source anchor missing")
    trace = docs["docs/architecture/12_TRACEABILITY_MATRIX.md"]
    rows = [line for line in trace.splitlines() if line.startswith("| PROB-")]
    reqs = set(re.findall(r"^\| (REQ-\d{3}) \|", docs["docs/architecture/05_REQUIREMENTS.md"], re.M))
    require(reqs == set(re.findall(r"\| (REQ-\d{3}) \|", "\n".join(rows))), "Requirement trace missing")
    require(all(any(d["id"] in line and d["requirement"] in line for line in rows) for d in register["decisions"]), "Decision forward trace missing")
    require(all(re.search(r"^\| " + d["id"] + r" \| " + d["status"] + r" \|", trace, re.M) for d in register["decisions"]), "Decision reverse trace missing")
    contract = docs["docs/architecture/13_GENERATOR_FEEDBACK_AND_EVALUATION.md"]
    for number in (28, 29, 30):
        require(f"TEST-{number} / REQ-{number:03}" in contract, f"Contract acceptance specification missing: TEST-{number}")
        require(any(f"REQ-{number:03}" in row and f"TEST-{number}" in row for row in rows), f"Contract test trace missing: TEST-{number}")
    checks.update(decisions=len(statuses), preserved_original_decisions=len(old["decisions"]), preserved_approved_decisions=len(approved["decisions"]), preserved_rejections=len(old["rejections"]), traced_requirements=len(reqs), generator_acceptance_specs=3)

    graph = docs["docs/architecture/06_MASTER_ARCHITECTURE.md"].split("```mermaid\n", 1)[1].split("```", 1)[0]
    edges = defaultdict(set)
    for line in graph.splitlines()[1:]:
        match = re.fullmatch(r"\s*(\w+)(?:\[[^\]]*\]|\{[^}]*\})? -->\s*(?:\|[^|]*\|\s*)?(\w+)(?:\[[^\]]*\]|\{[^}]*\})?\s*", line)
        require(bool(match), "Unparsed diagram edge: " + line)
        if match:
            edges[match[1]].add(match[2])

    def reaches(start, end, blocked=()):
        seen, todo = set(blocked), [start]
        while todo:
            node = todo.pop()
            if node in seen:
                continue
            if node == end:
                return True
            seen.add(node)
            todo.extend(edges[node] - seen)
        return False

    for node in ("A", "GAP", "W", "E"):
        require(reaches(node, "J") and reaches(node, "K", ("S", "M", "C")), "Lost feedback branch: " + node)
        require(not reaches(node, "M", ("C", "S")), "Journal branch bypasses evaluation: " + node)
    require(reaches("S", "M") and reaches("M", "K"), "Qualified knowledge feedback missing")
    require(not reaches("OE", "M", ("C", "S")), "Operations bypass evidence authority")
    require(not reaches("IP", "C", ("V",)), "Improvement bypasses validation/approval")
    checks["diagram_edges"] = sum(len(v) for v in edges.values())
    checks["diagram_check_scope"] = "Edge structure and routing, not Mermaid rendering or executable scientific semantics"

    if baseline:
        before = json.loads(Path(baseline).read_text(encoding="utf-8"))
        changed = {p for p, h in before.items() if not (ROOT / p).is_file() or digest(ROOT / p) != h}
        require(changed == set(CHANGED), "Unexpected existing-file changes: " + repr(sorted(changed)))
        checks["preexisting_files_unchanged"] = len(before) - len(changed)
    else:
        checks["preexisting_file_inventory"] = "Not checked; rerun with retained --baseline inventory"
    diff = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True)
    require(diff.returncode == 0, diff.stdout + diff.stderr)
    checks["git_diff_check_exit"] = diff.returncode
    return {"status": "PASS" if not errors else "FAIL", "checks": checks, "checked_files_sha256": {p: digest(ROOT / p) for p in CHECKED}, "errors": errors, "unverified": ["New-session behavioral efficacy and compaction retention", "Mermaid rendering", "Framework runtime, TEST-01 through TEST-30, calibration, profitability and speed improvement"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = verify(args.baseline)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    raise SystemExit(0 if result["status"] == "PASS" else 1)
