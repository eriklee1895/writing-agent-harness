---
title: "Hermes Bot 拆解：Agent 的身份、克隆与分发"
date: 2026-09-20
topic: hermes-bot-architecture
tags: ["hermes", "bot-mode", "ai-agent", "profile", "nous-research"]
register: "agent-ai-essay"
summary: "从源码拆解 Hermes 的 profile 原语：一位 agent 的完整身份如何装进一个可克隆、可分发、可迁移的目录。"
cover: assets/cover.png
ogImage: assets/blog-cover.png
---

# Hermes Bot 拆解：Agent 的身份、克隆与分发

2026 年 8 月，Nous Research 给开源 agent 项目 Hermes Agent 的桌面端上线了 Bot Mode——社区里更常叫它 Hermes Bot。它给你的是一列花名册：每个 Bot 有名字、有头像、有独立的一份记忆和技能库，能单独对话，能拉几个进同一个房间讨论，也能互相发消息派活。

我在上面建了第一个 Bot，就叫它 researcher 吧。然后我干了件扫兴的事：打开终端，看看它到底住在哪——

```
~/.hermes/profiles/researcher/
```

一个目录。SOUL.md 是人格与常驻指令，config.yaml 存模型和全部设置，.env 里是它自己的密钥，memories/ 是它记住的事，skills/ 是它会做的事，sessions/ 和 state.db 装着对话历史，cron/ 是它的定时任务。

花名册上的那个 Bot，在磁盘上就是这么一堆文件。

这篇拆解讲三件事：这个目录里装了什么，Bot Mode 在它之上加了什么，以及这套设计在工程上要付什么代价。所有结论都对着 2026 年 9 月的源码核过。

## 一个 profile 里装着什么

profile 的定义一句话说得完：**一个独立的 Hermes home 目录**。默认 profile 就是 `~/.hermes`；命名 profile 放在 `~/.hermes/profiles/<name>/`。

![Profile 解剖：一个目录就是一位 agent 的全部身份](assets/profile-anatomy.png)

它和几个容易混的概念不是一回事：workspace 管终端命令从哪启动，sandbox 管文件系统的访问权限，profile 管的是一位 agent 的全部状态。按用途分，有六类：

- **身份**：SOUL.md（人格与常驻指令）、profile.yaml（描述、显示名、花名册展示信息）
- **凭据**：.env 和 auth.json。代码里的规则比文档还严：命名 profile 只从自己的 auth.json 和 .env 解析提供商，永不继承根 profile 的登录或 API key
- **记忆**：memories/ 下的 MEMORY.md 和 USER.md。代码注释解释了它们的地位：和 SOUL.md 一样，属于身份，不是缓存
- **能力**：skills/。agent 自己沉淀的技能存在这里，只属于它自己
- **历史**：sessions/ 和 state.db（SQLite 状态库）
- **定时**：cron/ 里它自己的任务

选目录而不是发明一个注册表，好处是目录自带的工具全部可用：备份用 tar，搬移用 mv，同步用 rsync，版本控制用 git，查看用任意文本编辑器。状态是文件，操作系统本身就是管理界面，中间没有“先启动某个服务才能读到 agent”这一层。这个选择在后面会反复带来便利。

代码里，三百多个文件通过同一个 `get_hermes_home()` 解析路径。这个函数返回什么，agent 就住在哪里；profile 的别名命令（`~/.local/bin/` 下的一份包装脚本）做的事只有一件：把 `HERMES_HOME` 指到对应目录，再启动 Hermes。一位 agent 的地址、身份和全部数据，最终被压缩成了一个环境变量。

这个设计随即遇到一个真实的工程约束：环境变量是进程级的，但多 profile 网关要在一个进程里服务好几个 profile（后文会细说）。所以在那条路径上，home 不是靠 `os.environ` 切换的，而是一个 ContextVar 级的覆盖——`hermes_constants.py` 里的 `set_hermes_home_override()`，优先级高于环境变量。每一次对话轮次在自己的上下文里解析自己的 home，互不污染。

一个目录要被认成 profile，还有门槛：里面至少得有一个身份文件——config.yaml、.env、SOUL.md、profile.yaml、auth.json、state.db 之一。空目录不算，被日志弄脏的目录也不算。

