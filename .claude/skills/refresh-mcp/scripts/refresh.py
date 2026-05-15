#!/usr/bin/env python3
"""刷新 MCP Gateway 工具摘要到 CLAUDE.md。

用法: python3 refresh.py <project_root>
"""
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

API_URL = "http://localhost:8000/api/tools/summary"
START = "<!-- MCP_GATEWAY_TOOLS_START -->"
END = "<!-- MCP_GATEWAY_TOOLS_END -->"


def fetch_summary() -> str:
    try:
        with urlopen(API_URL, timeout=5) as resp:
            return resp.read().decode()
    except (URLError, OSError) as e:
        print(f"错误：无法连接 MCP Gateway（{API_URL}）\n{e}", file=sys.stderr)
        sys.exit(1)


def update_claude_md(claude_md: Path, summary: str) -> None:
    if summary.strip():
        block = f"{START}\n\n## MCP Gateway 可用工具\n\n{summary}\n\n{END}"
    else:
        block = f"{START}\n\n暂无已连接的 MCP Server。\n\n{END}"

    content = claude_md.read_text() if claude_md.exists() else ""

    start_idx = content.find(START)
    end_idx = content.find(END)

    if start_idx != -1 and end_idx != -1:
        end_idx += len(END)
        if end_idx < len(content) and content[end_idx] == "\n":
            end_idx += 1
        content = content[:start_idx] + block + "\n" + content[end_idx:]
    else:
        if content and not content.endswith("\n"):
            content += "\n"
        content += "\n" + block + "\n"

    claude_md.write_text(content)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 refresh.py <project_root>", file=sys.stderr)
        sys.exit(1)

    project_root = Path(sys.argv[1])
    claude_md = project_root / "CLAUDE.md"
    summary = fetch_summary()
    update_claude_md(claude_md, summary)

    tool_count = summary.count("\n  ") if summary.strip() else 0
    print(f"已刷新 {tool_count} 个工具摘要到 {claude_md}")


if __name__ == "__main__":
    main()
