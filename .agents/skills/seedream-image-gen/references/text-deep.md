# 文字密集型生图 (Text-Dense Image Generation)

适合：技术架构图、地铁/航线图、医疗/数据表、菜单/价目表、日历/排班表、机场信息屏、化学/物理/统计公式、密集 per-cell 数据可视化、长段正文 + 脚注。

Seedream 5.0 Pro 在文字密集型生图上**整体 8.4/10 平均**（14 张图覆盖 4 类别）。**强项是结构化重复标签的渲染**，**弱项是每格非重复内容 + 短 Latin 嵌入长 Chinese + 平衡箭头位置**。

## 核心阈值

| 项 | 阈值 | 失败模式 |
|---|---|---|
| 最小可读中文（2K）| 3-4 字/格 | <10px 实际高度笔画掉（模型自我保护放大，通常不会触发）|
| 网格最大 cell 数（重复标签）| 80+ 稳定 | 同结构（每格同样 4 个 label）能跑到 80+ cells 全过 |
| 网格最大 cell 数（每格唯一内容）| **~30 cells** | 12×12 multiplication table 第 4 行起 69% 错；模型能 hold 几何但 hold 不住语义 |
| 嵌入短 Latin 入长 Chinese body | 不可靠 | `AI` → `AA`，`Application examples` → `Applicatioiexamples` |
| 脚注 / caption / mixed-script 小字 | 不可靠 | wrong-char substitution（`案例`→`寔例`），Latin word 融合 |
| 化学平衡箭头 ⇌ + 折行 | **25% 正确率** | ⇌ 跑到第 2 行开头/重复/丢失 |
| 多公式 1:1 排版 | 4-5 formula OK | 长公式（cov）右边缘 clipping |
| Greek / 数学符号 | 100% 准确 | Σ / √ / ∂ / ∇ / ψ / Ĥ / ₁₂ / ² / × 全部正确 |
| 真实中文地名/品牌 | 触发 input safety block | 见 prompt-engineering 反模式 10 |

## Per-Category 评分

| 类别 | 代表 | 评分 | 甜点 | 硬限 | 反模式 |
|---|---|---|---|---|---|
| 架构/流程图 | TD1 | 9.5 | 3-4 中 + 1 Latin prefix, 4 层重复 | 无 | — |
| 路线/地图 | TD2 | 9 | 3 字中 + pinyin, 10-12 节点, X 交叉 | 真站名被 block | 泛化措辞接受发明名 |
| 临床/数据表 | TD3 | 8.5 | 短中 + 数字 + 单位 (°C, mmHg, %) | 多列空表头 | 别只说"加一列"——列出每行值 |
| 密集菜单 | TD4 | 9.5 | 4 字 + 4 字 + 价, 18-24 项, 3-4 段 | 30+ 项 | 别要 sub-10pt，模型会自保放大 |
| 物理公式 | TD5 | 8 | 6 公式, 2×3 grid, Σ/√/∂/∇/上下标 | 一次性塞所有符号 | 增量 stress test |
| 化学方程 | TD6 | 6 | 上下标, ↑ 箭头, °, 中文 | **多行 ⇌ 位置** | 避免折行；单行 + 3 列 max |
| 数学几何 | TD7 | 10 | 单公式重复, 简单 ² | 无 | — |
| 统计公式 | TD8 | 8.5 | Σ, x̄, ȳ, 上下标, √, 分数, 乘方 | 长公式右 clipping | 加 10% 右 padding |
| 日历网格 | TD9 | 10 | 30 cells, 1-2 位数, 2 字阴历, 1 footer | 无 | 别要周内特殊着色（注意力溢出）|
| 周期表 | TD10 | 9.5 | 4×5 grid, 4 labels/cell | 20 cells 无问题 | 别要"其他中性"——模型会给非金属上色（语义改进）|
| 乘法表 | TD11 | 2 | 12×12 每格唯一乘积 | **~30 cells 唯一内容就崩** | shell 用 Seedream，product 用 PIL 叠 |
| 机场信息屏 | TD12 | 10 | 12×5, parallel time/code/city/gate/status | 无 | — |
| 长段正文 | TD13 | 7 | 4 段 justified 宋体, 纯中文 | 短 Latin 嵌入 | 别让 Seedream 写 body |
| 学术 + 脚注 | TD14 | 6 | 5 段 + 横线 + 6 脚注 | Latin word fusion + 错字 | 脚注 HTML 叠加 |

