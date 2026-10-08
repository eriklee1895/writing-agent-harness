---
name: writing-task-closeout
description: "写作任务发布后 closeout。Use after WeChat/blog draft creation, publishing, or final handoff when the user says 任务收尾/归档/复盘/回填链接/清理素材/整理 memory/git/task; archive final article state, move image/video binaries to .local-archive/YYYY-MM-DD-<slug>/, preserve prompts/metadata/manifests/notes, update publish status, decide memory/skill improvements, and prepare git/task handoff without publishing."
---

# Writing Task Closeout

## Overview

这个 skill 用于 `wechat-publish-workflow`、blog build/publish 或其他渠道交付之后，关闭一次写作任务。

它不负责判断文章内容是否 ready；pre-publish 内容检查交给 `article-readiness-check`。它也不点击最终发布/群发，除非用户已经明确授权并且当前任务就是发布 workflow。

`.local-archive/` 是本机二进制素材库，不是跨机器 canonical source。这个 repo 的 canonical source 是 Markdown / MDX、prompt、metadata、manifest、notes 和发布状态。跨机器工作时，需要手动同步 `.local-archive/`、从外部资产库取回、从平台 CDN 回填，或按 metadata 重新生成素材。

## Workflow

1. 确认任务状态：
   - `draft-created`: 已创建草稿，但还未正式发布。
   - `published`: 已发布，需要回填链接、`appmsgid` 或平台 ID。
   - `handoff-only`: 已交给用户 final review，暂不发布。
   - `abandoned`: 本次写作停止，但需要清理和记录原因。
2. 找到 canonical Markdown / MDX 和渠道产物：
   - canonical article file（`content/origin/YYYY-MM-DD-&lt;slug&gt;/`）；
   - generated preview / draft notes；
   - images / prompts / metadata；
   - video material packages / clips；
   - publish URL、`appmsgid`、blog URL 或其他平台 ID。
3. **渠道产物校验（关键）**：在开始归档前，核对每个交付过的渠道都有对应派生 artifact。常见缺漏：
   - **微信公众号**：`content/wechat/YYYY-MM-DD-<slug>/index.wechat-preview.html` 必须存在（publisher 自动归档，但 closeout 仍需校验）。若缺失，立即补建：把 origin 下最新的 `*.wechat-preview.html` 拷过去。
   - **发布态不在渠道目录**：`publish-status.md` 需登记 `appmsgid`、`status: draft-created`（或 `published`），但它属于**渠道运营状态而非文章内容**，按 AGENTS.md 的 Publish Boundary 写在 `.local-archive/YYYY-MM-DD-<slug>/publish-status.md`（`.gitignore` 已覆盖），**不在 `content/wechat/` 下**。缺失时手写补建。`content/wechat/` 只放可进 git 的排版产物。
   - **Blog / 其他渠道**：按对应 workflow 的渠道目录约定校验。
   - 如果发现归档缺失属于**流程/脚本 bug 而非本次失误**（例如脚本没做、skill 没写），先在本次 closeout 里把产物补全，再通过 Skill Staleness Check 机制登记为 staleness flag，必要时修 skill/脚本。
4. 按 `YYYY-MM-DD-<slug>` 创建或使用本机归档目录（`<slug>` 为裸 topic）：

   ```text
   .local-archive/
     YYYY-MM-DD-<slug>/
       images/
       video-materials/
       video-clips/
       archive-manifest.md
   ```

5. 移动或确认二进制素材归档；repo 只保留轻量 provenance。
6. 写复盘、memory / skill 决策、git / task handoff。
   复盘时同步写入任务索引（`.local-memory/task-index.json`）。
7. 最终回复说明 closeout 状态和剩余人工动作。

### Contrastive Retrospective（自进化 1：Compare, don't just record）

单次复盘容易放大偶发事件。每次 closeout 必须反问三个对比问题：

1. **这次和上次同类任务有什么不同？**（成功/失败模式是否重现？）
2. **上次 closeout 标记的改进方向，这次验证了吗？**（如果没落地，blocker 是什么？）
3. **这次发现的问题在上次是否已经出现过？**（如果是，这是重复模式，必须写入 skill 或 anti-pattern。）

产出形式：Retrospective 中新增 `## Contrastive` 段落，记录对比结论而非感觉。

