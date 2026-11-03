"""Implementation-scope preservation and local documentation checks."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
ALLOWED = {
    # D101: explicit full adoption of the contextual methodology on November 3.
    # These four additional owners receive append-only canonical clarifications;
    # existing policy/source preservation is checked by the current doc gates.
    'docs/architecture/01_PROBLEM_DEFINITION.md',
    'docs/architecture/07_SCIENTIFIC_EVALUATION.md',
    'docs/architecture/08_ENGINEERING_REVIEW.md',
    'docs/architecture/11_OPEN_DECISIONS.md',
    'AGENTS.md',  # October 31 user-approved compact construction/session instructions.
    # D089: explicit October29 approval of the bounded median/log specification.
    'docs/architecture/02_DECISION_REGISTER.md', 'docs/architecture/ARCHITECTURE_REGISTER.json',
    'docs/architecture/04_DEFINITIONS.md', 'docs/architecture/05_REQUIREMENTS.md',
    'docs/architecture/12_TRACEABILITY_MATRIX.md',
    'docs/architecture/13_GENERATOR_FEEDBACK_AND_EVALUATION.md',  # D096: user-approved addendum; original body checked by adoption verifier.
    'docs/architecture/06_MASTER_ARCHITECTURE.md',  # Exact approved bytes: adoption-metacognition-2026-11-01/verification.json.
    'docs/architecture/15_AGENT_INQUIRY_DISCIPLINE.md',  # Exact approved bytes: diagnosis-practice-adoption-2026-11-01/verification.json.
    '.gitattributes',  # Preserve runtime/evidence bytes in the authorized GitHub publication.
    'docs/reviews/verify_retail_contract.py',  # Record that explicit later publication scope.
    '.gitignore', 'README.md', 'docs/architecture/09_IMPLEMENTATION_BLUEPRINT.md',
    'docs/architecture/CURRENT_STATE.md', 'tests/test_local_runtime.py',
    'trading_researcher/__main__.py', 'trading_researcher/checks.py', 'trading_researcher/coordination.py',
    'trading_researcher/README.md',  # Authorized storage/replay capability and backup instructions.
    'docs/reviews/integration-research-2026-10-24/IMPLEMENTATION_SEQUENCE_2026-10-25.md',
    'docs/reviews/integration-research-2026-10-24/INTEGRATION_PROPOSAL.md',  # October 26 user-requested dated risk addendum; original text preserved.
}


def check():
    baseline = json.loads((AUDIT / 'baseline.json').read_text(encoding='utf-8'))['files_sha256']
    errors, changed = [], []
    for name, expected in baseline.items():
        path = ROOT / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            changed.append(name)
            if name not in ALLOWED:
                errors.append('Unplanned baseline change: ' + name)
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'],
                                        cwd=ROOT, text=True).splitlines()
    documents = sorted({name for name in changed + untracked if name.endswith('.md')})
    count = 0
    for name in documents:
        path = ROOT / name
        content = path.read_text(encoding='utf-8')
        for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', content):
            if re.match(r'^[a-z]+:', target, flags=re.IGNORECASE) or target.startswith('#'):
                continue
            target = unquote(target.split('#', 1)[0])
            if target and not (path.parent / target).exists():
                errors.append(f'Broken local link: {name}: {target}')
            count += 1
    for name in sorted(set(changed + untracked)):
        if not name.endswith(('.py', '.md', '.json')):
            continue
        path = ROOT / name
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if line.rstrip() != line:
                errors.append(f'Trailing whitespace: {name}:{number}')
    return {'status': 'FAIL' if errors else 'PASS', 'baseline_files': len(baseline),
            'unchanged_files': len(baseline) - len(changed), 'changed_files': changed,
            'new_files': untracked, 'local_document_links': count, 'errors': errors,
            'scope': 'Implementation preservation, local link targets and whitespace; no semantic/scientific certification'}


if __name__ == '__main__':
    result = check()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
