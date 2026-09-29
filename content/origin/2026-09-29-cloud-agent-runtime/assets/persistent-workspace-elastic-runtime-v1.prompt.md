# persistent-workspace-elastic-runtime-v1

Tool: built-in image_gen. New image, infographic-diagram. Reference role: existing runtime-isolation-editorial-v2.png is style guidance only.

```text
Use case: infographic-diagram.
Create a NEW technical editorial article body diagram. Provided image is STYLE REFERENCE ONLY; do NOT copy the old three-column virtualization diagram.
Format: portrait 4:5. Uniform fully opaque warm ivory #faf9f5. Match restrained terracotta, slate blue, sage accents, charcoal text, fine lines and modest rounded geometry. LARGE mobile-readable Chinese typography. Flat design, no transparency, no dark haze, no frosted glass, no glow, no logos or robot imagery.

Explain a PROPOSED hybrid agent architecture: durable workspace and separate authorization services support task orchestration that dispatches work to different on-demand executors. This is a conceptual composition, not a vendor architecture.
Use at most seven main nodes. Clear top-to-bottom visual hierarchy:
Title at top, verbatim: "状态长期保留，计算按需运行"
At upper level two separate boxes:
Left heading "持久工作区", supporting text "文件 · 偏好 · 任务记录", folder/document icon.
Right heading "授权服务", supporting text "按任务授予权限", key/lock icon.
Below them, centered node "任务调度".
Connect workspace and task dispatch with a TWO-WAY arrow labeled "读取 / 回写".
Connect authorization to task dispatch with a DASHED line labeled "权限约束"; never place raw secret keys in the workspace.
Below task dispatch, fan out THREE separate downward arrows to three large compact cards. Clearly parallel alternatives, not sequential stages:
Card 1 "轻量计算" with subtitle "isolate"; simple small code icon.
Card 2 "浏览器 / 桌面" with subtitle "按需接续"; browser window icon.
Card 3 "独立任务沙箱" with subtitle "隔离执行"; minimal enclosed workspace icon.
Use two rows for these executor cards if needed to preserve legibility, but maintain clear fan-out routing. Do not connect the three executors to each other.
One calm footer band, verbatim: "保存结果后，可释放或休眠执行环境"
One short caption, verbatim: "组合思路示意；持续服务仍可常驻"

Technical invariants: logical durable state remains while compute can be replaced. Credentials/authorization remain a separate concern. The drawing must NOT imply sandbox means container, all state can be resumed by restoring files, or all servers must sleep. A task can use several executors. No performance numbers or vendor logos. Text verbatim only; no additional invented words. Arrows should be few, obvious, and non-overlapping.
```