### Skill Staleness Check（自进化 2：Staleness detection）

每次 closeout 扫描当前任务执行过程中是否有已有 skill 与实际情况不匹配的信号：

- 运行时 agent 是否忽略了某个 skill 指令而用别的方式完成任务？
- 某个 skill 引用的工具/API/路径是否已经变更？
- 用户是否在任务中纠正了某个 skill 假设的行为？
- publisher/renderer 是否因为 skill 过时导致额外 debug 循环？

如果发现 >=1 个腐化信号，在 `.local-memory/` 下写入 `skill-staleness-<name>.md`，并在 Retrospective 中标记 `⚠️ 技能腐化风险`。

### Task Index

每次 closeout 追加 `.local-memory/task-index.json`：

```json
{
  "slug": "hermes-agent-self-evolution",
  "date": "2026-06-12",
  "status": "draft-created",
  "appmsgid": "<见 .local-archive 发布态>",
  "skills_used": ["wechat-article-renderer", "wechat-article-publisher"],
  "patterns_detected": ["closeout-img-path-broken"],
  "staleness_flags": ["publisher-cover-auto-upload-unreliable"]
}
```

字段说明：
- `patterns_detected`：本次发现的重复模式或反模式（>=3 次出现在索引中 → 建议 skill 化）
- `staleness_flags`：发现的技能腐化信号
- `appmsgid` 或 `url` 作为 task ID

## Archive Policy

**重要：图片和视频素材在生成阶段不要双写。** 生成期版本（如 cover v1/v2/v3）只保留在 `content/origin/YYYY-MM-DD-<slug>/assets/` 工作副本中；在 closeout 收尾时，再把最终 `index.md` 和实际被引用的素材统一归档到 `.local-archive/YYYY-MM-DD-<slug>/`。

归档目录 `<slug>` 为裸 topic，目录名格式为 `YYYY-MM-DD-<slug>`，含日期前缀，避免同名冲突。

```text
.local-archive/
  YYYY-MM-DD-<slug>/
    index.md                  # 最终文章快照
    archive-manifest.md       # 归档说明
    images/                   # 实际使用的图片
    prompts/                  # 图片/视频生成 prompts 与 metadata JSON
    video-materials/          # 原始视频素材
    video-clips/              # 最终剪辑
```

### What Stays In Git

- Canonical Markdown / MDX articles（in `content/origin/`）and channel-specific text versions.
- Frontmatter（仅文章元数据）。
- Image prompt / metadata JSON, if small and not containing secrets.
- Asset manifest / notes, alt text, caption, usage, insertion point.
- `sources.md`, `manifest.json`, `clip-manifest.json`, `notes.md`.
- Published URL, CDN URL, blog repo path, or platform ID（**不含 `appmsgid`**，见下）。
- Retrospective notes and reusable workflow updates.

⛔ **`appmsgid` / 草稿 URL / 群发状态一律不进 git。** 它们是渠道运营态而非文章内容，写在 `.local-archive/YYYY-MM-DD-<slug>/publish-status.md`（`.gitignore` 已覆盖）。理由：`appmsgid` 可构造微信后台编辑链接，属账号态敏感信息；且草稿会删会重发、值会变，写进 git history 只会留下 stale data。

> 复盘、notes、readiness 里要引用发布态时，写指针而不是内联真实值——例如「公众号草稿：`appmsgid=<见 .local-archive 发布态>`」。**只要句子本身内联了那串数字，它就已经进了 git**，无论它出现在 `content/`、`docs/` 还是 skill 文档里。

### What Does Not Stay In Git

- Article image binaries: `*.png`, `*.jpg`, `*.jpeg`, `*.webp`, `*.gif`, `*.avif`, `*.heic`, `*.tif`, `*.tiff`.
- Design/source binaries such as PSD, large layered files, or generated image variants.
- Video binaries: `*.mp4`, `*.mov`, `*.m4v`, `*.webm`, `*.mkv`, `*.avi`.
- Raw video downloads, final clips, transcode intermediates, HyperFrames rendered video outputs.

Keep binary media in `.local-archive/YYYY-MM-DD-<slug>/` or external storage. If future blog assets move to a separate Astro repo, record the target repo/path or published URL in tracked notes here.

Do not use base64 as an archive strategy. It bloats HTML and Git history while making failures harder to debug.

### Image Archive

