# Cloudflare workspace and execution backends

Tool: built-in image_gen. New infographic, technical redrawing in Chinese.
Reference 1 (technical structure): `cloudflare-official-backends-reference.png`.
Reference 2 (visual style only): `persistent-workspace-elastic-runtime-v2.png`.
Source article: https://blog.cloudflare.com/cloudflare-computer/
Original figure: https://blog.cloudflare.com/_emdash/api/media/file/01KZ4CFYR52H8M9DBZFH552T63.png

```text
Use case: infographic-diagram. Create a NEW Chinese editorial explanatory diagram based on the technical architecture in reference image 1. Reference image 1 is Cloudflare's official Workspace/execution runtimes diagram: preserve its TECHNICAL MEANING, but redesign its layout and typography. Reference image 2 is STYLE guidance only: ivory background, charcoal typography, terracotta / muted blue / sage panels. Do NOT copy the authorization-service or browser/desktop nodes from image 2; those are not in this Cloudflare-specific diagram.

Format: portrait 4:5, large readable Chinese and short technical labels, mobile-first. Fully opaque warm ivory background #faf9f5. Refined flat technical editorial infographic, clear thin arrows, generous whitespace, no decorative cloud mascots, no robot, no fake screenshot, no dark gradients, no watermark.

Title verbatim: "Cloudflare Computer"
Subtitle verbatim: "共享工作区，两种执行后端"

Upper central full-width workspace panel:
Heading "Workspace"
Large line "共享虚拟文件系统"
Supporting line "SQLite 持久化"
A modest folder/database icon can aid recognition. This is the durable filesystem source of truth.

Below, TWO side-by-side equal panels, both connected to the SAME workspace above.
Use two-way arrows to express filesystem access. Label the LEFT connection exactly "binding · 直接访问".
Label the RIGHT connection exactly "FUSE · 挂载与同步".
Avoid crossed arrows.

LEFT panel heading: "Isolate 执行"
Within it, two clearly grouped short items: "Dynamic Worker" and "just-bash".
Supporting line at bottom: "文件操作 / 数据处理".
Small restrained code/tool icon.

RIGHT panel heading: "Container 执行"
Within it, two grouped items: "Linux 容器" and "computerd".
Supporting line at bottom: "原生程序 / npm".
Small restrained container/tool icon.

A slim centered bar between workspace and executor panels may read "统一 exec 接口" to show both are pluggable execution runtimes. Keep filesystem access arrows distinct and unobstructed.
Bottom takeaway in a large calm band: "同一份文件，不同的执行方式"

Scientific constraints: SQLite is associated ONLY with the workspace, not a separate database in each executor. Isolate works through Workers bindings; container has a FUSE-mounted view and synchronizes changes. Do NOT depict two unrelated workspaces or permanent independent copies. Do NOT imply all container operations run inside the Durable Object process. Do not add credentials, approval services, browser GUI, virtual machines, security guarantees, speed numbers or product availability claims. This is a simplified redrawing, not a literal software screenshot.
All listed text must be exact and legible; no other text needed. Preserve casing of "Workspace", "SQLite", "Dynamic Worker", "just-bash", "Linux", "computerd", "FUSE", "binding", "npm".
```
