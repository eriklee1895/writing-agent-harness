# Research Notes: Hermes Multilevel Skills

Date: 2026-07-05

## Working Brief

**One-line idea:** Hermes 的多层 Skills 目录表面是分类，实际是 agent skills 规模化后的来源、边界和冲突治理。

**Thesis:** 用户关于 `skills/3rd/` 区分第三方 skills 的直觉是对的；多层路径的生产价值在于 provenance、lifecycle、risk boundary 和 explicit disambiguation，而不只是好看。

**Register:** Agent / AI Technical Essay, with light personal observation.

**Anti-goals:**

- 不写成 Hermes 官方文档复述。
- 不夸大成“只有 Hermes 支持 skills”。
- 不把 Claude Code / Codex / OpenClaw 的现状说错。
- 不把多层路径吹成安全银弹。

## Sources Checked

- Hermes official docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
  - Skills are on-demand knowledge docs.
  - `~/.hermes/skills/` is source of truth.
  - Hub-installed and agent-created skills also go there.
  - External skill directories are scanned alongside local one.
  - Progressive disclosure levels: list, view, view specific file.

- Context7 (retrieval aid only; article should prioritize Hermes official docs and source):
  - `npx ctx7@latest library "Hermes Agent" "..."`
  - selected `/nousresearch/hermes-agent`
  - `npx ctx7@latest docs /nousresearch/hermes-agent "..."`
  - Returned official structure from CONTRIBUTING and docs.

- Local Hermes source:
  - Repo: `/Users/eriklee/code/agent/hermes-agent`
  - Remote: `git@github.com:NousResearch/hermes-agent.git`
  - Commit: `7e8f50a14`

- Local source files:
  - `/Users/eriklee/code/agent/hermes-agent/tools/skills_tool.py`
  - `/Users/eriklee/code/agent/hermes-agent/agent/skill_utils.py`
  - `/Users/eriklee/code/agent/hermes-agent/agent/skill_commands.py`
  - `/Users/eriklee/code/agent/hermes-agent/tests/tools/test_skills_tool.py`
  - `/Users/eriklee/code/agent/hermes-agent/CONTRIBUTING.md`

- Community / related discussions:
  - Claude Code nested skills feature request: https://github.com/anthropics/claude-code/issues/16438
  - Codex recursive nested SKILL.md bug: https://github.com/openai/codex/issues/22275
  - Hermes project-local skills request: https://github.com/NousResearch/hermes-agent/issues/4667
  - Hermes multi-file skill install bug: https://github.com/NousResearch/hermes-agent/issues/35125
  - Hermes global skills across profiles issue: https://github.com/NousResearch/hermes-agent/issues/19451
  - withastro/flue nested skills discussion: https://github.com/withastro/flue/discussions/100

- Official comparator docs:
  - Codex skills: https://developers.openai.com/codex/skills
  - Claude Code skills: https://code.claude.com/docs/en/skills
  - OpenClaw skills config: https://docs.openclaw.ai/tools/skills-config
  - Agent Skills spec: https://agentskills.io/specification
  - Agent Skills implementation guide: https://agentskills.io/client-implementation/adding-skills-support

## Evidence Highlights

- `tools/skills_tool.py` module docstring explicitly supports category directory:

```text
skills/
├── my-skill/
└── category/
    └── another-skill/
        └── SKILL.md
```

- `_find_all_skills()` recursively scans local skills and `external_dirs` via `iter_skill_index_files(scan_dir, "SKILL.md")`.

- `_get_category_from_path()` extracts first path segment under skills root as category.

- `scan_skill_commands()` also scans via `iter_skill_index_files`, so nested skills are slash-command visible.

- `skill_utils.py` excludes support dirs from active skill discovery when directly under a skill root:
  - `references`
  - `templates`
  - `assets`
  - `scripts`

- `skill_view()` collision detection refuses ambiguous names across local and external dirs and suggests categorized path.

- Regression tests explicitly cover:
  - nested local skill collides with top-level external skill
  - collision resolvable via categorized path
  - support markdown does not collide with real skill
  - `references/old-skill-package/SKILL.md` is not active skill
  - external-only skills resolve normally
  - two external dirs same name also refuse

## Angle Decisions

- Lead with "small feature, bigger governance problem".
- Agree with user that `skills/3rd/` is useful.
- Argue that it is more than categorization: source/provenance boundary.
- Use Codex bug as counterexample showing naive recursive scanning risk.
- Avoid claiming Hermes is uniquely nested-capable; current Claude/Codex/OpenClaw docs have related path discovery features.
- Added source hierarchy: Hermes official docs and source first, Context7 only as helper.
- Added section-title shortening.
- Added scenario table for single-level vs multi-level directory choice.
- Added standard boundary analysis: Agent Skills spec defines package internals, not discovery policy.
- Added why other agents may hesitate: scanning depth, support-file false positives, collisions, slash-command UX, trust, symlinks, cloud/sandbox constraints.

## Polish Pass 2026-07-05

- Register: `agent-ai-essay`, with light personal technical observation.
- Removed AI-ish section headings such as `先说结论`.
- Reworked the opening to move from a concrete directory detail into skills governance.
- Reduced briefing / memo language: fewer "所以", "换句话说", "不是...而是", "银弹", "免费午餐" style transitions.
- Preserved source-backed technical claims and footnotes.
- Kept the author's judgment: `skills/3rd/` is useful, but mainly as provenance / trust boundary, not only categorization.

## Code Analysis Addition 2026-07-05

- Added a dedicated section on Hermes name handling.
- Key finding: parent directories do not automatically become part of skill `name`.
- `_find_all_skills()` uses `frontmatter.get("name", skill_dir.name)`.
- Parent path contributes to `category` via `_get_category_from_path()`, currently first path segment under skills root.
- Slash commands are generated from frontmatter name / skill dir name, normalized to command-safe hyphenated slug; `research/arxiv` usually becomes `/arxiv`, not `/research-arxiv`.
- `skill_view()` can still use direct relative paths such as `research/arxiv` for explicit load / disambiguation.

## Structure Review 2026-07-05

- Reworked the article from flat same-level sections into a clearer hierarchy.
- Kept main sections for: opening motivation, Hermes source-level rules, practical directory choices, standard / ecosystem comparison, and closing argument.
- Removed draft-like meta sentences from the body, especially reviewer comments such as "不能为了夸 Hermes" and "说法要收回来".
- Folded the single-child `skill 是一个 package` subsection back into body prose so the heading structure does not feel mechanically nested.