## Anti-patterns

1. **每格唯一内容 > 30 cells**——grid 几何 hold 住，per-cell 语义飘。**Fix**: shell 用 Seedream，value 用 HTML/PIL 叠加。
2. **化学平衡箭头 ⇌ + 折行**——位置错乱。**Fix**: `2H₂ ⇌ 2H₂O` 单行 + 无内空格 + 单行 per equation。
3. **短 Latin 嵌长 Chinese body**——`AI` 变 `AA`。**Fix**: body 全部真文字 overlay（HTML/CSS/PIL），Seedream 只画背景。
4. **Latin word boundary collapse in footnotes**——`Application examples` 融合。**Fix**: 脚注/caption 全部真文字叠加。
5. **错字替换 in mixed-script 区域**——`案例`→`寔例`。**Fix**: 跟 3、4 同——mixed-script 小字全部 overlay。
6. **只指定列头不列行值**——模型渲列头但留空。**Fix**: prompt 里逐行列值。
7. **1:1 长表达式右 clipping**——长公式超右边。**Fix**: 减到 4 formula，加 10% 右 padding，或 2×3 grid。
8. **真实地名/品牌 list**——输入 safety block。**Fix**: 泛化措辞（"X-station line map"）+ 接受发明名；或后期 marker edit 替换。
9. **硬指定 char count**——`缓存层` 3 字不 4 字。**Fix**: 别硬卡 char count，信任模型语言直觉。
10. **色彩中性/语义混说**——说"其他中性"模型仍按语义上色。**Fix**: 接受模型语义偏好，要严格中性用 SVG。

## 何时放弃 Seedream 改 HTML 叠加

**The 30-cell rule**：每格唯一内容 > 30 cells → 渲染 shell 用 Seedream，values 用 HTML/PIL/matplotlib/canvas 叠加。Seedream 提供**视觉外壳**（页美感/配色/grid 骨架/装饰），HTML 提供**语义内容**（每格正确数值/脚注/嵌入 Latin）。两段合成：Seedream 的色彩和 grid 对齐稳定可复用，只需修正 per-cell text 不动 layout。

| 场景 | Seedream 失败原因 | 推荐 fallback |
|---|---|---|
| 乘法表/计算表格 | per-cell 唯一值 | shell Seedream + 数值 PIL |
| Latin 嵌入 body | 长 Chinese 中短 Latin 替换 | body 真文字 overlay |
| 化学方程 ⇌ | 多行折行坏 | KaTeX/LaTeX 渲 → PNG → composite |
| 学术脚注 | Latin 词融合 + 错字 | 脚注真文字 overlay |
| 1:1 长表达式 | 右 clipping | 减到 4 formula 或 matplotlib math |
| 真实地标/品牌 list | safety block | 泛化措辞 + 接受发明名，或 marker edit 替换 |
| per-cell 数据可视化 | 模型 hold 不住 >30 cells 唯一内容 | 数据层 matplotlib/plotly/canvas，Seedream 画 hero |

## Recipes

### Recipe 1：技术架构图（TD1 9.5/10）

```bash
uv run scripts/seedream_image_gen.py generate \
  --landscape \
  --prompt "Technical architecture diagram, 16:9, clean white background, light pastel
  engineering aesthetic.

  Layer 1 (top): rounded rectangle filled light blue, label 'Client (浏览器 / Browser)'
  Layer 2: rounded rectangle filled light green, label 'API Gateway'
  Layer 3: rounded rectangle filled light orange, label 'Microservices'
  Layer 4: rounded rectangle filled light grey, label 'Database'

  Each layer contains 3 inner boxes side by side, repeating across all 4 layers:
    Left box: 'LB 负载均衡'
    Middle box: 'Auth 鉴权服务'
    Right box: 'Cache 缓存层'

  Down arrows between layers, labeled 'HTTPS', 'gRPC', 'SQL'.
  Monospace arrows, no watermark, no UI elements, 2K"
```

**为什么 9.5：** 3 个内层标签在 4 层重复 → 模型 hold 住；pastel 填充给视觉层级不增文字密度；"rounded rectangle filled X" 给模型明确视觉基元；显式 `no watermark` 防御。

### Recipe 2：30 天中文日历（TD9 10/10）

