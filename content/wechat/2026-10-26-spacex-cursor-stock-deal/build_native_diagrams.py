#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Replace the three WeChat markers with native, mobile-friendly cards.

Run the renderer into index.wechat-preview.html first. The builder deliberately
requires a fresh rendered file: an already substituted preview has no markers.
"""

from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
E = html.escape
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif"


def section(title, subtitle, body):
    return f'''<section style="box-sizing:border-box;max-width:100%;margin:30px 0;padding:18px 0 0;border-top:2px solid #1a1a2e;font-family:{FONT};color:#1a1a2e;">
<p style="margin:0 0 8px;font-size:12px;line-height:1.5;color:#6b7280;letter-spacing:.04em;">移动端静态图解</p>
<h3 style="margin:0 0 8px;font-size:21px;line-height:1.45;font-weight:700;color:#1a1a2e;">{E(title)}</h3>
<p style="margin:0 0 18px;font-size:14px;line-height:1.75;color:#6b7280;">{E(subtitle)}</p>
{body}
</section>'''


timeline_items = [
    ('04-19', '算力合作与 call option', 'SpaceX 提供 GPU，Cursor 投入团队与工作流；获得的是收购权，不是必须收购的义务。'),
    ('06-12', 'SpaceX IPO', '发行价 $135；约 638.9M 股 Class A，净募集约 $85.675B。'),
    ('06-16', '签署合并协议', '隐含股权价值 $60B。签约日不是交割日。'),
    ('08-14', '正式交割', '交割前七个交易日 VWAP 为 $128.65，Exchange Ratio 为 9.7142。'),
    ('10-12', 'X Subscription', 'Premium 定价 $30；既有用户可以保留旧方案。'),
    ('10-22', 'Form S-8 转售注册', '涉及 23,637,224 股；注册不等于实际出售。'),
]
timeline_body = '<div style="border-left:2px solid #2d8cff;padding-left:14px;">' + ''.join(
    f'<div style="margin:0 0 18px;padding:0 0 16px;border-bottom:1px solid #e5e7eb;"><p style="margin:0 0 4px;font-size:12px;color:#6b7280;">2026-{E(date)}</p><p style="margin:0 0 6px;font-size:16px;line-height:1.5;font-weight:650;">{E(title)}</p><p style="margin:0;font-size:14px;line-height:1.75;color:#4b5563;">{E(detail)}</p></div>'
    for date, title, detail in timeline_items
) + '</div><p style="margin:4px 0 0;font-size:13px;line-height:1.75;color:#6b7280;">六个时间点分开看：签约、交割、产品整合与注册披露不是同一件事。</p>'
timeline = section('从算力合作到统一订阅', '用六个短节点代替横向宽表，手机上逐项阅读。', timeline_body)

prices = [('$128.65', '交割前七日 VWAP', '#2d8cff'), ('$141.29', '交割日价格', '#ff6b35'), ('$159.31', '10 月 21 日最近成交价', '#199e70')]
price_html = '<div style="display:flex;gap:8px;align-items:stretch;margin:0 0 18px;">' + ''.join(
    f'<div style="flex:1;min-width:0;padding:10px 8px;border:1px solid #e5e7eb;border-top:3px solid {color};border-radius:8px;background:#fafafa;"><p style="margin:0 0 5px;font-size:18px;line-height:1.3;font-weight:700;">{E(value)}</p><p style="margin:0;font-size:11px;line-height:1.55;color:#6b7280;">{E(label)}</p></div>'
    for value, label, color in prices
) + '</div><p style="margin:0 0 18px;font-size:13px;line-height:1.75;color:#6b7280;">日期与用途不同，三个价格不能直接互换，也不能单独证明实际成交或收益。</p>'
identities = [
    ('SpaceX 老股东', 'Cursor 及潜在协同的权益敞口', '承担股权稀释与整合风险；协同不等于已经兑现的收益。'),
    ('Cursor 普通股 / 优先股持有人', 'SpaceX Class A 股票', '承担价格波动与具体转售条件；股价和能否转售是两件事。'),
    ('已归属、尚未结算的 RSU', '获得并购对价的权利', '重点是税务与结算条件，不是未来归属。'),
    ('Revest 签署者', '相关股份与期权的 75% 被重置为未归属状态', '涉及回购、转让、归属与行权条件；只适用于签署者，不是全部股东。'),
    ('未归属 RSU / RSA / 期权', '转换后的 Rollover awards', '仍需满足服务、归属、行权或结算条件。'),
    ('后来的公开市场买家', '在公开市场买入的股票', '承担自己的入场价与重新定价；买入股票不等于向 SpaceX 支付 $60B。'),
]
identity_html = ''.join(
    f'<div style="margin:0 0 10px;padding:12px 13px;border:1px solid #e5e7eb;border-radius:8px;background:#ffffff;"><p style="margin:0 0 7px;font-size:15px;line-height:1.5;font-weight:650;">{E(title)}</p><p style="margin:0 0 4px;font-size:14px;line-height:1.7;color:#4b5563;"><strong>收到：</strong>{E(receive)}</p><p style="margin:0;font-size:14px;line-height:1.7;color:#4b5563;"><strong>条件：</strong>{E(risk)}</p></div>'
    for title, receive, risk in identities
)
boundary = '<div style="margin-top:14px;padding:12px 13px;border-left:3px solid #199e70;background:#f4f8f6;"><p style="margin:0;font-size:13px;line-height:1.8;color:#4b5563;">S-8 注册不等于实际出售；不同身份不共用同一转售条件；10 月参考价也不能证明持有人亏损。类别可以重叠。</p></div>'
shareholders = section('股票到手，不等于现金到手', '先看三个价格口径，再按六类身份看权益与条件。', price_html + identity_html + boundary)

current_items = [
    ('X', '分发与实时信息'),
    ('Grok Bot · Cursor', 'agent 与编程工作流'),
    ('Grok', '通用模型能力'),
    ('地面算力 · SI', '1.7 GW 铭牌容量（截至 2026-09-30，非利用率）'),
    ('X Subscription', 'Premium $30；既有用户可保留旧方案'),
]
current_html = '<p style="margin:0 0 8px;font-size:14px;font-weight:650;color:#2d8cff;">当前事实</p>' + ''.join(
    f'<div style="padding:9px 0;border-bottom:1px solid #e5e7eb;"><p style="margin:0 0 3px;font-size:14px;line-height:1.6;font-weight:650;">{E(name)}</p><p style="margin:0;font-size:13px;line-height:1.65;color:#6b7280;">{E(detail)}</p></div>'
    for name, detail in current_items
)
plan_html = '''<p style="margin:18px 0 8px;font-size:14px;font-weight:650;color:#ff6b35;">公司规划</p>
<div style="display:flex;gap:10px;margin:0 0 10px;">
<div style="flex:1;min-width:0;padding:12px;border:1px solid #eadfd8;border-radius:8px;background:#fffaf6;"><p style="margin:0 0 5px;font-size:20px;font-weight:700;">最早 2028</p><p style="margin:0;font-size:13px;line-height:1.65;color:#6b7280;">开始部署轨道 AI 算力卫星，不等于规模商用。</p></div>
<div style="flex:1;min-width:0;padding:12px;border:1px solid #eadfd8;border-radius:8px;background:#fffaf6;"><p style="margin:0 0 5px;font-size:20px;font-weight:700;">100 GW / 年</p><p style="margin:0;font-size:13px;line-height:1.65;color:#6b7280;">更长期目标，不是当前能力或承诺时间表。</p></div>
</div>
<p style="margin:0;font-size:13px;line-height:1.75;color:#6b7280;">静态假设：100 kW/公吨、100 公吨/次，对应约 100 万公吨载荷与约 10,000 次发射/年；这只是量级演算，不是部署预测。</p>'''
metrics = ['人才留存', '企业续约', '模型质量与单位算力成本', '订阅现金流', '发射与部署里程碑', '稀释后每股价值']
metrics_html = '<p style="margin:18px 0 8px;font-size:14px;font-weight:650;color:#199e70;">验收指标</p>' + ''.join(
    f'<div style="padding:9px 11px;margin:0 0 8px;border:1px solid #e5e7eb;border-radius:8px;background:#fafafa;"><p style="margin:0;font-size:14px;line-height:1.6;">{E(item)}</p></div>'
    for item in metrics
) + '<p style="margin:4px 0 0;font-size:13px;line-height:1.75;color:#6b7280;">这些是需要继续验证的问题，不是已经实现的生态结论。</p>'
fullstack = section('从应用到轨道算力', '把当前事实、公司计划和验收指标分开，全部改为原生短卡片。', current_html + plan_html + metrics_html)


def portable_local_paths(document: str) -> str:
    """Keep tracked channel HTML independent of the machine that rendered it."""
    pattern = re.compile(r'data-local-path=(["\'])(.*?)\1')

    def replace(match: re.Match[str]) -> str:
        quote, value = match.groups()
        path = Path(html.unescape(value))
        if path.is_absolute():
            try:
                value = path.relative_to(REPO_ROOT).as_posix()
            except ValueError as exc:
                raise ValueError(f"image path is outside the repository: {path}") from exc
        return f"data-local-path={quote}{html.escape(value, quote=True)}{quote}"

    return pattern.sub(replace, document)


def main() -> None:
    preview_path = ROOT / "index.wechat-preview.html"
    preview = preview_path.read_text(encoding="utf-8")
    for marker, snippet in [
        ("[[WECHAT_TIMELINE]]", timeline),
        ("[[WECHAT_SHAREHOLDERS]]", shareholders),
        ("[[WECHAT_FULLSTACK]]", fullstack),
    ]:
        pattern = rf'<p([^>]*)>\s*{re.escape(marker)}\s*</p>'
        preview, count = re.subn(pattern, snippet, preview)
        if count != 1:
            raise SystemExit(f"Expected one placeholder {marker}, found {count}; render article.md first")
    preview = portable_local_paths(preview)
    preview = "\n".join(line.rstrip() for line in preview.splitlines()) + "\n"
    if "[WECHAT_" in preview:
        raise SystemExit("unreplaced WeChat marker remains")
    preview_path.write_text(preview, encoding="utf-8")
    print("NATIVE_WECHAT_DIAGRAMS_INSERTED=3")


if __name__ == "__main__":
    main()
