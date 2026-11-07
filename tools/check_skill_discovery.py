#!/usr/bin/env python3
"""Ask the installed Codex app server to list skills; never start a model turn."""
import argparse
import asyncio
import json
from pathlib import Path


async def check(cwd: Path) -> dict:
    process = await asyncio.create_subprocess_exec(
        "codex", "app-server", "--stdio",
        cwd=cwd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    async def rpc(request: dict) -> dict:
        process.stdin.write((json.dumps(request) + "\n").encode())
        await process.stdin.drain()
        while True:
            line = await asyncio.wait_for(process.stdout.readline(), timeout=30)
            if not line:
                raise RuntimeError("Codex app server closed before replying")
            reply = json.loads(line)
            if reply.get("id") == request["id"]:
                if "error" in reply:
                    raise RuntimeError("App-server RPC failed: " + str(reply["error"].get("code")))
                return reply["result"]

    try:
        await rpc({"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "skills-migration-check", "version": "1.0"},
            "capabilities": {"experimentalApi": True},
        }})
        process.stdin.write(b'{"method":"initialized"}\n')
        await process.stdin.drain()
        response = await rpc({"id": 2, "method": "skills/list", "params": {
            "cwds": [str(cwd)], "forceReload": True,
        }})
        expected = {p.parent.name for p in (cwd / ".agents/skills").glob("*/SKILL.md")}
        items = response.get("data", [])
        local = [s for item in items for s in item.get("skills", [])
                 if str(s.get("path", "")).startswith(str(cwd / ".agents/skills") + "/")]
        discovered = {s["name"] for s in local}
        errors = [e for item in items for e in item.get("errors", [])]
        return {
            "method": "skills/list", "cwd": str(cwd),
            "expected_count": len(expected), "discovered_count": len(discovered),
            "skills": sorted(discovered), "missing": sorted(expected - discovered),
            "disabled": sorted(s["name"] for s in local if not s.get("enabled", True)),
            "errors": errors,
            "note": "Fresh app-server metadata scan; no model turn or current-chat reload.",
        }
    finally:
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = asyncio.run(check(args.root.resolve()))
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if result["missing"] or result["errors"] or result["disabled"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