```bash
uv run scripts/seedream_image_gen.py generate \
  --landscape \
  --prompt "Monthly Chinese calendar poster for 2026年7月, 16:9 horizontal, clean white
  paper background.

  Header (bold, top center): 2026年7月日历

  Grid: 5 rows × 6 columns (30 days total, Monday-Saturday layout)

  Day-of-week column labels across top: 一 二 三 四 五 六 (small black)

  Date cells, 30 total in row-major order (1 through 30):
    Each cell shows: large Arabic numeral + small Chinese lunar date below
    Day 1: 1 / 初一, Day 2: 2 / 初二, ..., Day 21: 21 / 廿一, Day 30: 30 / 三十
    (use 廿 for 21-29)

  Solar terms: 小暑 on day 7, 大暑 on day 23 (small annotation top-right of cell)

  Footer (small, bottom): 月相: 满月 (十五), 新月 (初一)

  Clean calendar grid aesthetic, no watermark, 2K"
```

**为什么 10/10：** 30 cells 同样结构（1 数字 + 2 字阴历）= 完美输入分布；廿 for 21-29 跟模型训练语料一致；footer 短且自包含。

### Recipe 3：机场信息屏（TD12 10/10）

```bash
uv run scripts/seedream_image_gen.py generate \
  --landscape \
  --prompt "Airport flight departure display board, 16:9 horizontal, dark navy
  background #0A1F3D.

  Title top: 'Departures 出发航班'

  12 rows of flight data in monospaced font, columns:
    TIME | FLIGHT NO | DESTINATION | GATE | STATUS
    07:30 | CA1234 | 北京首都 | A12 | 登机中
    08:15 | MU5678 | 上海虹桥 | B07 | 即将登机
    09:00 | CZ9012 | 广州白云 | C03 | 延误
    09:45 | HU7890 | 成都双流 | A05 | 已起飞
    10:30 | CA2345 | 深圳宝安 | B12 | 登机中
    11:15 | MU9876 | 杭州萧山 | A08 | 即将登机
    12:00 | CZ3456 | 西安咸阳 | C07 | 取消
    12:45 | HU1234 | 厦门高崎 | B03 | 已起飞
    13:30 | CA5678 | 青岛胶东 | A15 | 登机中
    14:15 | MU7890 | 昆明长水 | B09 | 即将登机
    15:00 | CZ2345 | 海口美兰 | C11 | 延误
    15:45 | HU4567 | 三亚凤凰 | A03 | 登机中

  Yellow-green dot before STATUS for in-progress, red for cancelled, white for scheduled.
  Monospace LED-board aesthetic, no watermark, 2K"
```

**为什么 10/10：** 12×5 = 60 cells 但每格用**固定小词汇**（城市/航司/状态词），不要求每格唯一计算值。

### Recipe 4：物理/统计公式卡片（TD5 + TD8）

```bash
uv run scripts/seedream_image_gen.py generate \
  --square \
  --prompt "Statistics formula reference card, 1:1 square, clean white paper.

  Header (bold, centered): 常用统计量

  Formula 1: x̄ = Σxᵢ / n          (均值)
  Formula 2: s² = Σ(xᵢ - x̄)² / (n-1)   (方差)
  Formula 3: s = √[Σ(xᵢ - x̄)² / (n-1)]   (标准差)
  Formula 4: r = Σ(xᵢ-x̄)(yᵢ-ȳ) / √[Σ(xᵢ-x̄)²·Σ(yᵢ-ȳ)²]   (相关系数)
  (drop to 4 formulas in 1:1; for 5 use 2×3 grid)

  Each formula on its own line, name left-aligned, formula right-aligned.
  Use proper Unicode: Σ, x̄, ȳ, xᵢ, yᵢ, s², √, ·, superscripts, subscripts.
  Generous right margin (10% padding), no watermark, 2K"
```

**为什么 8-9.5：** 单列布局（1×5）避开折行问题；4 公式稳定通过，第 5 长公式可能右 clipping——降到 4 公式或换 2×3。所有符号 100% 渲染正确。

### Recipe 5：化学方程（TD6 防御版）

```bash
uv run scripts/seedream_image_gen.py generate \
  --landscape \
  --prompt "Chemistry equation reference card, 16:9 horizontal, clean white
  lab-paper background. Title '化学平衡与反应速率' in bold dark blue.

  4 chemical equations, EACH ON A SINGLE LINE (do not wrap), one per row:
    1) N₂+3H₂⇌2NH₃ (高温高压催化剂)
    2) 2SO₂+O₂⇌2SO₃ (400°C 催化剂)
    3) CaCO₃⇌CaO+CO₂↑ (高温煅烧)
    4) 2H₂O⇌2H₂↑+O₂↑ (通电)

  Each equation on a single line with NO internal spaces; subscripts and gas-up
  arrows render as Unicode. Below each: brief Chinese condition label.
  No watermark, 2K"
```

