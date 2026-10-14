# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Normalize supported backend entries from immutable upstream README snapshots."""
import csv
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

PROJECT = Path(__file__).resolve().parents[4]
SCRATCH = PROJECT / "content/drafts/2026-10-14-copilotkit-ag-ui/research/ecosystem-2026"
ASSETS = Path(__file__).resolve().parent
index = SCRATCH / "snapshots.json"
snapshots = (json.loads(index.read_text()) if index.exists() else
             json.loads((ASSETS / "agui-ecosystem-data.json").read_text())["snapshots"])
records = []
for snapshot in snapshots:
    cached = SCRATCH / (snapshot["cutoff"] + "-readme.md")
    if cached.exists():
        body = cached.read_text()
    else:
        url = f"https://raw.githubusercontent.com/ag-ui-protocol/ag-ui/{snapshot['sha']}/README.md"
        with urlopen(Request(url, headers={"User-Agent": "article-research"}), timeout=35) as response:
            body = response.read().decode("utf-8")
    section = body.split("## Frameworks", 1)[1].split("## Agent Interaction Protocols", 1)[0]
    entries = re.findall(r"^\|\s*\[([^\]]+)\].*?\|\s*✅ Supported", section, re.M)
    normalized = sorted(set("LangChain / LangGraph" if x in {"LangGraph", "LangChain"} else x
                            for x in entries if x != "AWS Bedrock AgentCore"))
    records.append({**snapshot, "supported_backend_count": len(normalized),
                    "supported_backends": normalized})
expected = [10, 11, 12, 13, 15]
assert [r["supported_backend_count"] for r in records] == expected
for before, after in zip(records, records[1:]):
    assert set(before["supported_backends"]).issubset(after["supported_backends"])
    after["newly_listed_since_previous_snapshot"] = sorted(
        set(after["supported_backends"]) - set(before["supported_backends"]))
payload = {
    "as_of": "2026-10-14", "metric": "README-listed supported backend frameworks / SDKs",
    "rules": [
        "Count only Supported rows under Frameworks, excluding built-in/direct-to-LLM.",
        "Merge LangGraph and LangChain as the same backend family.",
        "Exclude AWS Bedrock AgentCore: a deployment platform, moved between sections.",
        "Exclude protocol specs, client SDK languages, frontend clients, In Progress and Help Wanted.",
        "Community integrations count as listed support, not vendor-native support.",
        "Snapshots measure directory documentation coverage, not production adoption.",
        "README edits can lag release dates; no claim is made about first availability dates."
    ], "snapshots": records}
(ASSETS / "agui-ecosystem-data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
with (ASSETS / "agui-ecosystem-data.csv").open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["snapshot_date", "supported_backend_count", "readme_commit_date", "readme_sha", "source_url"])
    for r in records:
        writer.writerow([r["cutoff"], r["supported_backend_count"], r["commit_date"], r["sha"], r["source_url"]])
print(json.dumps({"dates": [r["cutoff"] for r in records], "counts": expected}))

