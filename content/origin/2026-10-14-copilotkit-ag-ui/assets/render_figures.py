# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["matplotlib==3.10.3"]
# ///
"""Render article figures from the checked-in data; run with uv run."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent
FONT = Path("/System/Library/Fonts/Hiragino Sans GB.ttc")
if FONT.exists():
    font_manager.fontManager.addfont(str(FONT))
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(FONT)).get_name()
plt.rcParams.update({"svg.fonttype": "path", "axes.unicode_minus": False,
                     "font.size": 13, "figure.facecolor": "#faf9f5",
                     "axes.facecolor": "#faf9f5", "text.color": "#252722",
                     "axes.labelcolor": "#62665c", "xtick.color": "#62665c",
                     "ytick.color": "#62665c"})
INK, MUTED, ACCENT, PALE = "#252722", "#62665c", "#ae5438", "#ccd2c5"

def save(fig, name):
    fig.savefig(ROOT / (name + ".svg"), facecolor=fig.get_facecolor())
    fig.savefig(ROOT / (name + ".png"), dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)

data = json.loads((ROOT / "agui-ecosystem-data.json").read_text())
values = [r["supported_backend_count"] for r in data["snapshots"]]
labels = ["2025 年末", "2026 Q1 末", "2026 Q2 末", "2026 Q3 末", "2026.10.14"]
fig, ax = plt.subplots(figsize=(12, 7.3))
fig.subplots_adjust(left=.09, right=.95, top=.73, bottom=.21)
fig.text(.075,.91,"AG-UI 的后端生态继续扩展",fontsize=25,weight="bold")
fig.text(.075,.85,"README 标记为 Supported 的后端框架 / SDK，按统一口径去重",fontsize=13,color=MUTED)
fig.text(.94,.91,"10 → 15",fontsize=26,color=ACCENT,ha="right",weight="bold")
fig.text(.94,.85,"较去年底增加 5 项（50%）",fontsize=12,color=MUTED,ha="right")
ax.bar(range(5), values, width=.52,color=[PALE]*4+[ACCENT],zorder=3)
for i,value in enumerate(values):
    ax.text(i,value+.42,str(value),ha="center",fontsize=21,weight="bold",color=ACCENT if i==4 else INK)
ax.set_ylim(0,17)
ax.set_yticks([0,5,10,15])
ax.set_ylabel("目录项数",labelpad=12)
ax.set_xticks(range(5),labels)
ax.tick_params(axis="both",length=0,pad=10)
ax.grid(axis="y",color="#dce0d5",linewidth=.8,zorder=0)
for spine in ax.spines.values(): spine.set_visible(False)
fig.text(.075,.11,"不含云部署平台、内置 Agent、语言绑定及进行中项目；LangChain / LangGraph 合并。",fontsize=11,color=MUTED)
fig.text(.075,.065,"统计的是上游目录的记录范围；社区集成计入，不代表厂商原生支持、生产使用量或市场份额。",fontsize=11,color=MUTED)
fig.text(.075,.026,"来源：ag-ui-protocol/ag-ui 的固定 README 提交；截止 2026-10-14。",fontsize=10,color=MUTED)
save(fig,"agui-ecosystem-growth")

fig=plt.figure(figsize=(12,7.7))
ax=fig.add_axes([0,0,1,1])
ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis("off")
ax.text(.065,.93,"CopilotKit 正在扩展自己的产品生态",fontsize=25,weight="bold")
ax.text(.065,.875,"从界面 SDK 延伸到开发工作流、生产运营与应用入口",fontsize=13,color=MUTED)
rows=[
(.69,"用户界面","React  ·  Vue  ·  Angular  ·  React Native","4 类前端 SDK / 绑定"),
(.525,"开发工作流","CLI  ·  Inspector  ·  aimock","搭建、调试与测试"),
(.36,"生产与渠道","Intelligence  ·  Channels","Slack / Teams 已提供正式支持"),
(.195,"应用与学习","OpenBot  ·  Open Intelligent UI  ·  CLiF*","开源应用与改进产品方向"),
]
for y,title,products,detail in rows:
    ax.add_patch(FancyBboxPatch((.06,y),.88,.133,boxstyle="round,pad=0.007,rounding_size=0.012",
                               facecolor="#f0f1e9",edgecolor="#d8ddcf",linewidth=1))
    ax.text(.085,y+.087,title,fontsize=14,color=ACCENT,weight="bold",va="center")
    ax.text(.265,y+.09,products,fontsize=16,va="center",weight="bold")
    ax.text(.265,y+.037,detail,fontsize=11,color=MUTED,va="center")
ax.text(.065,.115,"共同连接基础：AG-UI；可组合 A2UI / MCP Apps，并提供 WebMCP 接入。",fontsize=12,color=INK)
ax.text(.065,.068,"* CLiF 产品操作轨迹为 early access。各产品能力与成熟度不同，图中不表示完整互换或统一交付。",fontsize=10,color=MUTED)
ax.text(.065,.028,"来源：CopilotKit 官方产品页、SDK 文档与发布公告；资料截至 2026-10-14。",fontsize=10,color=MUTED)
save(fig,"copilotkit-ecosystem-map")
print("Rendered 2 SVG + 2 PNG figures from local evidence.")

