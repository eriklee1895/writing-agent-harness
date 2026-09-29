# 2026-09-29 Reasoning Effort 微信草稿 Closeout

## 状态

- 状态：`draft-created`，尚未群发。
- 公众号草稿：appmsgid `100001431`。
- Blog：<https://eriklee-blog.pages.dev/posts/2026-09-29-reasoning-effort/>。
- 微信 preview：`content/wechat/2026-09-29-reasoning-effort/index.wechat-preview.html`。
- 正文 3 张图均已上传至微信 CDN，封面上传状态为 `cover-set`。

## 验证

- Renderer 使用 `warm-editorial`，输出 3 张正文图；生成 HTML 无 `<script>`、外链 `href` 或 base64 图片。
- 430px 移动视口 `scrollWidth=clientWidth=430`，无横向溢出。
- Publisher 保存前回读：标题 42 字符、摘要 100 字符，作者使用 `.config/wechat.toml` 的默认值。
- 发布器截图显示编辑器 `已保存`，Draft History 有 09-29 16:47 的手动保存记录；appmsgid 为 `100001431`。

## 坑点与修复

Publisher 的 `_JS_DRAFT_STATUS` 把 `#title` 回读值截为前 40 字符，导致这篇 42 字符标题在保存状态比较中永远不相等。正文、封面和图片均已进入编辑器，但自动确认分支因此报“标题不匹配 / 保存未确认”。编辑器截图中的标题完整，并显示 `已保存`，所以该报告是客户端校验的 false negative。

已删除标题回读的 40 字符截断。为了避免额外创建重复草稿，本次不再重跑保存；已用编辑器保存状态、草稿历史、appmsgid、封面和 3/3 CDN 上传日志确认现有草稿。后续运行 publisher 时应确认完整标题回读通过。

默认 publisher Chrome profile 正被一个现有浏览器会话占用。保留该会话，使用独立 profile 复用本次登录，避免关闭或覆盖用户已有浏览器。

## Contrastive

- 与 2026-06-29 publisher 修复相比：当时解决了预分配 appmsgid 假阳性、Vue blur/flush 和保存后校验；本次是另一层问题——状态快照自身截断标题。两次都说明，保存状态校验必须比较完整字段，同时把编辑器可见保存状态和草稿历史纳入证据。
- `.local-memory/task-index.json` 先前记录过 `wechat-title-truncated-by-backend`。本次不是微信后台再次截标题；根因是本地脚本只返回 40 字符，界面显示的完整标题未被保留在自动比较值中。
- 本次未遇到 6/29 多次尝试后标题/作者丢失的情况：保存前标题、作者、摘要均回读完整，封面和正文图片上传均成功。

## Archive 与来源

- 4 张最终 PNG 已归档到 `.local-archive/2026-09-29-reasoning-effort/images/`，hash 已核对。
- `content/origin/2026-09-29-reasoning-effort/assets/manifest.json` 保留生成 prompt 和素材 provenance；canonical `assets/*.png` 以相对 symlink 指向归档文件。
- Blog 仓库拥有独立发布资产副本；WeChat 草稿图片已位于微信 CDN。

## 后续

- Erik 在微信后台「草稿箱」检查完整标题、作者、摘要、封面裁切及 3 张正文图，再决定是否群发。
- 发布器完整标题回读修复本轮只做 CLI 解析和静态检查；之后的正常草稿流程可继续验证，不为此重复创建当前草稿。