- **只在 closeout 时移动图片。** 生成阶段不要双写到 `.local-archive/`。
- 移动最终图片到 `.local-archive/YYYY-MM-DD-<slug>/images/`，只移动 `index.md` 中实际引用的图片；未使用的生成版本可保留在 `content/origin/YYYY-MM-DD-<slug>/assets/` 中作为本地工作副本，不强制清理。
- 同时复制最终 `index.md` 到 `.local-archive/YYYY-MM-DD-<slug>/index.md` 作为文章快照。
- 保留源 prompt、style profile、model/provider、size/ratio、generation time、usage 和 article reference；将对应 `.json` metadata 放入 `.local-archive/YYYY-MM-DD-<slug>/prompts/`。
- Repo 中保留 `content/origin/YYYY-MM-DD-<slug>/assets/manifest.json` 作为轻量 provenance，记录每张图的来源、生成参数、归档路径、使用状态。
- 移动后必须维持 canonical 的 `assets/...` 引用有效：可在原素材路径保留指向归档图片的相对软链接，并确认该链接仍被媒体忽略规则排除。不要把 canonical 引用改成 `.local-archive/...`。校验归档文件哈希、软链接解析和预览加载；跨机器仍需按 manifest 同步或恢复图片。
- 归档 `index.md` 快照也需要能找到图片：可在归档根建立 `assets -> images` 相对链接。独立博客仓库中的已发布图片属于其部署资产，不随写作仓库清理删除。
- 后续需要修改或重新生成已归档图片时，先把工作路径的软链接替换为独立工作副本或使用新文件名，避免通过软链接覆盖归档快照。

### Video Archive

- Move `media.*`, `final.*`, transcode intermediates and rendered video outputs to `.local-archive/YYYY-MM-DD-<slug>/video-materials/` or `video-clips/`.
- Keep tracked `sources.md`, `manifest.json`, `clip-manifest.json`, `notes.md` with source URL, retrieved date, segment timestamps, rights reminder, publish status and recovery hint.
- Do not record cookies, login state, account state, private browser profile paths, or sensitive absolute local paths. If needed, use a relative `.local-archive/YYYY-MM-DD-<slug>/...` hint.
- Do not `git add` video files.

## Cleanup

- Clean only files clearly belonging to this task and safe to regenerate or discard.
- `inbox/` material can be deleted, moved, or summarized only after confirming it has no independent future value.
- Failed `drafts/` intermediate versions can be removed or moved to `.local-archive/YYYY-MM-DD-<slug>/` when they are not meaningful writing variants.
- Do not delete user edits, canonical article files, or unconfirmed assets.

## Retrospective

Record the useful parts of the run:

- final status and timeline;
- what changed during channel publishing;
- failures, error messages, workaround and verification;
- good prompts, styles, editorial moves, renderer fixes or upload lessons;
- remaining follow-ups.

Write verified, reusable workflow improvements to `docs/` or the relevant skill. Keep one-off observations and unverified local context in `.local-memory/`.

## Memory And Skill Decisions

- `SOUL.md`: only update for durable author voice, register or anti-style lessons validated in real writing.
- `AGENTS.md`: only update high-frequency repo behavior boundaries; keep it short.
- `docs/`: use for workflow improvements, retrospectives, checklists and publishing lessons.
- `.local-memory/`: use for short-term, local, not-yet-validated context.
- Existing skill bug: make a small fix when obvious; otherwise record in `docs/project/todolist.md` or the user's issue tracker.
- New skill: suggest one only when the workflow is likely to repeat 3+ times and has clear boundaries.

## Git And Task Handoff

- Inspect working tree before staging. There may be unrelated user changes.
- If the user asks for a commit, stage only files belonging to this writing task.
- Never stage ignored media binaries unless the user explicitly force-adds a specific exception.
- If a task system or `TaskCreate` item exists, mark it complete or report the remaining blocker.
- Final response should state archive path, tracked provenance files, publish status, retrospective/memory/skill actions and git/task status.

## Output Format

```markdown
## Closeout Status

Complete / Needs follow-up / Blocked

## Published State

- Status:
- URL / appmsgid / platform ID:

## Archive

- Local archive:
- Tracked provenance:
- Media not committed:

## Retrospective

- ...

## Memory / Skill

- ...

## Git / Task

- ...
```
