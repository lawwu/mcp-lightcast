"""Build the reference directly from registered tools, without any API requests."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path


def generate_reference():
    from mcp_lightcast.server import mcp

    tools = asyncio.run(mcp.get_tools())
    lines = [
        "# MCP tool reference",
        "",
        f"**{len(tools)} tools, generated from the running server’s schemas.** This page rebuilds with every documentation deployment.",
        "",
        "All tools query external Lightcast services. They are read-only, but may consume your subscription quota. Premium API permissions are independent of basic taxonomy access.",
        "",
    ]
    groups = {}
    for name, tool in tools.items():
        category = sorted(tool.tags)[0] if tool.tags else "other"
        groups.setdefault(category, []).append((name, tool))
    for group, entries in sorted(groups.items()):
        lines += [f"## {group.title()}", ""]
        for name, tool in sorted(entries):
            schema = tool.parameters
            lines += [
                f"### `{name}`",
                "",
                tool.description or "",
                "",
                "| Parameter | Required | Default |",
                "| --- | --- | --- |",
            ]
            for key, prop in schema.get("properties", {}).items():
                default = (
                    json.dumps(prop["default"], ensure_ascii=False)
                    if "default" in prop
                    else "—"
                )
                lines.append(
                    f"| `{key}` | {'Yes' if key in schema.get('required', []) else 'No'} | `{default}` |"
                )
            if not schema.get("properties"):
                lines.append("| No parameters | — | — |")
            lines += ["", '??? info "Full input schema"', "", "    ```json"]
            lines += [
                "    " + line for line in json.dumps(schema, indent=2).splitlines()
            ]
            lines += ["    ```", ""]
    dest = Path(__file__).resolve().parent.parent / "docs" / "reference" / "tools.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines) + "\n"
    if not dest.exists() or dest.read_text() != content:
        dest.write_text(content)


if __name__ == "__main__":
    generate_reference()
    raise SystemExit(
        subprocess.call(
            ["zensical", *(sys.argv[1:] or ["serve"])],
            cwd=Path(__file__).resolve().parent.parent,
        )
    )
