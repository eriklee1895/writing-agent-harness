---
date: 2026-09-29
slug: reasoning-effort
dir: 2026-09-29-reasoning-effort
status: draft-created
appmsgid: "100001431"
channel: wechat
title: Reasoning Effort 到底在调什么？从 Claude 的实测到跨模型验证
author: 李玉恒
image_count: 3
saved_at: 2026-09-29 16:47
---

# 发布状态

微信公众号草稿已保存，appmsgid=`100001431`。封面状态为 `cover-set`；正文图片 3/3 已上传到微信 CDN。

## Draft History

- 2026-09-29 16:47  status=draft-created  appmsgid=100001431
  - 标题：Reasoning Effort 到底在调什么？从 Claude 的实测到跨模型验证
  - 作者：李玉恒
  - 摘要：从 Anthropic 的 Claude Code 实测出发，拆解思维链、推理时计算与 reasoning effort 的关系，再用跨模型文档和自己的 Agent benchmark 检验适用边界。
  - 正文：33262 chars，3 张正文图
  - 封面：reasoning-effort-cover-imagegen.png（已设置）

## Verification Notes

- 微信编辑器截图显示 `已保存`，Draft History 有 09-29 16:47 的手动保存记录；编辑器标题为完整标题。
- Publisher 自动回读未确认成功：脚本在保存状态快照中把标题截为 40 字符，导致与 42 字符标题比较失败。已修复 `.agents/skills/wechat-article-publisher/scripts/publish.py` 的截断问题。正文图上传日志为 3/3 CDN，封面日志为 `cover-set`。
- 文章目前是公众号草稿，尚未群发/正式发布。

下一步：去微信后台「草稿箱」做 final human review，核对标题、作者、摘要、封面裁切和 3 张正文图，再决定是否群发。
