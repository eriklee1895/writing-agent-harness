---
title: "Claude Code 典型工作流常用命令速查"
date: "2026-06-12"
description: "把 Claude Code 的命令按初始化、干活、并行、发布、切换、排错六个阶段串成一条主线，方便随时查阅。"
style: agent-flow
source: "Anthropic Claude Code official reference"
version: "2026.06"
---

# Claude Code 典型工作流常用命令速查

> 命令不是孤立工具，而是嵌在 **初始化 · 干活 · 并行 · 发布 · 切换 · 排错** 这条主线上的节点。记住每个阶段该用哪几个，就能把整套流程串起来。

一句话总结：Claude Code 的斜杠命令可以按会话阶段分成六组，按需调用即可避免在终端里「硬想该打什么」。

## 01 初始化：搭好地基

- `/init` — 生成起步用的 `CLAUDE.md`
- `/memory` — 打磨、精修项目记忆
- `/mcp` — 配置 MCP 服务器
- `/agents` — 配置子代理
- `/permissions` — 设定审批 / 授权规则

## 02 干活：控制节奏与上下文

- `/plan` — 大改动前进入计划模式
- `/model` — 调整所用模型
- `/effort` — 调整推理投入
- `/context` — 查看上下文窗口被什么占满
- `/compact` — 压缩过长对话，腾出空间
- `/btw` — 旁白提问，不撑大历史记录

## 03 并行：把活儿铺开

- `/agents` — 打开子代理管理器，委派支线
- `/tasks` — 列出当前会话后台任务
- `/background` — 会话转入后台，腾出终端
- `/batch` — 大改动拆 worktree 并行执行

## 04 发布：检查改动

- `/diff` — 查看具体改了什么
- `/code-review` — 审查 diff；`--fix` 直接修，`--ultra` 深度
- `/review` — 更深入的只读审阅
- `/security-review` — 安全相关的只读审阅

## 05 切换：开新局或回头

- `/clear` — 保留项目记忆，重开会话
- `/resume` — 回到某段早期对话
- `/branch` — 分叉某段对话
- `/teleport` — 把网页端会话拉进当前终端
- `/remote-control` — 让另一台设备继续操作

## 06 排错：回滚与诊断

- `/rewind` — 回退代码 / 对话到检查点
- `/doctor` — 诊断安装问题
- `/debug` — 诊断运行时问题
- `/feedback` — 上报 bug，自动附会话上下文

---

Source · Anthropic Claude Code official reference · v.2026.06
