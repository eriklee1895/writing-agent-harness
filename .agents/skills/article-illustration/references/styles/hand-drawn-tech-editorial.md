# 手绘科技随笔（hand-drawn-tech-editorial）

温暖的手绘科技插画风格：彩色铅笔 / 蜡笔在米色或白色纸上的质感，线条 loose 有机，带轻微纸张纹理。画面常以书桌、工作台为场景，出现拟人化的电脑、机器人、终端窗口等科技角色，搭配咖啡杯、笔记本、盆栽、便利贴、小流程图涂鸦。整体像技术随笔里的插画：理性但不冷淡，有编辑感又带手作温度。

适合 AI 工具对比、agent 工作流、技术随笔、编程伙伴、 productivity 笔记等题材。

> 本 preset 提供的是**脚手架而非模具**：默认给出分屏/对坐构图、暖橙-冷蓝分色、拟人设备角色，但当用户 brief 已自带强烈视觉概念时，只保留结构 guardrails（手绘纸质感、避免 corporate flat/ glossy），让出配色、构图和道具自由。

## 结构模板（除非 brief 覆盖，否则保留）

| Guardrail | 默认 Prompt 关键词 |
|---|---|
| 媒介 | `colored pencil and crayon texture on paper`, `hand-drawn editorial illustration`, `loose organic linework`, `slight paper grain` |
| 背景 | `warm off-white or cream paper`, `cozy desk scene`, `generous negative space` |
| 构图 | `split-screen or facing composition`, `two friendly computer characters across a desk`, `left warm / right cool` |
| 主体 | `anthropomorphic monitor or device with a friendly face`, `small robot assistant`, `laptop with chat bubbles or code` |
| 细节 | `coffee mug`, `notebook`, `potted plant`, `floating sticky notes`, `small flowchart doodles`, `binary code snippets as paper notes` |
| 硬约束 | `避免 glossy 数字渲染`, `避免 corporate flat vector`, `避免 photorealism`, `避免厚重阴影和霓虹色` |

## 灵感默认（当 brief 自带风格/氛围/配色时可被覆盖）

| 维度 | 默认方向 |
|---|---|
| 色彩 | 左侧暖橙/奶油/陶土色，右侧冷蓝/石板蓝；线稿为石墨灰或深棕 |
| 氛围 | 温暖编辑式插画、友好协作、技术随笔、手作温度 |
| 道具 | 咖啡杯、笔记本、盆栽、便利贴、小机器人、流程图草图 |

> **覆盖规则：** 如果用户指定了不同的配色、媒介或氛围，就放弃灵感默认，只保留结构模板（手绘纸质感、分屏构图可选、避免 corporate flat/glossy）。

## 可复用 Prompt 模板

```text
一张温暖的手绘科技随笔插画，彩色铅笔和蜡笔在米色纸上的质感，线条 loose 有机，带轻微纸张纹理。

场景：[发生什么——例如 Claude 与 Codex 两个 AI 助手在书桌前协作、一个 agent 与人类共同完成写作工作流]。
构图：[如何布局——例如左右分屏对坐、中央工作台、两个拟人电脑角色面对面]。
细节：[关键道具和角色——例如左侧暖橙显示器握着咖啡杯、右侧冷蓝显示器显示代码、小机器人助手、漂浮的二进制便利贴、墙上的小流程图]。
色彩（默认；如 brief 已指定则覆盖）：左侧暖橙/奶油/陶土色，右侧冷蓝/石板蓝，线稿石墨灰。
氛围（默认；如 brief 已指定则覆盖）：温暖、友好、编辑式技术随笔，有手作温度。
避免：glossy 数字渲染、corporate flat vector、photorealism、厚重阴影、霓虹色。
```

## 与 article-illustration 脚本一起使用

`article-illustration` 的 `--style-profile` 里没有专门的 `hand-drawn-tech-editorial` 选项。推荐做法是把本 preset 的内容写进 `--brief`，并选择一个不会过度限制手绘注释的 profile：

```bash
uv run .agents/skills/article-illustration/scripts/generate_article_illustration.py \
  --style-profile flat-illustration \
  --size doc-hd \
  --title "Claude vs Codex" \
  --brief "一张温暖的手绘科技随笔插画，彩色铅笔和蜡笔在米色纸上的质感。左右分屏：左侧暖橙显示器角色拿着咖啡杯（Claude asterisk logo），右侧冷蓝显示器角色显示代码（Codex cloud logo），桌上散落笔记本、盆栽、便利贴，二进制便签在两者之间漂浮。氛围友好协作，像技术随笔插图。避免 glossy 渲染和 corporate flat vector。" \
  --output-dir output/article-illustration/hand-drawn-tech-editorial
```

如果不需要任何文字/标签，只想保留纯插画氛围，也可用 `--style-profile editorial-atmospheric`。

## 变体

- **更偏信息图 / 流程解释**：保留手绘质感，但强调 `带标签的小流程图`、`虚线箭头`、`便签上的短词`，选择 `--style-profile flat-tech-infographic` 并把本 preset 写进 brief。
- **更暖更个人化**：加入 `暖米色纸张`、`深褐墨水`、`蜂蜜色高光`，减少科技感道具。
- **更冷更技术感**：把暖橙侧换成 `石板蓝/银灰`，让线稿占主导，适合 developer tools 主题。
- **单角色/主视觉**：减少为一个大号拟人设备 + 一个小机器人 + 大量留白。

## 技巧

1. 先把媒介锚定（`colored pencil and crayon texture on paper`），再描述场景，模型更容易锁定风格。
2. 明确写 `loose organic linework` 和 `slight paper grain`，否则容易滑向 polished digital illustration。
3. 需要出现文字时，用中文引号 "" 包裹具体文字；但本风格更适合短词、图标、二进制数字，避免长段落。
4. 用 `--mode reference+text` 加参考图时，把参考图作为风格指引（palette、line quality、spacing），不要复制其 literal 主体。
