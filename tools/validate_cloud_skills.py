#!/usr/bin/env python3
"""Check migrated skill files, metadata, local Markdown links and Python syntax."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


def markdown_prose(text):
    """Blank fenced/inline code while keeping line numbers for template examples."""
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            if fence is None:
                fence = marker.group(1)[0]
            elif marker.group(1)[0] == fence:
                fence = None
            lines.append("\n" if line.endswith("\n") else "")
        elif fence:
            lines.append("\n" if line.endswith("\n") else "")
        else:
            lines.append(re.sub(r"`[^`\n]+`", "", line))
    return "".join(lines)


def validate(root):
    skills_root = root / ".agents/skills"
    manifest = json.loads((root / "migration/manifest.json").read_text(encoding="utf-8"))
    expected_names = set(manifest["skills"])
    actual_names = {p.parent.name for p in skills_root.glob("*/SKILL.md")}
    errors = []
    if expected_names != actual_names or len(actual_names) != 41:
        errors.append({"kind": "skill-set-mismatch"})
    for skill in sorted(actual_names):
        path = skills_root / skill / "SKILL.md"
        text = path.read_text(encoding="utf-8-sig")
        parts = re.split(r"^---\s*$", text, maxsplit=2, flags=re.M)
        if len(parts) != 3 or parts[0].strip():
            errors.append({"kind": "frontmatter", "path": str(path.relative_to(root))})
            continue
        name = re.search(r"^name:\s*([^\r\n]+)", parts[1], re.M)
        description = re.search(r"^description:\s*([^\r\n]+)", parts[1], re.M)
        if not name or name.group(1).strip(" '\"") != skill:
            errors.append({"kind": "name", "path": str(path.relative_to(root))})
        if not description or not description.group(1).strip(" '\""):
            errors.append({"kind": "description", "path": str(path.relative_to(root))})

    actual_files = {str(p.relative_to(root)) for p in skills_root.rglob("*") if p.is_file()}
    expected_files = {f["path"] for f in manifest["files"]}
    if actual_files != expected_files:
        errors.append({"kind": "file-set-mismatch", "missing": sorted(expected_files - actual_files),
                       "extra": sorted(actual_files - expected_files)})
    for entry in manifest["files"]:
        path = root / entry["path"]
        if not path.is_file():
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            errors.append({"kind": "hash-mismatch", "path": entry["path"]})

    links_checked = 0
    python_checked = 0
    for path in sorted(skills_root.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        if path.suffix == ".py":
            python_checked += 1
            try:
                compile(path.read_bytes(), rel, "exec")
            except (SyntaxError, ValueError) as exc:
                errors.append({"kind": "python-syntax", "path": rel, "line": getattr(exc, "lineno", None)})
        if path.suffix != ".md":
            continue
        prose = markdown_prose(path.read_text(encoding="utf-8-sig"))
        for match in re.finditer(r"!?\[[^\]\n]*\]\(([^)\n]+)\)", prose):
            target = match.group(1).split(' "')[0].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            if any(c in target for c in ("{", "}", "*", "$", "<", ">")):
                continue
            links_checked += 1
            dest = path.parent / unquote(parsed.path)
            if not dest.exists():
                errors.append({"kind": "missing-local-link", "path": rel,
                               "line": prose.count("\n", 0, match.start()) + 1, "target": target})

    return {
        "skills_checked": len(actual_names), "files_checked": len(actual_files),
        "python_files_syntax_checked": python_checked, "local_markdown_links_checked": links_checked,
        "errors": errors,
        "limits": "No remote URLs, anchors, model routing, authentication or workflow behavior tested. "
                  "Fenced generation examples are excluded from local-link checks. "
                  "Secret/privacy review is documented separately in SKILLS-MIGRATION.md.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.root.resolve())
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    raise SystemExit(bool(result["errors"]))


if __name__ == "__main__":
    main()
