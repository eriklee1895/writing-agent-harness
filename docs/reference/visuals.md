# Visuals

生成图片优先使用系统 `$imagegen` skill。不要重建项目重复的 `gpt-image-gen`，除非用户明确要求创建 project-specific fork。

账号信息放在 `.env`。不要打印 secret values。OpenAI 图片相关 key 可能包括：

```text
OPENAI_API_KEY
OPENAI_BASE_URL
```

## Asset Rule

- 图片放在使用它们的 article folder 里，通常是 `assets/`。
- 可复用素材可以放在 `content/assets/`。
- 使用 descriptive alt text。微信公众号 renderer 会把 alt text 转成 caption。
- 避免 `文章配图` 这种 generic caption。

## 微信公众号封面图

尺寸规范（上传压缩后更清晰）：

| 类型 | 标准尺寸 | 比例 | 高清画布 |
|------|----------|------|----------|
| 头条封面（单图文首图） | 900×383px | 2.35:1 | 1080×460px（优选） |
| 次条封面（小图） | 200×200px | 1:1 | — |
| 信息流卡片 | 500×500px | 1:1 | — |

不要用 `1792x1024`（约 1.75:1），`cover-hd` 修正为 `1080x460`（2.35:1）。

> ⚠️ GPT Image API 最宽只支持 `1792x1024`，无法直接生成 2.35:1。`article-illustration` skill 的 `wechat-cover-hd` 预设已内置自动裁剪：生成 `1792x1024` → Pillow 裁剪至 `1080x460`。使用命令：
> ```bash
> uv run .agents/skills/article-illustration/scripts/generate_doc_illustration.py \
>   --size wechat-cover-hd --style-profile watercolor-illustration ...
> ```

- 不要让 image model 直接生成精确中文标题。优先生成干净背景图，再用本地工具 overlay exact text。
- 关键信息要在微信小图预览里仍然可读。

## 正文插图

- 只在图片能帮助理解、传播或渠道呈现时加入。
- 技术文章优先使用简洁信息图、结构图、流程图或有明确语义的插图。
- 移动端优先，避免信息密度过高或文字过多。
- 微信公众号正文图片保存后应上传为 `mmbiz.qpic.cn` URL。
