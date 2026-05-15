---
name: refresh-mcp
description: 刷新 MCP Gateway 托管的工具摘要并写入 CLAUDE.md
disable-model-invocation: true
---

执行此 skill 目录下的 `scripts/refresh.py` 脚本，传入项目根目录作为参数：

```
python3 <SKILL_DIR>/scripts/refresh.py $PROJECT_ROOT
```

其中 `<SKILL_DIR>` 是此 SKILL.md 文件所在的目录（根据加载路径推导，可能是 `$PROJECT_ROOT/.claude/skills/refresh-mcp` 或 `~/.claude/skills/refresh-mcp`）。
