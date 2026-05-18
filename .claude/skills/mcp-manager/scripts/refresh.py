#!/usr/bin/env python3
"""从 mcp2cli bake 获取所有已连接 MCP Server 的工具摘要，写入 CLAUDE.md。

用法: python3 refresh.py <project_root>
"""
import re
import subprocess
import sys
from pathlib import Path

START = "<!-- MCP_GATEWAY_TOOLS_START -->"
END = "<!-- MCP_GATEWAY_TOOLS_END -->"


def run(cmd: list[str], timeout: int = 30) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def get_baked_servers() -> list[str]:
    """解析 mcp2cli bake list 输出，提取 server 名称列表。

    表格格式：Name  Type  Source（至少 3 列），跳过表头、分隔线和非表格行。
    """
    output = run(["mcp2cli", "bake", "list"])
    names = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("Name") or line.startswith("---"):
            continue
        parts = line.split()
        if len(parts) >= 3 and parts[1] in ("mcp", "openapi", "graphql", "stdio"):
            names.append(parts[0])
    return names


def get_server_tools(name: str) -> list[tuple[str, str]]:
    """解析 mcp2cli @name --list 输出，提取 (tool_name, description) 列表。"""
    output = run(["mcp2cli", f"@{name}", "--list"], timeout=60)
    tools = []
    for line in output.splitlines():
        if not line.startswith("  "):
            continue
        line = line.strip()
        match = re.match(r"^(\S+)\s+(.*)", line)
        if match:
            tool_name = match.group(1)
            desc = match.group(2).strip()
            if len(desc) > 80:
                desc = desc[:77] + "..."
            tools.append((tool_name, desc))
    return tools


def build_summary(servers: list[str]) -> str:
    lines = []
    for name in servers:
        tools = get_server_tools(name)
        if not tools:
            continue
        lines.append(f"[{name}]")
        for tool_name, desc in tools:
            lines.append(f"  {tool_name}: {desc}")
    return "\n".join(lines)


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

    servers = get_baked_servers()
    if not servers:
        print("未发现已 bake 的 MCP Server")
        update_claude_md(claude_md, "")
        return

    print(f"发现 {len(servers)} 个 baked MCP Server: {', '.join(servers)}")
    summary = build_summary(servers)
    update_claude_md(claude_md, summary)

    tool_count = summary.count("\n  ") if summary.strip() else 0
    print(f"已刷新 {tool_count} 个工具摘要到 {claude_md}")


if __name__ == "__main__":
    main()
