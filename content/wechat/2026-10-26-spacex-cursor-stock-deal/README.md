# 微信原生图解重建

`article.md` 是微信渠道源稿，三个 `[[WECHAT_*]]` 标记对应移动端原生卡片。最终 `index.wechat-preview.html` 是由 renderer 和 `build_native_diagrams.py` 两步生成的派生产物；不要把 canonical 中的 iframe 直接送进公众号。

从仓库根目录执行：

```bash
node .agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs content/wechat/2026-10-26-spacex-cursor-stock-deal/article.md content/wechat/2026-10-26-spacex-cursor-stock-deal/index.wechat-preview.html --style agent-flow
```

```bash
uv run content/wechat/2026-10-26-spacex-cursor-stock-deal/build_native_diagrams.py
```

builder 会要求每个标记恰好出现一次，替换时间线、股东身份和全链条三个区块，并把 renderer 产生的绝对 `data-local-path` 转为可提交的 repo 相对路径。每次重建都先重新运行 renderer；对已经替换完成的 HTML 再跑一次 builder 会主动报错，避免静默覆盖。

进入 publisher 前检查：白底、390px 无横向溢出、无 iframe / 外链 / script / base64、正文图片可解析、封面经过实际尺寸验收。发布状态和草稿信息只写入 `.local-archive/2026-10-26-spacex-cursor-stock-deal/publish-status.md`，不放进本目录。