**为什么 6 → 8：** 关键是**单行** + **无内空格** + 显式"do not wrap"——避开 75% 折行 ⇌ 位置错乱。**仍 25% 概率会坏；高保真需求走 LaTeX。**

### Recipe 6：菜单（TD4 9.5/10）

```bash
uv run scripts/seedream_image_gen.py generate \
  --portrait \
  --prompt "Dense Chinese restaurant menu page, 3:4 vertical, warm cream paper
  background with subtle bamboo texture.

  Menu header 「川味家常菜」 in bold dark red (centered, top).

  Sections separated by thin gold horizontal lines: 凉菜 / 热菜 / 主食 / 汤品.

  18 menu items total, each with 4-char Chinese name (left) + 4-char description
  (middle) + RMB price (right, tabular numerals).

  凉菜: 口水鸡 麻辣鲜香 ¥28 / 凉拌黄瓜 清爽开胃 ¥12 / 夫妻肺片 川味经典 ¥32
  热菜: 麻婆豆腐 麻辣下饭 ¥22 / 鱼香肉丝 酸甜微辣 ¥26 / 回锅肉 经典川味 ¥28
  ... (continue all 18 with parallel 4-char name + 4-char desc + price structure)

  11pt Chinese characters, tabular numerals for prices, clean menu typography,
  no watermark, 2K"
```

**为什么 9.5：** 4 字 + 4 字 + 价 = 高度平行的 18 项结构，模型稳定 hold 住。**注意 11pt 实际渲到 14-16pt**（模型自保放大），别硬要 sub-10pt。

### Recipe 7：医学数据表（TD3 防御版）

```bash
uv run scripts/seedream_image_gen.py generate \
  --portrait \
  --prompt "Medical vital signs chart poster, 3:4 vertical, clean white clinical
  background. Header 「生命体征监测报告」 in bold black sans-serif.

  Table with 8 rows × 4 columns, columns 项目 / 数值 / 单位 / 参考范围.
  (DO NOT omit data for 参考范围 column — every row must have a value.)

  Row 1: 体温 36.5 °C 36.0-37.3 °C
  Row 2: 心率 72 次/分 60-100 次/分
  Row 3: 收缩压 120 mmHg 90-139 mmHg
  Row 4: 舒张压 80 mmHg 60-89 mmHg
  Row 5: 呼吸频率 16 次/分 12-20 次/分
  Row 6: 血氧饱和度 98 % 95-100 %
  Row 7: 白细胞 6.5 ×10⁹/L 4-10 ×10⁹/L
  Row 8: 血小板 250 ×10⁹/L 100-300 ×10⁹/L

  Footer in 9pt: 本报告仅供参考,请遵医嘱. Alternating row colors (white/light grey).
  11pt Chinese, tabular numerals, clinical document aesthetic, 2K"
```

**修复 TD3 缺陷**：明确列出**每行每列的值**，避免模型渲列头不填行值。

## Quick Decision Tree

```
你的图属于：
  ├─ 短标签/数字密集（菜单/价目/航班/日历/架构图/数据表）？
  │   └─ YES → 用 Seedream，4-8 字/格 + tabular numerals + 重复结构，9-10/10 稳定
  │
  ├─ 公式/符号密集（物理/统计/数学几何）？
  │   └─ YES → Seedream 可，4 formula/screen, 2×3 grid 优于 1:1, 单行布局
  │
  ├─ 化学/反应方程式含 ⇌？
  │   └─ YES → 接受 25% 失败；高保真需求 KaTeX/LaTeX → PNG 合成
  │
  ├─ 长段正文/多段 body / 脚注 / 短 Latin 嵌入？
  │   └─ YES → Seedream 渲 hero 图 + 背景，body 全部 HTML 真文字 overlay
  │
  ├─ per-cell 唯一计算值（乘法表/数据矩阵）？
  │   └─ YES → Seedream 渲 grid shell + PIL/HTML 叠 per-cell values
  │
  └─ 真实地名/品牌/政治人物 list？
      └─ YES → 泛化措辞 + 接受发明名；或后期 marker edit 替换真名
```