## 从 Profile 到 Bot

官方文档维护着一张术语表，先把名字对齐：

- Profile：一位助理的持久化 home，配置与数据。跨对话、跨重启保持同一份状态。
- Agent：正在运行的、使用这份配置与状态的实例。“Hermes Agent”同时也是产品名。
- Bot Mode 的 Bot：profile 在桌面花名册里的展示形态，有头像和一条常驻 Bot Chat。
- Messaging bot：Telegram、Discord 这类平台上那个账号，身份是它的 bot token。
- Subagent：`delegate_task` 临时拉起的子助理，用完即走；一次独立对话不等于一个独立 profile。

其中最要紧的一条：**Every Bot is a profile, but not every profile is a Bot.**

那一个 profile 什么时候变成 Bot？答案在代码里：当它的 profile.yaml 里出现 `ui_meta['hermes-bots']` 块的时候。仓库里有个 `tools/bot_mode_probe.py`，专门探测这件事。

Bot Mode 是八月合入桌面端的功能（当时的提交信息：“bundle Bot Mode as a built-in, default-on plugin”）。它往原语上加的东西很克制：

- 一层展示：花名册、头像（由名字哈希出的确定性面孔）、分组、隐藏状态。这些存在 profile 元数据里，同一台后端上的每一块桌面看到同一套花名册。
- 一条常驻会话：canonical Bot Chat，桌面端源码里的定义是 “one bot, one forever-chat, resolved by exact title”。Bot 出生时正式会话就钉死；在里面敲 `/new` 会被改道成 `/compact`。这段代码的注释里有一句：这份身份契约“已经稳定下来，并且被反复回归过”——出过 bug，加了测试，现在是铁律。
- 一套消息工具：message_agent 私信、群聊房间、定时任务面板。

![官方 demo：Developer 给 Mr Tester 发消息，对方回完还顺手存了一条关于“我”的记忆（来源：NousResearch/Hermes-Bot-Mode）](assets/bot-mode-ui.png)

![新建 Agent：本质上是创建一个 profile——它有“自己的记忆、技能和对话”（来源：NousResearch/Hermes-Bot-Mode）](assets/new-agent-dialog.png)

没有新数据库，没有守护进程，桌面插件那几十个 TypeScript 文件做的全部是读写 profile 原语。所以桌面里能做的事，CLI 里都等价存在：`hermes -p researcher chat` 打开同一个 agent，Bot 的定时任务出现在 `hermes cron list` 里。

命令行上的日常就很直白：

```bash
hermes profile create coder    # 建一位 agent，同时获得 coder 命令别名
coder setup                    # 配置它自己的模型和密钥
coder chat                     # 和它说话
```

三条命令之后，是一套独立的人格、记忆和会话。把它加进桌面花名册，它就成了花名册上的一个 Bot——中间没有注册或迁移动作，它一直就是那个目录。

加的东西不多，但每一条的实现都不浅。以 message_agent 为例，投递不是一次普通调用：消息落进接收方后端的持久 ingress，由它已有的通知轮询器接手；接收方空闲就直接受理，正在跑 turn 就等它收尾。回执分两级——`queued` 只表示“已持久受理”，不等于有回复；投递 ID 和回执存在目标 profile 的 `runtime/bot_live_delivery/` 下，turn 跑完才以 `settled` 收尾。

失败最多自动重试一次，且只重试有机会成功的类别：瞬时故障和上下文超限会重跑（超限那次会先自动压缩），认证、配额、配置错误直接上报，不浪费第二次调用。群聊房间的状态同理——房间的记录、成员和名字会镜像进你 Desktop 连接过的每台网关的 profile 元数据里，按网关分别记版本，两块桌面同时写是合并而不是互相覆盖。

![message_agent 的投递与回执：durable ingress、两级回执与失败重试规则](assets/message-agent-flow.png)

## 原语之上：跨机器、克隆、分发

### 跨机器：导出与导入

带走一位 agent 有现成设施：`/export` 把整个 profile 打包成 tar.gz（密钥剥离），另一台机器 `/import` 就回来了。桌面端导出的包还带主题和窗口布局，回来时看起来也是你的。

