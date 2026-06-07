# 2026-06-06 微信公众号 CDP Only 决策

## Context

在 Cloudflare/Vite 文章通过 CDP 成功同步到微信公众号草稿箱后，继续调研了官方 API 创建草稿能力。官方 API 看起来更工程化，但真实约束会显著增加个人写作 harness 的维护成本。

## Decision

本 repo 的微信公众号自动化工作流只维护 CDP/browser 模式。

官方 API / remote-api 保留为历史和实验能力，不作为默认发布路径，不围绕它继续设计主 workflow。除非未来已经自然具备稳定白名单出口 IP，并且有明确收益，否则不投入维护 API 主线。

## Why Not API

- API 调用需要 AppID/AppSecret、access_token，以及在微信公众号后台配置调用 IP 白名单。
- 如果本机公网 IP 不稳定，就需要维护一台固定公网 IP 的服务器，或维护 remote-api SSH 隧道；这会把发文章自动化变成基础设施维护。
- API 富文本链路需要额外兼容层：正文图片要先上传成微信图片 URL，封面要上传成永久素材 `thumb_media_id`，再调用 `draft/add`。
- API 草稿返回成功不等于最终编辑器呈现完全符合预期；复杂排版、封面、图片、摘要和外链仍然需要在微信后台核对。
- 对个人写作 harness 来说，API 的速度收益抵不过 IP 白名单、富文本兼容和调试成本。

## Why CDP

- CDP 复用已经登录的微信公众号后台，直接操作真实编辑器。
- 编辑器里看到的状态更接近最终 human review 状态。
- 不需要 AppID/AppSecret、access_token、固定公网 IP 或服务器。
- 已经通过真实文章跑通：Markdown source -> WeChat HTML preview -> mobile verification -> CDP editor upload -> save 草稿箱 -> user final publish。
- 已经沉淀了外链、正文图、封面图、自动保存失败、`appmsgid` 等关键坑点和可验证信号。

## Human In The Loop

CDP 模式唯一不可避免的人工参与点是扫码登录。

这是微信账号安全模型和登录态限制带来的物理原因，不是 workflow 设计缺陷。用户扫码后，agent 可以继续接管后续草稿箱同步、图片检查、封面检查、链接检查和 `appmsgid` 报告。

这个边界可以接受：扫码之外，微信公众号草稿同步已经接近 100% AI 自动化。

## Reusable Rule

下次任何 agent 处理微信公众号发布时：

- 默认使用 CDP/browser 模式。
- 不要为了“更优雅”把主路径改回官方 API。
- 不要要求用户维护公网服务器或固定出口 IP。
- 不要未经用户明确确认点击最终发布/群发。
- 如果 CDP 登录态失效，提示用户扫码；扫码后继续自动化流程。

## Open Questions

- 是否需要把 `baoyu-post-to-wechat` 的 browser/CDP 子集蒸馏成更小的 project-specific uploader。
- 是否需要给 CDP 流程增加更稳定的 post-save checker，用于自动确认正文图片、封面、外链和 `appmsgid`。
