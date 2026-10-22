"""Check this instruction review's artifacts; this is not a framework test suite.

Run from any directory with Python's standard library:
    python docs/reviews/session-understanding/verify.py --snapshots
Omit --snapshots when the temporary experiment snapshots are no longer available.
Behavioral grading remains a separate, explicitly manual review.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHANGED = {"AGENTS.md", "docs/architecture/CURRENT_STATE.md"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def heading_ids(path):
    ids = set()
    counts = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^#{1,6} ", line):
            continue
        heading = re.sub(r"^#+\s+", "", line).strip().lower()
        slug = re.sub(r"[^\w\- ]", "", heading).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        ids.add(slug if not count else f"{slug}-{count}")
    return ids


def verify(include_snapshots):
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    protocol = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
    failures = []
    checks = {}

    def require(condition, message):
        if not condition:
            failures.append(message)

    require(digest(HERE / "protocol.json") == manifest["protocol_sha256"], "Frozen protocol changed")
    modified = []
    for rel, before in manifest["before_sha256"].items():
        if not (ROOT / rel).exists() or digest(ROOT / rel) != before:
            modified.append(rel)
    require(set(modified) == CHANGED, f"Unexpected pre-existing file changes: {modified}")
    checks["pre_existing_changed_files"] = modified
    checks["unchanged_pre_existing_files"] = len(manifest["before_sha256"]) - len(modified)
    for rel, expected in manifest.get("final_tested_instruction_sha256", manifest["tested_instruction_sha256"]).items():
        require(digest(ROOT / rel) == expected, f"Final file differs from tested instruction snapshot: {rel}")

    source = json.loads((ROOT / "sources/capture_manifest.json").read_text(encoding="utf-8"))
    for item in source["files"]:
        path = ROOT / "sources" / item["path"]
        require(path.stat().st_size == item["bytes"] and digest(path) == item["sha256"], f"Source mismatch: {item['path']}")
    checks["archived_source_files_checked"] = len(source["files"])

    authored = [ROOT / "AGENTS.md", ROOT / "docs/architecture/CURRENT_STATE.md", HERE / "README.md"]
    links = 0
    for path in authored:
        content = path.read_text(encoding="utf-8")
        require(all(line == line.rstrip() for line in content.splitlines()), f"Trailing whitespace: {path.name}")
        for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", content):
            if re.match(r"^[a-zA-Z][\w+.-]*:", target):
                continue
            local, _, anchor = unquote(target.strip("<>")).partition("#")
            destination = (path.parent / local).resolve() if local else path
            links += 1
            require(destination.exists(), f"Broken local link in {path.name}: {target}")
            if anchor and destination.exists():
                require(anchor in heading_ids(destination), f"Missing anchor in {path.name}: {target}")
    checks["local_links_checked"] = links
    whitespace = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True)
    require(whitespace.returncode == 0, f"git diff --check: {whitespace.stdout}{whitespace.stderr}")
    checks["git_diff_check_exit"] = whitespace.returncode
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
    require(all(p.startswith("docs/reviews/session-understanding/") for p in untracked), f"Unexpected untracked files: {untracked}")

    expected_pairs = {(t["id"], c) for t in protocol["tasks"] for c in ("baseline", "revised")}
    actual_pairs = {(r["task"], r["condition"]) for r in manifest["schedule"]}
    require(len(manifest["schedule"]) == 10 and actual_pairs == expected_pairs, "Incomplete/duplicate task schedule")
    retests = manifest.get("retest_schedule", [])
    if retests:
        require(digest(HERE / "protocol-v2.json") == manifest["protocol_v2_sha256"], "Frozen v2 protocol changed")
        repair = json.loads((HERE / "protocol-v2.json").read_text(encoding="utf-8"))
        require(repair["tasks"] == protocol["tasks"] and repair["critical_errors"] == protocol["critical_errors"], "Repair changed the task criteria")
        require(len(retests) == 5 and {r["task"] for r in retests} == {t["id"] for t in protocol["tasks"]}, "Incomplete/duplicate repair task schedule")
    runs = manifest["schedule"] + retests
    for run in runs:
        expected_input = dict(manifest["before_sha256"])
        if run["condition"] == "revised":
            version = "final_tested_instruction_sha256" if run in retests else "tested_instruction_sha256"
            expected_input.update(manifest[version])
        require(run["input_sha256"] == expected_input, f"Unexpected condition differences: {run['run_id']}")
        response = HERE / "responses" / (run["run_id"] + ".md")
        require(response.exists(), f"Missing response: {run['run_id']}")
        if response.exists() and "response_sha256" in run:
            require(digest(response) == run["response_sha256"], f"Changed response: {run['run_id']}")
        else:
            require(False, f"Response not frozen: {run['run_id']}")
    checks["behavioral_responses_checked"] = len(runs)

    if include_snapshots:
        original_readme = (Path(manifest["experiment_dir"]) / "baseline/README.md").read_bytes()
        edited_readme = original_readme.replace(b"Source audit and known gaps", b"Source audit and documented gaps")
        for run in runs:
            folder = Path(run["snapshot"])
            actual_files = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
            require(actual_files == set(run["input_sha256"]), f"Unexpected snapshot files: {run['run_id']}")
            for rel, expected in run["input_sha256"].items():
                path = folder / rel
                if rel == "README.md" and run["task"] == "local_edit":
                    require(path.read_bytes() == edited_readme, f"Incorrect local edit: {run['run_id']}")
                else:
                    require(path.exists() and digest(path) == expected, f"Unauthorized snapshot mutation: {run['run_id']}/{rel}")
        checks["isolated_snapshot_mutation_audits"] = len(runs)
    else:
        checks["isolated_snapshot_mutation_audits"] = "not requested; historical results only"

    if (HERE / "assessment.json").exists():
        assessment = json.loads((HERE / "assessment.json").read_text(encoding="utf-8"))
        require(len(assessment["runs"]) == len(runs), "Assessment run count mismatch")
        for name, expected_hash in assessment["reviewer_outputs"].items():
            require(digest(HERE / name) == expected_hash, f"Changed reviewer output: {name}")
        final = assessment["summary"][-1]
        checks["manual_behavioral_assessment"] = {
            "status": assessment["final_status"],
            "tasks_passed": final["tasks_passed"],
            "tasks_total": final["tasks_total"],
            "criteria_passed": final["criteria_passed"],
            "criteria_total": final["criteria_total"],
            "all_task_gate_met": assessment["final_behavioral_acceptance_met"],
        }

    artifacts = authored + [HERE / "protocol.json", HERE / "manifest.json", Path(__file__).resolve()]
    if retests:
        artifacts.append(HERE / "protocol-v2.json")
    for name in ("grading-v1.json", "grading-v2.json", "assessment.json"):
        if (HERE / name).exists():
            artifacts.append(HERE / name)
    checks["checked_artifact_sha256"] = {p.relative_to(ROOT).as_posix(): digest(p) for p in artifacts}
    return {"status": "passed" if not failures else "failed", "scope": "static integrity and snapshot mutation checks", "checks": checks, "failures": failures,
            "boundary": "Static integrity and isolated edit checks only. Behavioral correctness is manually scored; no scientific framework capability is validated."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", action="store_true")
    args = parser.parse_args()
    result = verify(args.snapshots)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "passed" else 1)
