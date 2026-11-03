"""Verify approved specification integration, not application/scientific behavior.

Run with python -B to avoid generating cache artifacts in the review directory.
The immutable preapproval inventory measures this adoption, including prior edits.
Explicit later approvals may add changed paths; original policy checks remain scoped.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import zipfile

from verify_system_model import ROOT, verify


FOLDER = ROOT / "docs/reviews/adoption-2026-10-23"
EXPECTED_CHANGED = {
    "AGENTS.md", "README.md", "docs/reviews/verify_system_model.py",
    *["docs/architecture/" + name for name in (
        "01_PROBLEM_DEFINITION.md", "02_DECISION_REGISTER.md", "04_DEFINITIONS.md",
        "05_REQUIREMENTS.md", "06_MASTER_ARCHITECTURE.md", "07_SCIENTIFIC_EVALUATION.md",
        "08_ENGINEERING_REVIEW.md", "09_IMPLEMENTATION_BLUEPRINT.md",
        "10_IMPLEMENTATION_ROADMAP.md", "11_OPEN_DECISIONS.md",
        "12_TRACEABILITY_MATRIX.md", "13_GENERATOR_FEEDBACK_AND_EVALUATION.md",
        "ARCHITECTURE_REGISTER.json", "CURRENT_STATE.md",
    )],
}
ADDED = [
    "docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md",
    "docs/reviews/verify_retail_contract.py",
    "docs/reviews/adoption-2026-10-23/baseline.json",
    "docs/reviews/adoption-2026-10-23/preapproval-documents.zip",
    "docs/reviews/adoption-2026-10-23/verification.json",
]
LATER_APPROVED_CHANGED = {
    "REVIEWING.md": "D086 / agent-inquiry/1.0",
    ".gitattributes": "October 26 explicit GitHub publication: preserve exact runtime, fixture and evidence bytes",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def normalized(data):
    return data.decode("utf-8").replace("\r\n", "\n")


def decision_blocks(text):
    return dict(re.findall(r"^### (D\d{3}) (.*?)(?=^### D\d{3} |\Z)", text, re.M | re.S))


PRIVATE_USE_CLARIFICATION = (
    "**Private-use construction clarification (user approval, November 3, 2026):** for this user'"
    's private data-source selection and integration work, rights clearance is not an assistant-i'
    'mposed prerequisite. Apply the [explicit instruction and approval](../reviews/integration-re'
    'search-2026-10-24/IMPLEMENTATION_SEQUENCE_2026-10-25.md#private-use-data-source-instruction-'
    'november-3-2026); retain already-recorded rights/use observations as descriptive history rat'
    'her than reopening clearance work or requests. This operational clarification does not relab'
    'el provider terms, change frozen research-contract/1.0 profiles or waive data quality, histo'
    'rical availability, exposure, scientific admission, costs or execution requirements.'
)


def original_contract_bytes(data):
    """Remove only the explicitly approved construction addendum, byte-exactly.

    This preserves the complete original contract for its existing baseline and
    scientific-policy checks; no other paragraph or policy edit is exempted.
    """
    marker = PRIVATE_USE_CLARIFICATION.encode('utf-8')
    if marker not in data:
        return data
    record = json.loads((ROOT / 'docs/reviews/implementation-2026-10-25/data-candidate-review-2026-11-03.json').read_text(encoding='utf-8'))
    approval = record['private_use_instruction']
    if (approval['source'] != 'SESSION-2026-11-03-PRIVATE-DATA-USE'
            or approval['explicit_followup_approval'] != 'freigabe'
            or data.count(marker) != 1):
        raise ValueError('Exact private-use construction approval required')
    ending = b'\r\n' if marker + b'\r\n\r\n' in data else b'\n'
    block = marker + ending * 2
    if data.count(block) != 1:
        raise ValueError('Exact private-use construction paragraph boundary required')
    return data.replace(block, b'', 1)


def validate():
    result = verify()
    errors = result["errors"]
    checks = result["checks"]

    def require(condition, message):
        if not condition:
            errors.append(message)

    baseline = json.loads((FOLDER / "baseline.json").read_text(encoding="utf-8"))
    changed = sorted(p for p, h in baseline.items()
                     if not (ROOT / p).is_file() or sha((ROOT / p).read_bytes()) != h)
    require(set(changed) == EXPECTED_CHANGED | set(LATER_APPROVED_CHANGED),
            "Unexpected changes since adoption baseline: " + repr(changed))
    checks["later_approved_changed_paths"] = LATER_APPROVED_CHANGED
    for path in ADDED:
        require((ROOT / path).is_file(), "Missing adoption artifact: " + path)
    checks["adoption_baseline_files"] = len(baseline)
    checks["preexisting_files_unchanged"] = len(baseline) - len(changed)
    checks["preexisting_file_inventory"] = "Checked against this adoption's preapproval inventory"
    with zipfile.ZipFile(FOLDER / "preapproval-documents.zip") as archive:
        require(archive.testzip() is None, "Preapproval archive CRC failure")
        for name in archive.namelist():
            require(sha(archive.read(name)) == baseline[name], "Preapproval archive mismatch: " + name)
        checks["archived_documents_exact"] = len(archive.namelist())
        regpath = "docs/architecture/ARCHITECTURE_REGISTER.json"
        before = json.loads(archive.read(regpath))
        after = json.loads((ROOT / regpath).read_text(encoding="utf-8"))
        require(after["decisions"][:70] == before["decisions"], "D001-D070 structured history changed")
        require(after["rejections"] == before["rejections"], "Rejection records changed")
        rel = "docs/architecture/02_DECISION_REGISTER.md"
        old_blocks = decision_blocks(normalized(archive.read(rel)))
        new_blocks = decision_blocks((ROOT / rel).read_text(encoding="utf-8"))
        require(all(new_blocks[k].strip() == v.strip() for k, v in old_blocks.items()),
                "Historical decision prose D001-D070 changed")
        checks["preserved_preapproval_decisions"] = len(old_blocks)
        for name in ("04_DEFINITIONS.md", "07_SCIENTIFIC_EVALUATION.md",
                     "13_GENERATOR_FEEDBACK_AND_EVALUATION.md"):
            rel = "docs/architecture/" + name
            require(normalized(archive.read(rel)).strip() in (ROOT / rel).read_text(encoding="utf-8"),
                    "Historical full text not retained: " + name)
        checks["full_historical_definition_review_generator_texts"] = 3

    contract_path = ROOT / "docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md"
    contract = contract_path.read_text(encoding="utf-8")
    proposal_path = ROOT / "docs/reviews/RETAIL_RESEARCH_CONTRACT_PROPOSAL_2026-10-23.md"
    proposal = proposal_path.read_text(encoding="utf-8")
    body = "## 1. OPEN-01:" + proposal.split("## 1. OPEN-01:", 1)[1].split(
        "## Integration, implementation and rollback plan", 1)[0]
    # Only approval-status words change between proposed and adopted policies.
    substitutions = [
        ("Propose `historical-batch-v1`", "Adopt `historical-batch-v1`"),
        ("Proposed demonstration profiles", "Approved demonstration profiles"),
        ("**Decision:** propose a first research profile", "**Decision:** adopt a first research profile"),
        ("Proposed pilot ceiling", "Approved pilot ceiling"),
        ("these proposed limits", "these approved limits"),
        ("Proposed observable criterion", "Approved observable criterion"),
        ("Proposed substantial-improvement target", "Approved substantial-improvement target"),
        ("scoped engineering choices requiring approval", "scoped engineering choices approved with this contract"),
    ]
    for old, new in substitutions:
        body = body.replace(old, new)
    try:
        original_contract = original_contract_bytes(contract.encode('utf-8')).decode('utf-8')
    except (KeyError, ValueError, OSError) as exc:
        require(False, 'Unqualified construction clarification: ' + str(exc))
        original_contract = contract
    checks['private_use_construction_clarification_exact'] = original_contract != contract
    actual = "## 1. OPEN-01:" + original_contract.split("## 1. OPEN-01:", 1)[1].split(
        "## Versioning, migration and rollback", 1)[0]
    require(actual.strip() == body.strip(), "Adopted scientific policy differs from approved proposal")
    require("> Freigabe" in contract and "SESSION-2026-10-23-CLOSURE" in contract,
            "Approval provenance missing")
    checks["approved_policy_sections_exact_except_status_words"] = len(
        re.findall(r"^## \d+\. OPEN-\d+: ", actual, re.M))
    require(checks["approved_policy_sections_exact_except_status_words"] == 15,
            "Contract section count differs")

    expected_open = [f"OPEN-{n:02}" for n in range(1, 16)]
    require([r["open_id"] for r in after["decision_resolutions"]] == expected_open,
            "Structured open resolution coverage mismatch")
    open_text = (ROOT / "docs/architecture/11_OPEN_DECISIONS.md").read_text(encoding="utf-8")
    trace = (ROOT / "docs/architecture/12_TRACEABILITY_MATRIX.md").read_text(encoding="utf-8")
    for n, oid in enumerate(expected_open, 1):
        did = f"D{70+n:03}"
        disposition = (f"| {oid} | {did}; contract section {n}; D087 invocation extension |"
                       if n == 13 else f"| {oid} | {did}; contract section {n} |")
        require(disposition in open_text, "Missing open disposition: " + oid)
        require(f"| {n} / {did} | TEST-" in trace, "Missing closure acceptance trace: " + oid)
        resolution = after["decision_resolutions"][n-1]
        require(resolution["adopted_by"] == did and resolution["section"] == n,
                "Incorrect resolution binding: " + oid)
    adopted_decisions = after["decisions"][:85]
    counts = Counter(d["status"] for d in adopted_decisions)
    require([d["id"] for d in adopted_decisions] == [f"D{n:03}" for n in range(1, 86)]
            and counts["ACCEPTED"] == 63,
            "Adoption decision counts mismatch")
    checks["scoped_open_dispositions_and_acceptance_mappings"] = 15
    checks["adoption_decision_status_counts_D001_D085"] = dict(counts)
    checks["decision_status_counts"] = dict(Counter(d["status"] for d in after["decisions"]))

    for name, stale in [("AGENTS.md", "remain unapproved semantic proposals"),
                        ("README.md", "awaiting explicit scientific approval"),
                        ("docs/architecture/CURRENT_STATE.md", "Scientific adoption is awaiting")]:
        require(stale not in (ROOT / name).read_text(encoding="utf-8"), "Stale active authority: " + name)
    result["status"] = "PASS" if not errors else "FAIL"
    result["changed_files_since_preapproval"] = changed
    result["added_files"] = ADDED
    result["preserved_proposal_sha256"] = sha(proposal_path.read_bytes())
    result["preapproval_archive_sha256"] = sha((FOLDER / "preapproval-documents.zip").read_bytes())
    result["checked_files_sha256"].update({p: sha((ROOT / p).read_bytes())
                                          for p in changed + ADDED if not p.endswith("verification.json")})
    result["unverified"] += [
        "Complete executable AST/schema/primitive implementations and independent golden fixtures",
        "Actual data quality, rights, historical availability, model exposure and account/execution costs",
        "Pinned research-runtime/backend compatibility, licensing, full model isolation, scientific registry/blob crash recovery and restore; local coordination recovery is tested separately",
        "Bootstrap marginal coverage, full-process calibration and economic opportunity/risk inputs",
        "SRC-001 through SRC-008 and completeness of original conversation",
    ]
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    report = validate()
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    raise SystemExit(0 if report["status"] == "PASS" else 1)