### 克隆一位有记忆的 agent

`hermes profile create work --clone` 会复制 config、SOUL、技能，以及 memories/ 下的 MEMORY.md 与 USER.md。文档的解释是：记忆被视为 agent 身份的一部分，和 SOUL.md 同级。

克隆的边界处理得很细：

- OAuth 登录永远不复制。这类登录用单次刷新令牌，“一份拷贝不是第二份凭据，而是同一份凭据有了两个主人——先刷新的那个会把其他拷贝注销”。
- 消息渠道默认不复制。因为一个 bot token 只能属于一个 profile，两个网关拿着同一个 token 长轮询会互相打架。想共享要显式加 `--clone-channels`，运行中的网关会直接拒绝。
- 克隆在隐藏的暂存目录里构建、最后一次原子改名发布，防止运行中的网关扫到一棵半复制的树。

### 分发：把 agent 变成 git 仓库

最远的用法是 distribution：把一位完整的 agent 打包成 git 仓库。作者侧：调试好的 profile 加上 `distribution.yaml`（名字、版本、需要哪些环境变量）、一个 .gitignore，推上 GitHub 打 tag。安装者侧：

```bash
hermes profile install github.com/you/research-bot --alias
```

一条命令装好，填上自己的 API key 就能 `research-bot chat`。作者发新版本，安装者 `hermes profile update research-bot` 拉更新——记忆、会话、密钥不动。

这条命令背后是一串固定步骤：克隆到临时目录、读 `distribution.yaml`、把声明的环境变量逐个对照你的 shell 和已有 `.env`（标出已设置 / 待设置）、在安装侧再执行一遍硬排除清单、写一份 `.env.EXAMPLE`、需要的话建命令别名。装完 `.git/` 会被剥掉——装出来的 profile 不是 git checkout，从机制上杜绝“把自己的 .env 提交进分发的 git 历史”这类事故。

更新按条目合并：作者这次带的技能和 cron 逐个替换同名条目，作者撤掉的条目消失，你自己加的留在原地；`config.yaml` 默认保留你改过的版本，要重置得显式加 `--force-config`。

![安装与更新流程：八步安装管线、按条目合并的更新与双方的文件所有权](assets/install-pipeline.png)

几个关键决定。

为什么是 git？文档里有一段坦诚的比较：试过 tarball、HTTP 归档、自定义格式，最后选 git 的理由是“tag 推送替代了打包+上传+更新索引”、“更新就是一次 fetch”、“私有仓库免费”、“可复现性就是一个 commit SHA”。作者侧发布成本是零。

哪些文件属于谁？SOUL.md、skills/、cron/ 属于作者，更新时被替换；memories/、sessions/、auth.json、.env 属于安装者，永不触碰。即使作者把密钥提交进仓库，安装器一侧也会硬排除这些路径——文档说这是“被回归测试保护的不变量”。

信任边界不装蒜。distribution 目前没有签名，文档直说：“安装一个 distribution 就像安装浏览器扩展或 VS Code 扩展——低摩擦、高权限、信任来源。”从 distribution 来的 cron 不会自动启用（打印出来让你手动开），SOUL 和技能则第一次对话就生效。

## 隐形成本：单写者、改名、多实例

代价落在边界情况里：省掉一个概念，它本来负责的边角现在都得手写。这部分工程量不小，好在都摊在代码里，可以逐笔看。

**一条铁律：一位 agent，一个 profile。** 文档开头的警告写得很重——永远不要让两个 agent 进程指向同一个 profile：“两边都会自动写记忆，各自在会话开始时把对方的写入加载进系统提示词，两位作者互相叠加，直到那份状态不再是你配置过的任何东西。”

改名的成本等于一次身份迁移。profile 从 `coder` 改名到 `dev-bot`，会话命名空间（`agent:<profile>:*`）、网关心跳、投递义务、checkpoint 的项目路径——所有从名字或绝对路径推导出来的东西都要重新编码。仓库里为此有整套 `profile_identity.py`，同时处理改名的镜像和删除的镜像（purge），还要防一个刁钻的竞态：删除 `coder` 之后又建了一个新的 `coder`，清除逻辑必须识别出这是另一个转世，不能把新人格的身份删掉。

