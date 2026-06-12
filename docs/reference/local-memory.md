# Local Memory

`.local-memory/` 是本机 scratch memory，用于暂存还没有判断清楚、还不适合进入 Git 的想法和 todo。

它不属于 canonical repo memory，不提交，不同步，不作为长期事实来源。

## When To Use

适合放入 `.local-memory/` 的内容：

- 今天想到但还没决定是否推进的 todo。
- 需要下次继续看的临时线索。
- 不适合公开或同步的个人上下文。
- 本机环境状态和一次性调试记录。
- 还没有验证、还不值得写进 docs 的 workflow 想法。

不适合只留在 `.local-memory/` 的内容：

- 已确认会影响 workflow 的规则。
- 已跑通、下次还会复用的坑点和经验。
- project skills 的边界、触发条件、脚本变化。
- 目录结构、发布边界、长期路线图。

这些内容应迁移到 `docs/`、`AGENTS.md`、`.agents/skills/` 或 retrospectives。

## Suggested Files

本机可自行创建：

```text
.local-memory/
├── todo.md
├── inbox.md
└── notes.md
```

建议格式：

```markdown
# Local Todo

- [ ] 想法或任务
  - context: 为什么想到它
  - promote when: 什么条件下迁移到 repo docs
  - destination: 如果提升，应该进入 `docs/`、`AGENTS.md`、`.agents/skills/` 还是 `content/origin/`
```

## Promotion Rule

每次任务结束或整理 memory 时，快速判断：

```text
这条 local memory 是否已经对未来 workflow 有稳定价值？
```

如果答案是 yes：

- 长期 todo → `docs/project/todolist.md`
- workflow 规则 → `docs/workflows/*.md`
- 坑点复盘 → `docs/retrospectives/*.md`
- skill 变化 → `.agents/skills/*`
- 高频行为规则 → `AGENTS.md`
- 文章源稿 → `content/origin/`，不要迁移到 `docs/`

如果答案是 no，继续留在 `.local-memory/` 或删除。
