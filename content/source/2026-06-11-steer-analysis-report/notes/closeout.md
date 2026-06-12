# Closeout — steer-analysis-report

- Date: 2026-06-11
- Status: draft-created (微信公众号草稿箱)
- WeChat draft appmsgid: **100000195** (agent-flow white style) — final human review pending
- Superseded draft: 100000193 (impact-rational) — delete in 草稿箱
- Author: 李玉恒

## Timeline

1. Rendered `report.zh.md` → WeChat HTML, found 2 of 8 images leaking as raw markdown.
2. Root-caused + fixed a renderer bug (see below), re-rendered → 8/8 images.
3. Created WeChat draft via `baoyu-post-to-wechat` CDP browser path (impact-rational). appmsgid 100000193.
4. User feedback: card + tinted background looks too bright under phone night/dark mode; switch default WeChat style to white/flat.
5. Switched renderer default style to `agent-flow` (white, flat, no cards); re-rendered + re-published. appmsgid 100000195.

## Renderer bug fixed (wechat-article-renderer)

`scripts/render-wechat-article.mjs` fenced-code parser matched the closing fence by exact equality with the **full opening line including the info string** (`fence = trimmed`, then `lines[i].trim() !== fence`). A bare closing ` ``` ` never equals ` ```json `, so a fenced block with an info string and no second identical opener swallowed everything to EOF — here the lone ` ```json ` block ate images 7 and 8 (and trailing content).

Fix: capture the backtick run on the opener and close on any line that is a bare run of `>=` that many backticks (`/^\`{N,}\s*$/`). Standard CommonMark behavior. Verified: 25 code blocks now close correctly, 8/8 images render.

## Style change (durable)

- Renderer `DEFAULT_STYLE` `impact-rational` → `agent-flow`.
- `AGENTS.md` Current Defaults updated: agent-flow (white, flat, no cards) is the tech-article default; rationale = WeChat night mode auto-inverts, light card+background styles glare under dark mode.

## Follow-ups

- User: final review + publish/群发 of appmsgid 100000195; delete superseded 100000193.
- Images live in `.local-archive/2026-06-11-steer-analysis-report/images/` (not in git).

## Cleanup (2026-06-12)

After the user marked the draft as "写好，归档", I finished the closeout pass:

- Moved `content/drafts/steer-analysis-report/` → `.local-archive/2026-06-11-steer-analysis-report/drafts-scratch/`. Reason: stale scratch intermediates, content already promoted into canonical `article.md` / `article.en.md`. Kept rather than deleted because `report.html` is the impact-rational HTML rendered before the renderer bug fix + style switch, useful as a debug reference.
- `.local-archive/.../archive-manifest.md` updated to point at the new drafts-scratch location.
- `content/drafts/` is gitignored, so no git churn; nothing was committed.

## Remaining follow-ups (unchanged)

- User: final review + publish/群发 of appmsgid 100000195; delete superseded 100000193.
