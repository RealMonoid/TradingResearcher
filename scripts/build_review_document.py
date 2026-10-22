"""Build a deterministic, uncompressed reading copy of the architecture.

Run with --check to detect a stale copy. Original documents remain authoritative.
"""

import argparse
import hashlib
from pathlib import Path
import posixpath
import re

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "review/README.md"
FILES = ["REVIEWING.md", "README.md", "AGENTS.md", "docs/architecture/CURRENT_STATE.md"] + [
    p.relative_to(ROOT).as_posix()
    for p in sorted((ROOT / "docs/architecture").glob("[0-9][0-9]_*.md"))
]


def relocate_links(text, source):
    """Keep Markdown links pointing to their original repository destinations."""
    def replace(match):
        label, target = match.groups()
        if re.match(r"^[a-zA-Z][\w+.-]*:", target) or target.startswith("/"):
            return match[0]
        local, separator, anchor = target.partition("#")
        dest = posixpath.normpath(posixpath.join(posixpath.dirname(source), local)) if local else source
        return f"[{label}](../{dest}{separator}{anchor})"

    lines, fence = [], None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            lines.append(line)
        elif fence:
            lines.append(line)
        else:
            lines.append(re.sub(r"\[([^\]\n]+)\]\(([^)\n]+)\)", replace, line))
    return "".join(lines)


def build():
    assert len(FILES) == 17, "Review the export scope when architecture files change"
    parts = [
        "# TradingResearcher: complete architecture reading copy\n\n",
        "This is an uncompressed Markdown document for readers that cannot import the GitHub repository or follow multiple file links. Read the reviewer instructions below before assessing the framework.\n\n",
        "Generated from the 17 files listed below; their full text is included, not summarized. Only relative Markdown links outside code blocks are relocated to their original repository destinations. Each source SHA-256 identifies the original bytes. The original files govern; do not edit this generated copy. Rebuild with `python scripts/build_review_document.py`; check freshness with `python scripts/build_review_document.py --check`.\n\n",
        "Scope: reviewer instructions, repository overview/instructions, current state, and all architecture documents 00-12. The original conversation archive, structured JSON companions, source review index and historical verification artifacts remain separate linked files. Do not claim to have inspected those from this copy; source disputes require the relevant original material. The framework has no application implementation.\n\n",
        "This generated distribution file intentionally exceeds 1,000 lines to allow single-page retrieval. Maintain the separate source documents; splitting this copy would defeat that access purpose.\n\n",
        "If your retrieval stops before `END OF COMPLETE ARCHITECTURE READING COPY`, report truncation and withhold a whole-framework verdict. Seeing that marker alone does not prove that every section was processed.\n\n",
        "## Included sources\n\n| File | SHA-256 of source bytes |\n|---|---|\n",
    ]
    bodies = []
    for source in FILES:
        raw = (ROOT / source).read_bytes()
        text = raw.decode("utf-8")
        parts.append(f"| [{source}](../{source}) | `{hashlib.sha256(raw).hexdigest()}` |\n")
        bodies.append(f"\n---\n\n## Source file: {source}\n\n" + relocate_links(text, source).rstrip("\n") + "\n")
    parts.extend(bodies)
    parts.append("\n---\n\nEND OF COMPLETE ARCHITECTURE READING COPY\n")
    return "".join(parts).encode("utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = build()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            raise SystemExit("FAIL: review/README.md is missing or stale")
        print(f"PASS: 17 complete source files; {len(expected)} output bytes; exact regeneration match")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(expected)
        print(f"Wrote {OUTPUT}: 17 complete source files; {len(expected)} bytes")
