#!/usr/bin/env python3
"""Use pinned CodeBurn for local read-only cost reporting, or install its runtime."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("install", "version", "doctor", "today", "week"), default="doctor", nargs="?")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    runtime = root / "tools/codeburn-runtime"
    if args.command == "install":
        npm = shutil.which("npm")
        if not npm:
            parser.error("npm and a compatible Node.js are required")
        command = [npm, "--prefix", str(runtime), "--cache", str(root / ".npm-cache"),
                   "ci", "--ignore-scripts", "--no-audit", "--no-fund"]
        raise SystemExit(subprocess.run(command, cwd=root).returncode)
    package = runtime / "node_modules/codeburn/package.json"
    if not package.is_file():
        parser.error("Runtime is missing. Set up once with: python3 tools/codeburn.py install")
    if json.loads(package.read_text(encoding="utf-8"))["version"] != "0.9.27":
        parser.error("Unexpected CodeBurn version; reinstall from the committed lock file")
    node = shutil.which("node")
    if not node:
        parser.error("Node.js is required")
    commands = {
        "version": ["--version"],
        "doctor": ["doctor", "--json"],
        "today": ["today", "--format", "json"],
        "week": ["report", "--period", "week", "--format", "json"],
    }
    env = {**os.environ, "CODEBURN_CURSOR_SYNC": "0", "DO_NOT_TRACK": "1", "NO_COLOR": "1"}
    command = [node, str(runtime / "node_modules/codeburn/dist/cli.js"), *commands[args.command]]
    raise SystemExit(subprocess.run(command, cwd=root, env=env).returncode)


if __name__ == "__main__":
    main()
