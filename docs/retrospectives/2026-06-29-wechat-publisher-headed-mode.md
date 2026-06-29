---
date: 2026-06-29
topic: wechat-publisher-headed-mode
tags: [wechat, playwright, retrospective, decision]
---

# 微信发布器默认使用 headed Chrome（headless=False）的决策

## 背景

`.agents/skills/wechat-article-publisher/scripts/publish.py` 用 `p.chromium.launch_persistent_context(..., headless=False)` 启动有头 Chrome。Erik 问这是否合理、是否只是因为"需要扫码登录"。复盘后结论：**默认 headed 是刻意权衡，理由不止扫码；未来即使加 `--headless` flag 也只能作实验性 opt-in。**

## 为什么默认 `headless=False`

1. **首次必须扫码登录，headed 是硬要求。** 公众号后台没有 OAuth/token 登录，只能扫码或「微信快捷登录」，都需要真实浏览器交互。
2. **`launch_persistent_context` 已经在复用 profile**（`user_data_dir=profile_dir`），后续 run 会自动登录（本次实测 `login_wait=14.2s`，就是 cookie 复用语义）。所以"扫码"只在首次/登录态过期时需要，但下面几个理由让即使在已登录状态也应该保留 headed。
3. **微信后台反自动化检测对 headless 很敏感。** `--disable-blink-features=AutomationControlled` 只绕过最基础的 `navigator.webdriver`；微信 JS 还会检测 UA（`HeadlessChrome`）、`chrome.runtime`、WebGL renderer、字体列表、插件列表、合成事件的人类特征等，headless 下误触风控的概率显著更高，表现就是 403、跳登录、保存失败。
4. **正文图片上传链路走的是编辑器内的真实文件选择 + XHR 回填 mmbiz URL。** ProseMirror/iframe 场景下 headless 合成事件 + multipart 边界差异更容易触发「图片插入但 CDN URL 不回填」之类的隐性故障；headed 下肉眼可直接看到上传进度和失败帧。
5. **final human review 本来就需要人眼。** 按 AGENTS.md 发布边界，最终群发必须人工确认。headed 浏览器停在编辑页直接就是 review 入口；如果 headless，用户还得自己再开浏览器 → 登录 → 找草稿，多一步且容易丢上下文。
6. **debug 成本差异大。** Runbook 已记录「自动保存失败」是常见 transient error；headed 下可直接看到错误弹框（风控提示、外链告警、图片未上传完告警），headless 只能靠事后 screenshot，排查链路慢一个量级。

## 什么情况下可以考虑 headless

- 长期稳定跑过 ≥20 篇、图片上传 100%、保存草稿 100% 无人工介入之后；
- 有无人值守场景（如 CI 定时发草稿）；
- 必须用 `headless=new`（Chrome 新 headless，贴近真实浏览器指纹）+ 持久 profile + 已验证过的 cookie；
- 即使加了，也要作为 `--headless` opt-in 实验 flag，默认仍 headed，并且在 SKILL.md 里标注"headless 模式下遇到保存失败请切回 headed"。

## Action

- 当前保持 `headless=False` 默认行为不动。
- 未来如果要加 `--headless` flag，先在本 retrospective 里登记验证过的文章数/失败率，再决定是否上浮到默认。
- 在 `wechat-publish-workflow` 和 `wechat-article-publisher` 的 SKILL.md 里各加一段说明，避免未来的 agent 或自己误切 headless。
