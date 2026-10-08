# 初稿交接记录

- 日期：2026-09-29。
- Canonical source：[index.md](index.md)。公众号草稿`<见 .local-archive 发布态>`已由用户检查，尚未收到公众号正式发表信息；博客已按用户授权发布，状态记录见下方。
- 文体：Agent / AI Technical Essay，辅助采用 Industry / Frontier Analysis。
- 写作输入：[writing brief v2](../../drafts/2026-09-29-cloud-agent-runtime/writing-brief.md)、[深度研究底稿](../../drafts/2026-09-29-cloud-agent-runtime/deep-research.md)、[来源索引](../../drafts/2026-09-29-cloud-agent-runtime/research-sources.md)。这些drafts文件是本机scratch；正式文章的事实链接已直接进入正文，不依赖scratch链接公开展示。
- 用户选定标题顺序“从Muse到Manus”已保留，指Muse发布到Manus2.0，不暗示Cloud Computer始于2.0。
- 本轮沿用用户标注的ChatGPT Work Cloud与Claude Cowork作为核心对照，另有Muse；Manus为引子，WorkBuddy为用户使用观察，Grok为共享环境边界的短例。

## 编辑取舍

- 以登录摩擦为入口，解释文件、身份、执行现场和任务进度；保留作者最初的VMware印象及其修正。
- 技术前沿只选Cloudflare Computer与TClone，AgentENV、Crab、DeltaBox保留在研究底稿，避免扩展为基础设施/论文综述。
- 按用户反馈，原产品表改为运行方式与实现机制两张技术比较表；三个产品保留在解释段落中。新增容器/VM/microVM分层图，源文件保存在`assets/runtime-isolation.mmd`，PNG由Mermaid确定性渲染。
- 来源核查基线是2026-09-29。本轮依据已保存官方原文/规范/论文复核，没有重新进行全网检索或产品性能测试。
- 不推断Muse/Manus采用Firecracker；不把Cloudflare preview与TClone研究原型写成成熟产品保证。
- Firecracker数字保留测量终点与额外内存口径；恢复范围补充文件快照与内存/进程恢复的区别。

## 本轮自审

- 结构：问题从使用摩擦进入，概念先于具体实现，代价与恢复语义先于趋势判断。
- 事实：Manus4月Cloud Computer与9月2.0分开；Cowork云端与本地模式分开；Work状态复用附带条件；Grok按用户共享电脑。
- 语言：收紧“所有现有软件都可使用”的泛化表述，解释Harness/VMM/isolate，减少无必要缩写。
- Markdown：必需frontmatter齐全，无author、无渠道特定字段；summary来自brief且不超过60字。
- 本轮交付初稿供内容审阅；未进行发布readiness评估或渠道排版。

## 后续编辑重点

读者是否能顺着登录状态自然进入运行时选择；三个产品的对照是否足够清楚；microVM与前沿研究的篇幅是否符合作者预期。当前无需再扩展产品名单。若需要新增精确价格、性能横评或Manus2.0的GUI/底层实现，需先补证据。

## 技术拆解增补（2026-09-29）

