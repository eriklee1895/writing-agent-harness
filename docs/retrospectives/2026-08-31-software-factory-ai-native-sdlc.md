# 2026-08-31 Software Factory 写作任务收尾

## Final State

- Status: `draft-created`，未确认正式发布。
- Canonical: `content/origin/2026-08-31-software-factory-ai-native-sdlc/index.md`。
- WeChat draft: `appmsgid=100001199`；标题、作者、43 字摘要、封面和 9 张正文图已校验，图片 CDN `9/9`。
- Feishu docx: [Software Factory：AI Native 软件开发流程的新范式](https://bytedance.my.larkoffice.com/docx/NLopdNdp1o3H0Gx1X5fmjW3myId)，revision 25。
- Blog: 未执行同步、构建或发布。
- Local archive: `.local-archive/2026-08-31-software-factory-ai-native-sdlc/`。

## What Worked

1. 用 Vercel、Warp、Anthropic 和 OpenAI 四条公开路线拆出 Software Factory 的 Task、Run、Workspace、Artifact、Gate、恢复和评测语义，避免写成“更多 Agent”的空泛趋势文。
2. 用户明确了“配图要帮助理解”的边界。装饰性概念封面被舍弃，最终封面与正文图都保留可读节点、流程和状态文字；Blog 八张正文图增加了可见 caption。
3. WeChat 渠道重做了竖向流程图，390px 校验无横向溢出；资料来源保留标题与可复制的明文 URL，同时 HTML 外部 `href=0`。
4. Publisher 成功保存草稿、设置封面并完成 9/9 图片 CDN 回填；标题、作者和摘要在保存前后回读一致。
5. 飞书转写的 image token → Markdown overwrite 链路稳定；云端回读确认 229 个 block ID、9 张图、30 个标题、2 张表格、38 个链接和 0 warnings。

## Problems And Fixes

### Cover layout

第一版确定性封面的 `Task Control Plane` 文字溢出，卡片宽度和箭头位置也不一致。修复 SVG 源文件后重新渲染 PNG，保留可重生成的矢量源。

### Publisher profile collision

第一次 publisher 启动遇到 `TargetClosedError`，日志显示专用 profile 已在现有 Chrome 会话中打开。通过进程参数确认冲突只属于 `wechat-article-publisher/profile`，没有关闭日常 Chrome；残留进程自行退出、Singleton 锁清除后，相同命令重试成功。

### Formal publish was not completed

用户在草稿创建后明确确认正式发布，但 publisher 只提供 `--save-draft`。可控 Chrome 仍在本地 `file://` 预览页，Computer Use 不允许在该 URL 上操作；专用微信后台窗口未暴露给可用控制面。因此状态保持 `draft-created`，没有把用户的发布意图误写为发布结果。

## Contrastive

1. 与同日《Anthropic 的 AI-Native 实践》closeout 相比，本次 origin 和 WeChat 显式保留两套不同信息密度的图：Blog 使用宽图，WeChat 使用竖向流程/组件图。这不是 asset drift，而是经过 390px 验证的渠道适配。
2. 上次 closeout 已强调 frontmatter、标准 `index.wechat-preview.html` 和飞书 image-token 链路。本次这三项都直接生效：无需补建渠道 artifact，publisher 元数据回读通过，飞书 9 张图全部写入。
3. `codex-long-running` 已出现过“当前可控浏览器是本地预览页，无法操作微信后台最终发布”。本次原样重复，已不能继续当作偶发问题，必须维持 skill staleness flag。

## Skill Staleness Check

⚠️ `wechat-publish-workflow` 对“用户确认后继续正式发布”的可执行路径描述超前于底层能力。重复信号已追加到 `.local-memory/skill-staleness-wechat-publish-workflow.md`。当前 publisher 应继续保持“只创建草稿”，最终发布需要独立 workflow 与可恢复的后台控制面。

## Memory / Skill Decision

- 已把“流程/架构图必须有可读节点文字”与“Blog alt 不等于可见 caption”提升到 `docs/reference/visuals.md`。
- 不修改 `SOUL.md` 或 `AGENTS.md`：本次经验属于视觉/发布 workflow，已有更精确的 docs 与 staleness 落点。

## Remaining Human Action

- 在微信草稿箱复核封面裁切、正文 9 张图与来源明文 URL，由用户完成最终发布/群发。
- 正式发布后回填公开 URL，将 `publish-status.md` 与 task index 状态改为 `published`。
- Blog 如需发布，另行启动 `erik-blog-publish-workflow`；本次 closeout 未触及 Blog repo。

## Git / Task

- 媒体二进制已复制到 `.local-archive/`，working copy 因 canonical 相对引用而保留，受 `.gitignore` 忽略。
- Markdown、SVG/Mermaid 源、manifest、渠道 HTML、草稿状态和本复盘属于可追踪交付物。
- 工作树存在与本任务无关的删除和其他未跟踪文章目录；closeout 未触碰它们，本次未提交、未暂存。
