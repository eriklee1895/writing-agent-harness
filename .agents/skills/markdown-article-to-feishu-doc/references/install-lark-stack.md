# 安装 lark-cli + 相关 skill 的最小可走通路径

本 skill 依赖 `lark-cli` 二进制和三个 lark-* skill。Agent **不会替你安装**,因为安装涉及账号授权,需要你手动走完。

## 1. 安装 lark-cli

官方仓库:<https://github.com/larksuite/cli>

### macOS / Linux

```bash
npm install -g @larksuite/cli
```

### Windows

Lark CLI 官方支持 Windows,具体安装见上面的 GitHub README。

### 验证

```bash
lark-cli --version
# 输出类似: lark-cli version 1.0.53
```

## 2. 授权(必须手动完成,agent 无法代劳)

```bash
lark-cli auth login
```

会弹出浏览器进行飞书账号 OAuth 授权。完成后令牌存放在用户配置目录,本机长期有效。

> **不要把令牌提交到 git。** 不要把 `~/.lark-cli/` 或类似目录加入版本控制。

## 3. 安装相关 lark-* skill

本 skill 委派给以下三个 skill,需要确保你的 agent 能调到它们:

| skill | 作用 |
|---|---|
| `lark-doc` | 飞书 docx 创建 / 更新 / fetch / 媒体插入,XML 规范的权威来源 |
| `lark-whiteboard` | 画板编辑(本 skill v1 默认走 mermaid 直传,这个 skill 是 fallback) |
| `lark-shared` | 认证、`auth login`、`--as user/bot` 切换、错误处理 |

**安装命令依调用方 agent 而异**:

| Agent | 命令 |
|---|---|
| Claude Code | `npx skills add lark-doc lark-whiteboard lark-shared` |
| Codex | 参考 Codex 的 skills 安装文档 |
| Hermes / OpenClaw / Pi | 参考各自的 skills 管理命令 |
| 其他 | 查阅你 agent 的 skills 安装方式 |

## 4. 故障排查

### `lark-cli: command not found`

- npm 全局安装路径不在 PATH 里。`npm bin -g` 看一下,把它加到 `~/.zshrc` 或 `~/.bashrc`。
- 用 nvm 时,切换 Node 版本会丢失全局包,重装即可。

### `permission denied` / `missing scope` 类报错

- 没跑 `lark-cli auth login`,或 token 过期。重跑 `auth login`。
- 应用 scope 不够:见 [`lark-shared`](../../../../.claude/skills/lark-shared/SKILL.md) 的 scope 处理章节(具体路径以你的安装为准)。

### 看不到 lark-doc / lark-whiteboard skill

- 上面的 `npx skills add` 没跑成功。
- agent 的 skills 路径不对。`ls ~/.claude/skills/` 或对应 agent 的 skills 目录确认。

## 5. 跨用户 / 跨 tenant 的注意事项

- `+media-insert` 上传的 `file_token` **绑定上传账号**。跨 tenant 转到别人的飞书空间时,这些 token 会失效,图片显示空白。
- 跨用户分享文档前,确保对方的飞书账号能访问图片资源,或重新让对方上传。