- 用户指出需要明确的云电脑vsSandbox比较和技术原理拆解，已补充。
- 第一张表限定比较“持久云电脑”与“按任务供给的Sandbox”两种运行方式；不把所有沙箱定义为临时、无状态或无法运行浏览器。
- 第二张表比较普通容器、通用VM、microVM的内核边界与Agent工程取舍，避免仅按名字给安全性或速度排名。
- 图示采用Linux/KVM示例路径，箭头表示依赖；不暗示所有hypervisor采用同一实现，也不表示厂商实际部署。
- 新增核实来源：[Docker Engine安全](https://docs.docker.com/engine/security/)、[Firecracker设计](https://github.com/firecracker-microvm/firecracker/blob/main/docs/design.md)。cgroups仅说明资源计量与限制，不当成跨进程访问控制。
- 软件镜像与隔离机制分开：OCI/Docker镜像本身不能证明底层是共享内核容器，相关平台案例已在研究底稿的AgentENV部分留证。
- 分层图已用Mermaid CLI 11.4.2渲染并目视检查，修复分组标题遮挡；运行配置为`assets/mermaid-config.json`，调用本机Chrome。两张表的列数和正文图片引用已检查。

## ImageGen配图版本（2026-09-29）

- 根据用户明确指定的imagegen，使用内置工具生成新的文章信息图，未调用API/CLI图片生成路径。
- v1构图与标签符合内容需求，但背景与透明度影响标题、页脚对比度；v2保留内容，改为清晰浅色背景，移除无必要品牌图标。
- v2为1536×1024、RGB不透明PNG，已核对中文标签、容器共享内核以及VM/microVM独立Guest内核的关系。
- 正文改用`assets/runtime-isolation-editorial-v2.png`，原Mermaid源文件和PNG保留作技术参照。完整生成与编辑提示词、工具来源及使用状态保存在assets目录与manifest中。
- 这是助手的内容与图像检查，尚不代表用户已完成最终审阅。

## 本地阅读预览（2026-09-29）

- 使用`article-readiness-check`与`wechat-article-renderer`，style为`warm-editorial`。
- 渠道Markdown与HTML：[article.md](../../wechat/2026-09-29-cloud-agent-runtime/article.md)、[index.html](../../wechat/2026-09-29-cloud-agent-runtime/index.html)。图片指回origin，未复制一份渠道素材。
- 本地URL：`http://127.0.0.1:49268/wechat/2026-09-29-cloud-agent-runtime/index.html`，服务仅绑定loopback；URL依赖本机预览服务仍在运行。
- 390px、430px和1280px浏览器验证没有横向溢出；图片自然尺寸1536×1024、成功加载；无浏览器页面错误。
- 目视检查标题/开场、比较表、图与实现表、桌面排版；图内细注在手机宽度下较小，详细文字可结合正文表格或原图查看。
- HTML无script、外部href、base64图片或table标签；表格为flex div，本地图片保留data-local-path。
- 检查结论与发布前剩余事项见[readiness.md](readiness.md)。尚未进行微信真实草稿箱sanitizer验证。

## 补充正文插图（2026-09-29）

- 用户要求增加插图，内置ImageGen新增两张竖幅4:5信息图，沿用原图作风格参考；全文现在3张正文图。
- `agent-continuity-v1.png`：放在四种连续性定义之后，说明文件/环境、身份/授权、执行现场、任务进度。
- `persistent-workspace-elastic-runtime-v2.png`：放在Cloudflare工作区讨论之后，展示持久工作区、独立授权与按需执行能力的组合。图注明确能力可以组合，浏览器/桌面也可运行在沙箱中，不把这些标签误画成互斥隔离机制。
- 第二张v1的底部文字有误，使用ImageGen定向编辑为“保存结果，按需回收资源”，最终采用v2。
- 两张新图均为1122×1402、RGB不透明；中文标签、连接关系已由助手核对。完整提示词和生成记录在assets/manifest.json。
- 同步重渲染渠道预览。390px viewport下scrollWidth=390，3张图加载正常；两张新图显示尺寸366×457，已分别截图目视检查。

## 首尾插图与表格列宽（2026-09-29）

- 按用户要求在H1之后加入`manus-2-opening-v1.png`，文章结尾加入`agent-work-continues-ending-v1.png`；均为内置ImageGen生成的1672×941、RGB概念插图，不是官方产品截图。全文当前5张插图。
- 运行方式比较表改为20% / 40% / 40%；实现机制表改为20% / 32% / 48%。维度标签精简为四字，首列13px并保持单行，解释列有更多空间；解决microVM被拆成两行的问题。
- 不改共享renderer。文章专用可重现入口为`node content/wechat/2026-09-29-cloud-agent-runtime/render-preview.mjs`，自动同步canonical source、调用shared renderer，并对两张已知表格施加inline宽度；表格形状不符合预期时显式失败。
- 已验证360px与390px宽度，无横向或单元格溢出，5张图片成功加载。目视检查开头图、结尾图和两张表格；没有把首图自动指定为公众号2.35:1发布封面。

## 品牌元素修订（2026-09-29）

- 用户要求插图带有Muse或Manus的logo元素。首图v2在标题旁加入Manus手形glyph，结尾v2加入Muse蓝色标识与名称。
- 使用内置ImageGen，以原插图为edit target、官方标识PNG为reference；非代码后期贴图。生成后核对标识可辨认性与中文标题，未宣称像素级复刻。
- Manus来源：`https://events.manus.im/brand`及其指向的`https://files.manuscdn.com/assets/image/brand/image/Manus-Glyph-Black.svg`。
- Muse来源：从`https://introducing.muse.ai/`当前HTML确认并下载`https://introducing.muse.ai/landing/MuseLogo.svg`。旧`muse.ai/landing/brand/muse-logo.svg`请求停滞，已停止；没有依靠旧网址成功读取的假设。
- 原始SVG与供ImageGen使用的rsvg-convert PNG保存在assets并登记manifest。v1插图保留，正文选用v2；文章图注仍标识为概念插图，不作为官方产品截图。
- 重新运行文章专用render-preview.mjs，保留列宽配置；图片总数仍为5。

## Cloudflare官方图借鉴（2026-09-29）

- 用户希望借鉴Cloudflare Computer官方blog配图；查看了Harness拆分图、Workspace图、两后端图和执行示例截图。
- 选择官方两执行后端图作为技术参考：Workspace虚拟文件系统连接Container的FUSE/同步机制与Isolate的binding/just-bash路径。正文相邻说明补充SQLite持久化依据。
- 使用内置ImageGen重绘为中文竖版`cloudflare-workspace-backends-v1.png`，保持本篇配色，未当作官方原图直接展示。
- 替换该节较泛化的`persistent-workspace-elastic-runtime-v2.png`；旧图保留，manifest标为superseded-retained。图片总数仍为5。
- 图注已注明“参考Cloudflare官方架构图重绘”并链接原文，来源图URL、参考角色、提示词和工具记录均入manifest。

## polish-article精修（2026-09-29）

- 用户明确调用polish-article；按SOUL的Agent技术随笔语域处理，保留作者最初对Manus2.0和VMware的真实感受。
- 章节顺序与核心判断不变。合并过碎的开场段落，压缩概念辨析和产品介绍中的重复解释，替换“值得注意”等空泛转场，加强Cloudflare/环境分支到恢复风险的衔接。
- 结尾缩短为对个人Agent持续接续工作的期待，保留夜间交代、次日继续的具体场景。
- 中文字符约从4500收紧到4000，减少约10%；保留全部16处外部来源链接、5张图的路径与图注、两张表格内容，以及用户已确认的列宽和删除“（概念插图）”的修改。
- 精修前快照：`content/drafts/2026-09-29-cloud-agent-runtime/revisions/before-polish-20260929-145246.md`。比对检查：`content/drafts/2026-09-29-cloud-agent-runtime/qa/polish-check.json`。
- 本轮没有新增产品事实或变更事实核查日期；对原有证据边界的限定保留。
- 重渲染渠道预览，390px检查无横向溢出、5张图片加载正常、两套列宽保留。直接刷新现有应用内预览标签页，没有为精修稿另开标签页。

## 公众号草稿交付（2026-09-29）

- 用户确认精修预览后要求继续，使用wechat-publish-workflow与wechat-article-publisher保存草稿。
- 新增2.35:1横幅封面`assets/wechat-cover-v1.png`（1922×818，RGB），以现有Manus插图与Muse官方标识为参考，由内置ImageGen生成；frontmatter已设置cover。正文5图不变。
- 调用publisher之前检查了title、51字summary、无author frontmatter、默认作者配置存在、封面路径、5图路径、无外链href及自定义列宽。
- 既有工作树含其他任务改动，未为了发布流程清理或提交它们。使用本篇源稿/提交HTML/媒体SHA256检查点，保留精修前与提交版本，作为本次可追溯保障。
- 提交HTML：[index.wechat-preview.html](../../wechat/2026-09-29-cloud-agent-runtime/index.wechat-preview.html)。
- publisher实际结果：正文请求5图、插入5图、CDN5/5，标题回读一致，封面`cover-set`；作者从项目配置读取。已保存appmsgid=`<见 .local-archive 发布态>`。
- 保存后用同一专用profile重新进入后台首页，在“近期草稿”找到同名草稿并打开微信临时预览。正文5图均从mmbiz.qpic.cn加载、natural尺寸非零、显示尺寸非零；两张表保留20/40/40与20/32/48，表格单元格无溢出；正文结尾完整、外部链接数量0。
- 微信真实预览截图仅存本机drafts/qa，不含预览访问链接的发布记录。临时预览链接包含短期访问参数，不作为永久发布URL保存或交付。
- 发布状态与历史：[publish-status.md](../../wechat/2026-09-29-cloud-agent-runtime/publish-status.md)。此次未点击发表/群发，未自动声明原创；留给用户最终检查。

## Blog正式发布（2026-09-29）

- 用户明确指示“我检查草稿箱没问题，继续发布blog”，授权本篇公开发布。
- 已通过erik-blog-publish-workflow同步至`eriklee-blog`，category=`AI Engineering`，description保留已确认summary，draft=false。
- 博客渠道使用ArticleTable与本篇局部首列样式保留两张表的列宽和标签单行；5张正文图、OG封面及来源链接保留，未同步无用工作版本。
- 完整构建、Pagefind与图片优化检查通过；本地390px/1440px验证通过。提交`02c6fce0fee255dcee39928d9a5f4c62d7138a57`已fast-forward进入main并推送，Cloudflare Pages检查success。
- 线上URL：https://eriklee-blog.pages.dev/posts/2026-09-29-cloud-agent-runtime/
- 线上HTTP、5图加载、表格列宽、首页/分类/RSS收录、Pagefind搜索microVM均已核实。
- 博客渠道发布记录：[publish-status.md](../../blog/2026-09-29-cloud-agent-runtime/publish-status.md)。公众号仍独立记录为草稿状态。

## 飞书文档转写（2026-09-29）

- 按用户指令，将博客已发布版转写为用户个人知识库中的新文档：https://bytedance.my.larkoffice.com/docx/YNHsddyDYoCBKUxQwOMmsCZrykh
- 保留7节正文、5张原尺寸图片、两张原生表格及列宽比例、全部来源链接，增加博客原文链接。
- API回读核对102个block、5图、2表、17链接，逐段文本完整，无写入warning。
- 渠道记录：[publish-status.md](../../feishu/2026-09-29-cloud-agent-runtime/publish-status.md)。

## 写作任务收尾（2026-09-29）

- 最终文章、5 张正文图及封面归档至 `.local-archive/2026-09-29-cloud-agent-runtime/`；原 assets 保留相对软链接，引用不变。SHA256 与归档位置已回填 assets/manifest.json。
- Blog published、微信 draft-created、飞书 synced 分别保持；公众号草稿已由用户检查，尚未正式发表。
- 复盘：`docs/retrospectives/2026-09-29-cloud-agent-runtime-closeout.md`。本机任务索引与 skill staleness 记录已更新；未修改共享 skill，未执行 Git 暂存或提交。
