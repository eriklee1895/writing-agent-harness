# Manus 2.0 / CUE research notes

Research snapshot: 2026-09-29. Article register: Agent / AI technical essay with industry-analysis elements.

## Main finding

CUE's separation is best interpreted as a product-boundary change, not merely a mobile UI simplification. Manus is presented as a project/workbench for producing artifacts; CUE is presented as a roster of persistent personal agents, each with an identity and execution resources. This is an interpretation of the announced interaction model, not a stated internal product rationale.

## Verified product claims

- Manus 2.0 announcement (2026-09-28): Cascade harness, Studio, Cloud Computer, event-triggered Automations, Remote Control / Computer Use, and CUE. Manus says CUE is a separate app built on the same infrastructure; each agent has email, phone number, wallet, and computer; agents can collaborate in group chat; agents can take calls; QR-based service interaction is a stated scenario.
- CUE site: agents can connect services including Gmail, Trip.com, Oura, MyFitnessPal; define responsibilities, connect tools, create routines, and specify approval boundaries. It says agents keep working after logout.
- Manus context-engineering post (2025-07-18): action/observation loop; context management; file system as persistent external context; state machine and constrained tool selection; failures retained as observations. Company-authored technical description, historical and not proof of CUE implementation.
- Manus Sandbox / Cloud Computer docs: task-level sandbox and persistent always-on Cloud Computer are distinct Manus execution modes. Do not equate CUE's “own computer” with a specific isolation architecture without evidence.
- Meta Muse announcement: dedicated per-person VM, separate Sentinel agent, approval controls for sensitive actions, and memory/connected apps. This is Meta's public description, not independent security audit evidence.
- xAI Grok Bot announcement: agents have cloud computers, can operate across apps, can coordinate in groups, and can learn routines from demonstrated workflows.
- Hermes Agent repository: open-source and user-operated agent system; distinguish from managed consumer products.
- Manus announced resumed independent operations on 2026-09-01. The date precedes CUE by four weeks, but no evidence establishes it as the cause of the separate app.

## Early community signals (not representative)

- Manus official subreddit thread on 2026-09-29 includes a commenter mentioning bring-your-own-agent.
- Linux DO thread started 2026-09-28: invite-code entry confusion, questions about whether agents can obtain US numbers, and a report that naming an agent “Manus” led to an email-prefix issue. This is a small forum sample, not a product-quality assessment.
- Search results one day after launch were dominated by launch summaries, affiliate/invite posts, and product announcements. Independent sustained-use reports are not yet available.

## Inferences used in the article

- Independent app likely supports a distinct mental model and interaction loop: hand work to an agent and return for updates, rather than enter a project workspace to create/edit an artifact.
- Agent-specific email / phone / wallet / computer points toward persistent principals and resource ownership at the product level, beyond prompt/persona profiles. The underlying process, identity, memory, credential and VM isolation implementations remain undisclosed.
- Parallel agents can reduce elapsed time only when task decomposition, shared state, handoff and review are designed well. Otherwise they add coordination overhead.
- The September independence announcement may contextualize Manus's renewed positioning, but it is not evidence that independence caused the CUE product boundary.

## Sources

- https://manus.im/blog/introducing-manus-2-0
- https://cue.im/
- https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
- https://manus.im/blog/manus-sandbox
- https://help.manus.im/en/articles/15392111-what-is-the-cloud-computer
- https://manus.im/blog/manus-resumes-independent-operations
- https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/
- https://x.ai/news/introducing-grok-bot
- https://github.com/NousResearch/hermes-agent
- https://www.reddit.com/r/ManusOfficial/comments/1wsm465/introducing_manus_20/
- https://linux.do/t/topic/2964127?tl=zh_CN