这套迁移还有个所有权细节：网关活着时，路由索引在它的内存里并被周期性写回——CLI 直接改库会被覆盖，所以这类迁移由网关自己执行（CLI 通过它的 control socket 发起），网关不在跑，才由 CLI 直接写。失败会打印带重试命令的告警，而不是假装成功。

多 profile 网关是一次逐轮次的隔离工程。一台机器跑几个 profile，可以每个 profile 一个进程，也可以让默认 profile 的网关变成 multiplexer（默认开启）：一个进程服务全部 profile。代价是把 “What is isolated per profile” 做成一张几十行的对照表——每一次对话轮次的凭据、模型、技能、记忆、SOUL、终端设置、命令白名单、代理、日志，都要按“这轮属于哪个 profile”解析，凭据从不跨 profile 共享。

两个 profile 配了同一个 bot token 会怎样？第二个网关启动时被明确拒绝，错误信息点名冲突的 profile；在 multiplexer 里，重复的那个适配器直接被 park 掉（状态标为 `fatal / duplicate_credential`），先来者继续跑。

再往下还有两个细节。会话键带 profile 命名空间（`agent:<profile>:*`，默认 profile 保留历史格式；万一有人把 profile 取名叫 `main`，系统给它 `main~` 前缀避免撞车）。以及，一次被路由的 turn 写出的数据行，落在被路由 profile 自己的 `state.db` 里——哪怕这次写入发生在另一个 profile 启动的进程里。

![一个进程服务多个 profile：逐轮作用域、ContextVar home 覆盖与各自独立的 state.db](assets/multiplex-routing.png)

这些补丁谈不上优雅，但它们把复杂度集中在一个原语周围，没有让它渗透到每一层。

## 从三月到九月

四个时间点：

- 3 月（2026-03-29）：profile 原语落地——“运行多个隔离的 Hermes 实例”（commit #3681）
- 5 月（2026-05-08）：distribution——“通过 git 分享可安装的 profile”（commit #20831）
- 8 月（2026-08-16）：Bot Mode 合入桌面端，成为默认功能
- 9 月（v2026.9.7 起）：Bot Mode 进入发行版高亮，官方 release notes 的标题句是 “your agents become a society, built in”；当月更新继续加深群聊（房间 @提及与回复、房内改成员、房间置顶与分组），网关侧新增按发送者的 profile 路由，还补了 `hermes sessions repair-profiles` 修复跨 profile 遗留状态

`hermes profile list` 现在是这支队伍的名册——模型、网关、别名，以及它从哪个 distribution 装来：

```
 Profile          Model              Gateway    Alias          Distribution
 ◆default         claude-sonnet-4    stopped    —              —
  coder           gpt-5              stopped    coder          —
  research-bot    claude-opus-4      stopped    research-bot   research-bot@1.0.0
```

![Bot Mode 拓扑：从 profile 目录到花名册，再到私信、群聊与跨机器协作](assets/bot-mode-topology.png)

三种用法可以同时存在：个人用（同机多 agent、跨机器 export 同步）、团队用（私有仓库里 review 过的 agent，一人发版全员更新）、公开分发（install 命令本身就是发布文案——文档原话就是 “Tweet the install command”）。

桌面端还能同时连多台机器，Bot 跨机器寻址（`@name-device`），每个成员的对话在自己的机器上跑。

“agent 团队”在这里的样子：不是编排框架里的 DAG，是一台你自己的机器上，几个各有记忆、靠消息往来的常驻个体。团队感是在每个个体足够完整之后出现的。

## 尾声

回到开头：花名册上的 Bot，磁盘上是一个目录。

差别最终落在归属上。过去两年，agent 的身份大多住在别人的数据库里——对话历史、调教出的人设、积累的技能，都绑在某个账号体系上。profile 体系把它换成你能备份、能搬走、能打 tag 的东西：一个目录，或者一个 git 仓库。

签名、锁文件、版本固定，文档里还挂在“尚未发布”；这套原语会走多远，取决于有多少人真的开始打包和分发自己的 agent。至少现在，我知道我的那位住在哪了。

![尾声：花名册上的每一位 Bot，都能把自己的记忆和技能打包带走](assets/epilogue.png)
