# CopilotKit 文章交付与恢复

源稿：[index.md](index.md)。资料截止日为 2026-10-14，交付与收尾日期为 2026-10-15。

- [博客完整版](https://eriklee-blog.pages.dev/posts/2026-10-14-copilotkit-ag-ui/)，博客生产提交 `e43358c`。
- [飞书文档](https://bytedance.my.larkoffice.com/docx/JjFCdWebSo3ygHxKdqAmH3wyy6e)，回读核对 8 节、7 图、2 张原生表格和 42 个原始来源链接。
- [微信渠道排版](../../wechat/2026-10-14-copilotkit-ag-ui/index.wechat-preview.html)。平台运营信息仅见本机 `.local-archive/2026-10-14-copilotkit-ag-ui/publish-status.md`；本文档不保存草稿编号或后台编辑链接。
- [公开数据说明](https://eriklee-blog.pages.dev/data/2026-10-14-copilotkit-ag-ui/)提供计数规则、固定提交来源、JSON 和 CSV 下载。

## 资产恢复

全文有 7 幅有效视觉：1 张封面、6 张正文图。增长数据图使用确定性 SVG；公众号和飞书使用它的 PNG 副本，因此归档保存 8 个实际使用的图片文件。

7 个 PNG 原文件已移至本机 `.local-archive/2026-10-14-copilotkit-ag-ui/images/`，源 assets 路径保留相对软链接，仍被媒体忽略规则排除。SVG 作为文本资产继续留在 Git，并复制到归档供文章快照独立读取。图像 hash 与归档位置见 [assets/manifest.json](assets/manifest.json)。

跨机器恢复时，复制本机归档并校验 hash，或从博客仓库 `src/content/posts/assets/2026-10-14-copilotkit-ag-ui/` 取回 6 个 PNG。增长 SVG 本身由本仓库 Git 保存；博客 SVG 曾仅做尾部空白归一化，字节 hash 不与源 SVG 混用。渠道用的增长 PNG 可由确定性图表脚本重建。不要删除博客仓库的部署资产，也不要通过软链接直接修改已归档原图。

研究材料、脑暴和 outline 另存本机归档的 `research-and-drafts/`；原 scratch 保留。提示词、生成元数据及数据来源继续由 origin 的轻量文本追踪。

## 渠道适配

- 微信：纯白底、透明正文容器、透明表头与深色文字；每图一份图注，无外链跳转。用户在草稿箱确认格式满意，未据此推断任何后续发表动作。
- 博客：完整来源链接，分类 `AI Frontier`，系列 `CopilotKit Notes`；本地 README 链接改为公开数据说明页。重新同步时需要保留这些渠道适配。
- 飞书：原生一级章节标题、两张可编辑表格、原始尺寸图片，保留独立图注；新增博客原文入口，数据说明链接可在线访问。

收尾复盘见 [2026-10-15-copilotkit-ag-ui-closeout.md](../../../docs/retrospectives/2026-10-15-copilotkit-ag-ui-closeout.md)。
