# Runtime isolation — ImageGen editorial variant v1

Generation mode: built-in image_gen; new image; infographic-diagram.
Intended use: article body. Existing Mermaid source and PNG are retained as the technical reference.

```text
Use case: infographic-diagram
Asset type: Chinese technical article body illustration, publication-ready, landscape 3:2. Generate a NEW editorial infographic. This is an explanatory architecture illustration, not a cover or photograph.
Primary request: Beautiful, precise visual comparison of ordinary Linux containers, general-purpose VMs, and microVMs, explaining shared host kernel versus independent guest kernels. Readable at article width; short exact Chinese labels.

Style: refined contemporary technical editorial design, flat-tech-infographic. Warm ivory paper (#faf9f5), charcoal typography, restrained terracotta accents with muted slate blue and sage. Elegant grid, generous margins, strong typography and clear thin dependency arrows. Clean flat panels with slight layer depth; subtle technical linework only. No neon, no glowing server racks, no robots, no decorative clouds, no logos, no watermarks. Do not draw a screenshot or browser chrome.

Composition: top title and short subtitle. Underneath, THREE balanced side-by-side vertical implementation paths on a shared baseline. Use subtle tall column backgrounds for paths, not thick boundaries implying that a VMM is inside guest memory. Below all three, a single full-width shared host-kernel band, then a single full-width physical-hardware band. Arrows mean dependency, not network traffic. Give every label ample whitespace. Distinct muted accents per column, no hierarchy of winners.

Exact visible text, render verbatim:
Title: "Agent 的电脑，底层如何隔离？"
Subtitle: "容器、通用 VM 与 microVM"
Left column heading: "普通容器"
Left column SINGLE application block: "应用与依赖"
Below the application inside same column, concise annotations: "namespaces：资源视图" and "cgroups：资源配额"
A long arrow DIRECTLY from the left application path to the shared host-kernel band, labeled "共享内核". Do NOT add any guest kernel in this left column.
Center column heading: "通用 VM"
Three blocks top to bottom, connected by descending arrows: "应用与依赖", "独立 Guest 内核", "通用设备模型 / VMM".
Right column heading: "microVM"
Three blocks top to bottom, connected by descending arrows: "应用与依赖", "独立 Guest 内核", "精简设备模型 / VMM".
Each VMM block independently connects by a descending arrow to the shared host-kernel band.
Host-kernel band main label: "宿主机 Linux 内核"
Host-kernel band small supporting label: "为 VM 提供 KVM 虚拟化支持"
Physical-hardware band beneath, connected from host-kernel band: "物理 CPU · 内存 · 存储"
Bottom editorial takeaway: "云电脑是产品体验，沙箱是隔离边界。"
Small technical footnote: "Linux / KVM 路径示意；可在 VM 内叠加容器"

Technical invariants: ordinary containers share the host kernel; both VM types have their own guest kernel; microVM simplifies the device/VMM layer, it does not remove the guest kernel. KVM supports the VM paths and is not required for ordinary Linux containers. The diagram is a conceptual dependency stack, not a claim about a particular vendor. NO performance numbers, NO security rankings, NO additional text. All Chinese text must be accurate, crisp, with no clipped labels, overlapping arrows, or illegible small print. Prioritize technical fidelity and refined information design over decorative spectacle.
```
