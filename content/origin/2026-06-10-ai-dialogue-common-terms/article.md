---
title: "与AI对话常用词⭐️"
date: 2026-06-10
author: Erik Lee
style: tech-blog
description: "普适所有 Coding Agent 的极简对话语言，覆盖 Proceed / Continue / Agreed / LGTM / Approved 等高频词"
---

# 与AI对话常用词⭐️

普适所有agent！
如：TRAE / Claude Code / Codex / OpenClaw / Hermes Agent / Pi Agent / 。。。

## 高频词Overview

| 词语 | 含义 | 使用场景 | 频率 |
| --- | --- | --- | --- |
| **Proceed** | 按当前方案开始执行 | 方案确认后 | ⭐⭐⭐⭐⭐ |
| **Continue** | 继续上一轮任务 | 被打断、执行暂停后 | ⭐⭐⭐⭐⭐ |
| **Go ahead** | 开始执行 | 与 Proceed 基本同义 | ⭐⭐⭐⭐ |
| **Agreed** | 同意分析或方案 | 设计讨论阶段 | ⭐⭐⭐⭐ |
| **Approved** | 审批通过 | 代码修改前、PR Review | ⭐⭐⭐ |
| **LGTM** | Looks Good To Me | Code Review | ⭐⭐⭐ |
| **Ship it** | 可以提交/发布 | 完成开发后 | ⭐⭐ |
| **Sounds good** | 听起来不错 | 比较口语化 | ⭐⭐ |
| **Makes sense** | 有道理 | 认可分析过程 | ⭐⭐ |
| **Ack** | Acknowledged（收到） | 偏工程师风格 | ⭐⭐ |

## 按场景分类

## 任务推进类（最常用）

这几个词占了绝大多数 Agent 交互：

| **回复** | **Agent理解** | **频率** |
| --- | --- | --- |
| Proceed | 立即开始执行 | ⭐⭐⭐⭐⭐ |
| Continue | 继续上次任务 | ⭐⭐⭐⭐⭐ |
| Go ahead | 开始执行 | ⭐⭐⭐⭐ |
| Do it | 开始执行 | ⭐⭐⭐ |
| Implement it | 开始实现 | ⭐⭐ |

## 方案确认类

Agent 提出设计方案后：

| 回复 | Agent理解 | 频率 |
| --- | --- | --- |
| Agreed | 我同意 | ⭐⭐⭐⭐ |
| Makes sense | 逻辑合理 | ⭐⭐⭐ |
| Sounds good | 没问题 | ⭐⭐ |
| I agree | 我同意 | ⭐⭐ |

## Code Review 类

Agent 改完代码后：

| 回复 | 来源 | 频率 |
| --- | --- | --- |
| LGTM | GitHub传统 | ⭐⭐⭐ |
| Approved | PR审批 | ⭐⭐⭐ |
| Ship it | 工程师俚语 | ⭐⭐ |

## TLDR

- **高级用户最常用的极简回复**

很多重度 Agent 用户实际上经常只发下面几个：

```
Proceed.
Continue.
LGTM.
Approved.
Do it.
```

## 如果只能记住 5 个 😃

这是最通用的一组：

| 词 | 用途 |
| --- | --- |
| **Proceed** | 按方案开始执行 |
| **Continue** | 继续任务 |
| **Agreed** | 同意方案 |
| **LGTM** | 代码审核通过 |
| **Approved** | 正式批准 |

基本覆盖 90% 以上与 Coding Agent 的日常协作场景。

## 速记⭐️

**✅ 同意 / 批准（最常用）**

- yes / y / ok / okay
- agreed / approve / accepted
- sounds good / looks good / go ahead

**✅ 继续 / 执行（最常用）**

- proceed / continue / go on
- just do it（Claude Code 社区最爱）
- do it / execute / run

**✅ 不太常用但能识别**

- confirm / affirmative / proceed with plan

## FAQ

### 这些词，通常比用中文效果要好是吗？

> 💡 **TLDR：问就是更省 token，AI 能秒懂** 😜

对于 **Claude Code、Codex、OpenClaw、Hermes、Cursor Agent** 这类以英文训练数据为主的 Coding Agent 来说：

**是的，简短明确的英文指令通常会比中文略好一些，但差距没有很多。**

可以理解为：

| 方式 | 效果 |
| --- | --- |
| Proceed | ⭐⭐⭐⭐⭐ |
| Go ahead | ⭐⭐⭐⭐⭐ |
| Continue | ⭐⭐⭐⭐⭐ |
| 继续 | ⭐⭐⭐⭐ |
| 开始吧 | ⭐⭐⭐⭐ |
| 好的，按照你的方案继续执行 | ⭐⭐⭐⭐ |
| 我觉得方案总体上没什么问题，你可以开始尝试实现 | ⭐⭐⭐ |

原因不是 Agent 不懂中文，而是：

1. **训练数据问题**——GitHub、PR Review、Issue、RFC、开源社区讨论，大部分都是英文。
2. **Agent 工作流数据**——很多 Agent 的训练样本里存在大量 `User: proceed`、`User: continue`、`User: approved`、`User: lgtm` 这样的交互。
3. **减少歧义**——中文"好的"可能表示"我同意"、"我知道了"、"继续执行"、"我会自己处理"；而 `Proceed.` 几乎只有一种解释：开始执行。

不过对于 GPT-5.5、Claude Sonnet 4.x 这一代模型来说：

```
继续
```

和

```
Continue.
```

实际效果已经非常接近。

例如：

```
同意方案，开始执行。
```

与

```
Agreed. Proceed.
```

Agent 基本会做出相同的行为。

如果追求最稳定、最符合工程社区习惯的表达，可以参考：

| 场景 | 推荐 |
| --- | --- |
| 同意方案 | Agreed. |
| 开始执行 | Proceed. |
| 继续任务 | Continue. |
| 审核通过 | LGTM. |
| 正式批准 | Approved. |
| 允许提交 | Ship it. |

很多资深 Agent 用户甚至会把对话压缩成：

```
Agreed. Proceed.
```

```
LGTM.
```

```
Continue.
```

因为这些词已经接近一种“Agent 时代的命令行语言”，简短、低歧义，而且几乎所有主流 Coding Agent 都能稳定理解。