#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
notion-cli helper: wraps `ntn` CLI with the project's learned pitfalls handled.

Why this exists
---------------
Raw `ntn` is powerful but has sharp edges discovered during real use:
  * Empty-bracket inline syntax (`children[]`, `rich_text[]`) hangs on ntn 0.17.x.
  * Non-ASCII / emoji passed via `key=value` inline form can hang; must use JSON body.
  * `ntn pages create` does NOT parse YAML frontmatter into database properties
    (frontmatter is an output-only convention from `ntn pages get`).
  * A block's `type` field is immutable via PATCH — an empty external image block
    can't be turned into a file_upload image block in-place.
  * Cover uses type=`file_upload` (request) / `file` (response) — easy to mix up.
  * Auth via `ntn login` (OAuth, user-delegated) is preferred over NOTION_API_TOKEN
    because it requires no per-page "share connection" step.

This script wraps those patterns so calling code never re-discovers them.

Auth
----
Relies on `ntn`'s own auth resolution:
  1. `NOTION_API_TOKEN` env var (integration token; requires share connection)
  2. `ntn login` keychain session (OAuth user token; no share required)
No token handling in this script itself.

Sentinel-marker image flow
--------------------------
For interleaving text + uploaded images with correct positions:
  1. Caller writes markdown, replacing each image with a sentinel HTML comment:
        leading text
        <!-- __NTN_IMG_0__ -->
        more text
        <!-- __NTN_IMG_1__ -->
  2. `create-page` creates the page from that markdown (sentinels become paragraphs).
  3. `place-images <page-id> --mapping '{"0":"<file_upload_id>",...}'` walks the block
     list, inserts an image block after each sentinel paragraph, then deletes the
     sentinel. Order preserved, positions correct.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from typing import Any

SENTINEL_PREFIX = "NTN_IMG_MARKER_"
SENTINEL_RE = re.compile(rf"^\s*{re.escape(SENTINEL_PREFIX)}(\w+)\s*$")


# ---------- ntn CLI plumbing ----------

def _ntn_bin() -> str:
    ntn = shutil.which("ntn")
    if not ntn:
        die("`ntn` CLI not found in PATH. Install from https://developers.notion.com/cli/get-started/installation "
            "(e.g. `curl -fsSL https://ntn.dev | bash` or `npm install --global ntn`).")
    return ntn


def run_ntn(args: list[str], *, input_bytes: bytes | None = None,
            add_json_flag: bool = False, check: bool = True,
            timeout: int = 60) -> subprocess.CompletedProcess[bytes]:
    cmd = [_ntn_bin()] + args
    if add_json_flag and "--json" not in args and "--plain" not in args:
        cmd.append("--json")
    # If no stdin payload, explicitly set stdin=DEVNULL so `ntn` doesn't block
    # waiting for body input (some ntn subcommands default to reading stdin).
    kwargs: dict[str, Any] = {
        "capture_output": True,
        "check": False,
        "timeout": timeout,
    }
    if input_bytes is not None:
        kwargs["input"] = input_bytes
    else:
        kwargs["stdin"] = subprocess.DEVNULL
    try:
        return subprocess.run(cmd, **kwargs)
    except subprocess.TimeoutExpired:
        die(f"ntn timed out after {timeout}s: {' '.join(cmd)}")


def parse_json_or_die(proc: subprocess.CompletedProcess[bytes], context: str) -> Any:
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace").strip()
        stdout = proc.stdout.decode("utf-8", errors="replace").strip()
        die(f"ntn failed ({context}):\n  stderr: {stderr}\n  stdout: {stdout}")
    try:
        return json.loads(proc.stdout.decode("utf-8"))
    except json.JSONDecodeError as e:
        die(f"ntn returned non-JSON ({context}): {e}\n  stdout: {proc.stdout[:500]!r}")


def parse_plain_or_die(proc: subprocess.CompletedProcess[bytes], context: str) -> str:
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace").strip()
        die(f"ntn failed ({context}): {stderr}")
    return proc.stdout.decode("utf-8").strip()


def die(msg: str, code: int = 1) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def api_call(method: str, path: str, body: dict | None = None,
             query: dict[str, str] | None = None,
             timeout: int = 30) -> Any:
    """Call Notion API via `ntn api`. Always uses --data with JSON body to avoid
    empty-bracket / emoji inline-syntax pitfalls."""
    args = ["api", path]
    if method != "GET":
        args += ["-X", method]
    if query:
        for k, v in query.items():
            args.append(f"{k}=={v}")
    if body is not None:
        args += ["--data", json.dumps(body, ensure_ascii=False)]
    proc = run_ntn(args, timeout=timeout)
    return parse_json_or_die(proc, f"{method} {path}")


# ---------- Subcommands ----------

def cmd_probe(args: argparse.Namespace) -> None:
    """Probe a Notion target (page/database/data-source URL or raw ID). Returns JSON
    describing the target type, permissions, and schema (if a database/data source).

    Resolution order: page → data_source → database. This matches the common case
    (most targets are pages); hitting wrong endpoints returns 404 quickly.
    """
    ref = args.target
    target_id, hinted = _parse_ref(ref)

    def _quick_get(path: str, timeout: int = 10) -> Any | None:
        try:
            proc = run_ntn(["api", path], timeout=timeout)
            if proc.returncode != 0:
                return None
            return json.loads(proc.stdout.decode("utf-8"))
        except Exception:
            return None

    # If caller hinted the kind (e.g. data-source:<id>), use that endpoint first
    order = ["page", "data_source", "database"]
    if hinted:
        order = [hinted] + [k for k in order if k != hinted]

    for kind in order:
        if kind == "page":
            page = _quick_get(f"v1/pages/{target_id}")
            if page is not None:
                parent = page.get("parent", {})
                ptype = parent.get("type")
                info: dict[str, Any] = {
                    "kind": "page",
                    "id": page["id"],
                    "url": page.get("url"),
                    "parent_type": ptype,
                    "parent_id": parent.get(ptype) if ptype else None,
                }
                if ptype == "data_source_id":
                    info["data_source_id"] = parent["data_source_id"]
                # If parent is database_id and caller needs the data source, resolve
                if ptype == "database_id":
                    info["database_id"] = parent["database_id"]
                print(json.dumps(info, ensure_ascii=False, indent=2))
                return
        elif kind == "data_source":
            ds = _quick_get(f"v1/data_sources/{target_id}")
            if ds is not None:
                info = {
                    "kind": "data_source",
                    "id": ds["id"],
                    "title": "".join(t.get("plain_text", "") for t in ds.get("title", [])),
                    "parent": ds.get("parent"),
                    "properties": _simplify_schema(ds.get("properties", {})),
                }
                print(json.dumps(info, ensure_ascii=False, indent=2))
                return
        elif kind == "database":
            db = _quick_get(f"v1/databases/{target_id}")
            if db is not None:
                ds_list = db.get("data_sources", [])
                info = {
                    "kind": "database",
                    "id": db["id"],
                    "title": "".join(t.get("plain_text", "") for t in db.get("title", [])),
                    "data_sources": [{"id": ds["id"], "name": ds.get("name", "")} for ds in ds_list],
                }
                if len(ds_list) == 1:
                    info["default_data_source_id"] = ds_list[0]["id"]
                print(json.dumps(info, ensure_ascii=False, indent=2))
                return

    die(f"Cannot resolve Notion target: {ref!r}. Tried page, database, and data_source IDs. "
        "If using an integration token, ensure the target is shared with your connection; "
        "if using `ntn login` OAuth, run `ntn doctor` to verify auth.")


def _simplify_schema(props: dict) -> dict[str, Any]:
    """Simplify data source property schema for caller friendliness."""
    out: dict[str, Any] = {}
    for name, prop in props.items():
        t = prop.get("type")
        entry: dict[str, Any] = {"type": t, "id": prop.get("id")}
        if t == "select":
            entry["options"] = [o["name"] for o in prop.get("select", {}).get("options", [])]
        elif t == "multi_select":
            entry["options"] = [o["name"] for o in prop.get("multi_select", {}).get("options", [])]
        elif t == "status":
            entry["options"] = [o["name"] for o in prop.get("status", {}).get("options", [])]
        out[name] = entry
    return out


def _parse_ref(ref: str) -> tuple[str, str | None]:
    """Parse a Notion URL or raw ID into (uuid, optional hinted kind).

    Hint comes from ntn-style prefixes (page:, database:, data-source:). For plain
    URLs or raw UUIDs the hint is None and the caller will probe.
    """
    ref = ref.strip()
    # ntn-style refs: page:<id>, database:<id>, data-source:<id>
    m = re.match(r"^(page|database|data-source|data_source):([a-f0-9-]+)$", ref, re.I)
    if m:
        kind = m.group(1).replace("-", "_")
        return m.group(2), kind
    # Notion URL: https://www.notion.so/... or notion://page/...
    # URLs may contain the 32-char hex id with or without dashes
    m = re.search(r"([a-f0-9]{32})", ref.replace("-", ""))
    if m:
        raw = m.group(1)
        return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}", None
    # Raw UUID with dashes
    m = re.match(r"^([a-f0-9-]{36})$", ref)
    if m:
        return m.group(1), None
    die(f"Cannot parse Notion reference: {ref!r}. Pass a Notion URL, ntn-style ref (page:<id>), or a 32/36-char UUID.")


def cmd_upload_file(args: argparse.Namespace) -> None:
    """Upload a local file (or --external-url) and print the file_upload ID."""
    ntn_args = ["files", "create", "--plain"]
    if args.filename:
        ntn_args += ["--filename", args.filename]
    if args.content_type:
        ntn_args += ["--content-type", args.content_type]
    if args.external_url:
        ntn_args += ["--external-url", args.external_url]
        proc = run_ntn(ntn_args, timeout=120)
        out = parse_plain_or_die(proc, "files create (external)")
    else:
        path = args.path
        if not path or path == "-":
            in_bytes = sys.stdin.buffer.read()
        else:
            if not os.path.isfile(path):
                die(f"File not found: {path}")
            with open(path, "rb") as f:
                in_bytes = f.read()
        if not in_bytes:
            die("Refusing to upload empty file.")
        proc = run_ntn(ntn_args, input_bytes=in_bytes, timeout=120)
        out = parse_plain_or_die(proc, "files create")
    # --plain output: ID is tab-separated first field
    file_id = out.split("\t", 1)[0].strip()
    if args.json:
        print(json.dumps({"file_upload_id": file_id}, ensure_ascii=False))
    else:
        print(file_id)


def cmd_create_page(args: argparse.Namespace) -> None:
    """Create a page under a parent from Markdown content (stdin or file)."""
    parent_flag = _build_parent_flag(args.parent) if args.parent else None

    # Read markdown content
    if args.content_file:
        with open(args.content_file, "rb") as f:
            content_bytes = f.read()
    elif args.content:
        content_bytes = args.content.encode("utf-8")
    else:
        content_bytes = sys.stdin.buffer.read()

    ntn_args = ["pages", "create"]
    if parent_flag:
        ntn_args += ["--parent", parent_flag]
    ntn_args += ["--plain"]
    proc = run_ntn(ntn_args, input_bytes=content_bytes, timeout=60)
    out = parse_plain_or_die(proc, "pages create")
    page_id = out.split("\t", 1)[0].strip()

    if args.json:
        print(json.dumps({"page_id": page_id}, ensure_ascii=False))
    else:
        print(page_id)


def _build_parent_flag(parent_ref: str) -> str:
    """Convert a user-provided parent reference (URL, ID, ntn-style) into ntn's
    --parent format: page:<id>, database:<id>, or data-source:<id>.

    Probe order: page first (most common for sub-page writes), then data_source
    (for writing rows into an existing data source), then database (rare case
    where we'd need to pick a default data source).
    """
    parent_ref = parent_ref.strip()
    m = re.match(r"^(page|database|data-source|data_source):", parent_ref, re.I)
    if m:
        return parent_ref.replace("_", "-")
    pid, hinted = _parse_ref(parent_ref)
    if hinted:
        return f"{hinted}:{pid}"

    def _probe(path: str) -> Any | None:
        """Quick GET that returns None on non-200 instead of dying.
        Uses short timeout to avoid hangs on endpoints that aren't meant for this id."""
        try:
            proc = run_ntn(["api", path], timeout=10)
            if proc.returncode != 0:
                return None
            return json.loads(proc.stdout.decode("utf-8"))
        except Exception:
            return None

    # 1) Try as page first
    page = _probe(f"v1/pages/{pid}")
    if page is not None:
        return f"page:{pid}"
    # 2) Try as data source
    ds = _probe(f"v1/data_sources/{pid}")
    if ds is not None:
        return f"data-source:{pid}"
    # 3) Try as database
    db = _probe(f"v1/databases/{pid}")
    if db is not None:
        ds_list = db.get("data_sources", [])
        if len(ds_list) == 1:
            return f"data-source:{ds_list[0]['id']}"
        return f"database:{pid}"
    die(f"Cannot determine kind of parent ref: {parent_ref}. Pass page:<id>, data-source:<id>, or a Notion URL.")


def cmd_get_page(args: argparse.Namespace) -> None:
    """Retrieve page as Markdown (or JSON with --json)."""
    ntn_args = ["pages", "get", args.page_id]
    if args.json:
        ntn_args.append("--json")
    proc = run_ntn(ntn_args, timeout=30)
    if proc.returncode != 0:
        die(f"ntn pages get failed: {proc.stderr.decode('utf-8', errors='replace')}")
    sys.stdout.buffer.write(proc.stdout)


def cmd_trash_page(args: argparse.Namespace) -> None:
    proc = run_ntn(["pages", "trash", args.page_id, "--yes"], timeout=15)
    if proc.returncode != 0:
        die(f"trash failed: {proc.stderr.decode('utf-8', errors='replace')}")
    print(f"Trashed: {args.page_id}")


def cmd_set_cover(args: argparse.Namespace) -> None:
    """Set page cover to a file_upload ID."""
    body = {"cover": {"type": "file_upload", "file_upload": {"id": args.file_id}}}
    api_call("PATCH", f"v1/pages/{args.page_id}", body=body)
    print(f"Cover set: {args.file_id}")


def cmd_set_icon(args: argparse.Namespace) -> None:
    """Set page icon (emoji)."""
    body: dict[str, Any]
    if args.emoji:
        body = {"icon": {"type": "emoji", "emoji": args.emoji}}
    elif args.file_id:
        body = {"icon": {"type": "file_upload", "file_upload": {"id": args.file_id}}}
    elif args.external_url:
        body = {"icon": {"type": "external", "external": {"url": args.external_url}}}
    else:
        die("One of --emoji, --file-id, --external-url is required.")
    api_call("PATCH", f"v1/pages/{args.page_id}", body=body)
    print("Icon set")


def cmd_set_properties(args: argparse.Namespace) -> None:
    """Set database-row properties from a JSON file or JSON literal.

    Expected JSON shape:
        {
          "Name": {"title": [{"text": {"content": "..."}}]},
          "Status": {"select": {"name": "Done"}},
          ...
        }
    Or, for the common flat form supported by this helper:
        {
          "Name": "plain title text",
          "Status": "Done",            // select
          "Tags": ["OCR", "Multi"],    // multi_select
          "Description": {"text": "..."}, // rich_text chunk
          "Published": "2026-06-28",   // date
          "Stars": 4                   // number
        }
    Flat-form values are auto-wrapped into the correct Notion property shape
    based on the data source schema.
    """
    raw = args.properties_json
    if args.properties_file:
        with open(args.properties_file, "r", encoding="utf-8") as f:
            raw = f.read()
    if not raw:
        die("--properties-json or --properties-file required.")
    props_in = json.loads(raw)

    # If caller passed raw Notion-shaped properties, use as-is
    if any(isinstance(v, dict) and "type" not in v and any(
            k in v for k in ("title", "rich_text", "select", "multi_select",
                              "number", "date", "url", "checkbox", "email", "phone_number"))
           for v in props_in.values()):
        props_body = props_in
    else:
        # Flat form: need schema
        data_source_id = args.data_source_id
        if not data_source_id:
            page = api_call("GET", f"v1/pages/{args.page_id}")
            parent = page.get("parent", {})
            if parent.get("type") != "data_source_id":
                die("Flat-form properties require --data-source-id (or the page must live in a data source).")
            data_source_id = parent["data_source_id"]
        ds = api_call("GET", f"v1/data_sources/{data_source_id}")
        schema = ds.get("properties", {})
        props_body = _build_props_from_flat(props_in, schema)

    body = {"properties": props_body}
    api_call("PATCH", f"v1/pages/{args.page_id}", body=body)
    print(json.dumps({"ok": True, "properties_set": list(props_body.keys())}, ensure_ascii=False))


def _build_props_from_flat(flat: dict, schema: dict) -> dict:
    out: dict = {}
    for name, val in flat.items():
        if name not in schema:
            print(f"Warning: property {name!r} not in schema, skipping.", file=sys.stderr)
            continue
        ptype = schema[name]["type"]
        if ptype == "title":
            text = str(val)
            out[name] = {"title": [{"type": "text", "text": {"content": text[:1900]}}]}
        elif ptype == "rich_text":
            if isinstance(val, dict) and "text" in val:
                content = val["text"]
            else:
                content = str(val)
            # Auto-chunk at 1900 chars
            chunks = [content[i:i+1900] for i in range(0, max(1, len(content)), 1900)]
            out[name] = {"rich_text": [
                {"type": "text", "text": {"content": c}} for c in chunks if c
            ]}
        elif ptype == "select":
            out[name] = {"select": {"name": str(val)}}
        elif ptype == "multi_select":
            names = val if isinstance(val, list) else [val]
            out[name] = {"multi_select": [{"name": str(n)} for n in names]}
        elif ptype == "number":
            out[name] = {"number": float(val) if isinstance(val, str) else val}
        elif ptype == "date":
            if isinstance(val, dict):
                out[name] = {"date": val}
            else:
                out[name] = {"date": {"start": str(val)}}
        elif ptype == "url":
            out[name] = {"url": str(val)}
        elif ptype == "checkbox":
            out[name] = {"checkbox": bool(val)}
        elif ptype == "email":
            out[name] = {"email": str(val)}
        elif ptype == "phone_number":
            out[name] = {"phone_number": str(val)}
        else:
            print(f"Warning: property type {ptype} for {name!r} not supported in flat form, passing as-is.", file=sys.stderr)
    return out


def cmd_list_blocks(args: argparse.Namespace) -> None:
    """List blocks of a page or block."""
    blocks = _fetch_all_children(args.block_id)
    if args.json:
        print(json.dumps(blocks, ensure_ascii=False, indent=2))
    else:
        for i, b in enumerate(blocks):
            t = b["type"]
            text = _block_plain_text(b)
            print(f"[{i:3d}] {b['id']}  {t:20s} {text[:60]}")


def _fetch_all_children(block_id: str) -> list[dict]:
    out: list[dict] = []
    cursor = None
    while True:
        query = {"page_size": "100"}
        if cursor:
            query["start_cursor"] = cursor
        resp = api_call("GET", f"v1/blocks/{block_id}/children", query=query)
        out.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return out


def _block_plain_text(b: dict) -> str:
    t = b["type"]
    if t in ("paragraph", "heading_1", "heading_2", "heading_3", "quote",
             "bulleted_list_item", "numbered_list_item", "callout", "to_do",
             "toggle"):
        rt = b.get(t, {}).get("rich_text", [])
        return "".join(x.get("plain_text", "") for x in rt)
    if t == "image":
        img = b.get("image", {})
        caption = "".join(x.get("plain_text", "") for x in img.get("caption", []))
        sub = img.get("type", "")
        return f"[image {sub}] {caption}"
    if t == "divider":
        return "---"
    if t == "code":
        rt = b.get("code", {}).get("rich_text", [])
        lang = b.get("code", {}).get("language", "")
        return f"[code {lang}] " + "".join(x.get("plain_text", "") for x in rt)[:40]
    return ""


def _parse_sentinel_markdown(md: str, images: dict[str, str]) -> tuple[list[tuple[str, str | None]], dict[str, str]]:
    """Split markdown on NTN_IMG_MARKER_<key> sentinel lines.

    Returns (segments, upload_ids placeholder dict).
    segments is a list of (text, image_key_or_None); leading empty text is dropped.
    upload_ids will be populated by _layout_segments_to_page.
    """
    sentinel_line_re = re.compile(rf"^\s*{re.escape(SENTINEL_PREFIX)}(\w+)\s*$", re.MULTILINE)
    segments: list[tuple[str, str | None]] = []
    pos = 0
    for m in sentinel_line_re.finditer(md):
        segments.append((md[pos:m.start()], None))
        segments.append(("", m.group(1)))
        pos = m.end()
    segments.append((md[pos:], None))
    while segments and segments[0][0].strip() == "" and segments[0][1] is None:
        segments.pop(0)
    if not segments:
        die("Markdown content is empty.")
    return segments, {}


def _layout_segments_to_page(page_id: str, segments: list[tuple[str, str | None]],
                             images: dict[str, str], *, verbose: bool,
                             first_segment_goes_to_page_create: bool = False) -> dict[str, str]:
    """Upload images and lay out segments on an existing page.

    If first_segment_goes_to_page_create is True, the caller has already used
    the first text segment as the initial page content (used by create flow);
    this function then processes segments[1:] only. Otherwise it starts with
    the first segment (append) for the overwrite flow.
    """
    start_idx = 1 if first_segment_goes_to_page_create else 0

    # Upload all images referenced
    upload_ids: dict[str, str] = {}
    for _, key in segments:
        if key and key not in upload_ids:
            if key not in images:
                die(f"Sentinel key {key!r} has no matching image path in --image.")
            path = images[key]
            img_id = _upload_single_file(path, content_type=None, filename=None)
            upload_ids[key] = img_id
            if verbose:
                print(f"Uploaded {path} → {img_id}", file=sys.stderr)

    for text, key in segments[start_idx:]:
        if key is not None:
            img_id = upload_ids[key]
            img_block = {
                "object": "block",
                "type": "image",
                "image": {"type": "file_upload", "file_upload": {"id": img_id}},
            }
            api_call("PATCH", f"v1/blocks/{page_id}/children",
                     body={"children": [img_block]}, timeout=30)
        if text:
            _append_markdown(page_id, text, timeout=60)
    return upload_ids


def cmd_create_page_with_images(args: argparse.Namespace) -> None:
    """Create a page with interleaved Markdown text + local file_upload images.

    The Markdown file contains plain-text sentinel lines of the form
    "NTN_IMG_MARKER_<key>" (alone on their own line, with no surrounding markup).
    `--image key=path` maps each key to a local file path.

    Flow:
      1. Upload all images → file_upload IDs
      2. Create page with the first markdown segment
      3. For each subsequent segment, append image block and/or markdown text
      4. Return {page_id, file_upload_ids}
    """
    parent_flag = _build_parent_flag(args.parent) if args.parent else None

    if args.content_file:
        with open(args.content_file, "r", encoding="utf-8") as f:
            md = f.read()
    elif args.content:
        md = args.content
    else:
        md = sys.stdin.read()

    images: dict[str, str] = _collect_images(args.images, args.images_file)

    segments, _ = _parse_sentinel_markdown(md, images)
    if args.verbose:
        print(f"Parsed {len(segments)} segments; image keys: "
              f"{[k for _, k in segments if k]}", file=sys.stderr)

    # Create page with first text segment
    first_text = segments[0][0] if segments[0][1] is None else ""
    page_id = _create_page(parent_flag, first_text, timeout=60)
    if args.verbose:
        print(f"Created page {page_id}", file=sys.stderr)

    upload_ids = _layout_segments_to_page(
        page_id, segments, images, verbose=args.verbose,
        first_segment_goes_to_page_create=True,
    )

    print(json.dumps({
        "ok": True,
        "page_id": page_id,
        "file_upload_ids": upload_ids,
    }, ensure_ascii=False))


def cmd_overwrite_page_with_images(args: argparse.Namespace) -> None:
    """Overwrite an existing page with interleaved Markdown + local images.

    Clears existing children, then appends the sentinel-split content
    (same segment logic as create-page-with-images, but targeting an
    already-existing page — useful for rewriting a database row or a page
    whose ID is already known).
    """
    page_id = args.page_id

    if args.content_file:
        with open(args.content_file, "r", encoding="utf-8") as f:
            md = f.read()
    elif args.content:
        md = args.content
    else:
        md = sys.stdin.read()

    images: dict[str, str] = _collect_images(args.images, args.images_file)
    segments, _ = _parse_sentinel_markdown(md, images)
    if args.verbose:
        print(f"Parsed {len(segments)} segments; image keys: "
              f"{[k for _, k in segments if k]}", file=sys.stderr)

    # Clear existing children
    blocks = _fetch_all_children(page_id)
    for b in reversed(blocks):
        api_call("DELETE", f"v1/blocks/{b['id']}", timeout=15)
    if args.verbose:
        print(f"Cleared {len(blocks)} existing blocks from {page_id}", file=sys.stderr)

    upload_ids = _layout_segments_to_page(
        page_id, segments, images, verbose=args.verbose,
        first_segment_goes_to_page_create=False,
    )

    print(json.dumps({
        "ok": True,
        "page_id": page_id,
        "file_upload_ids": upload_ids,
        "cleared_blocks": len(blocks),
    }, ensure_ascii=False))


def _collect_images(images_args: list[str] | None, images_file: str | None) -> dict[str, str]:
    images: dict[str, str] = {}
    if images_file:
        with open(images_file, "r", encoding="utf-8") as f:
            images = json.load(f)
    for pair in images_args or []:
        if "=" not in pair:
            die(f"--image expects key=path, got {pair!r}")
        k, v = pair.split("=", 1)
        images[k.strip()] = v.strip()
    return images


def _create_page(parent_flag: str | None, content: str, timeout: int = 60) -> str:
    ntn_args = ["pages", "create", "--plain"]
    if parent_flag:
        ntn_args += ["--parent", parent_flag]
    proc = run_ntn(ntn_args, input_bytes=content.encode("utf-8"), timeout=timeout)
    out = parse_plain_or_die(proc, "pages create")
    return out.split("\t", 1)[0].strip()


def _upload_single_file(path: str, *, content_type: str | None = None,
                        filename: str | None = None) -> str:
    ntn_args = ["files", "create", "--plain"]
    if filename:
        ntn_args += ["--filename", filename]
    if content_type:
        ntn_args += ["--content-type", content_type]
    with open(path, "rb") as f:
        in_bytes = f.read()
    if not in_bytes:
        die(f"Refusing to upload empty file: {path}")
    proc = run_ntn(ntn_args, input_bytes=in_bytes, timeout=120)
    out = parse_plain_or_die(proc, f"files create {path}")
    return out.split("\t", 1)[0].strip()


def _append_markdown(page_id: str, markdown_text: str, timeout: int = 60) -> int:
    """Append markdown text to end of page via throwaway-subpage trick.
    Returns number of blocks appended."""
    # 1. Create scratch subpage
    scratch_id = _create_page(f"page:{page_id}", markdown_text, timeout=timeout)
    # 2. Harvest its blocks
    blocks = _fetch_all_children(scratch_id)
    clean = [_strip_block_for_new(b) for b in blocks]
    # 3. Trash scratch
    run_ntn(["pages", "trash", scratch_id, "--yes"], timeout=15)
    # 4. Append clean blocks in batches of 50
    BATCH = 50
    total = 0
    for i in range(0, len(clean), BATCH):
        batch = clean[i:i+BATCH]
        api_call("PATCH", f"v1/blocks/{page_id}/children",
                 body={"children": batch}, timeout=30)
        total += len(batch)
    return total


# Per-block-type server-populated fields that must NOT be sent on PATCH/create.
# Collected from real-world validation errors (whack-a-mole).
_READ_ONLY_TYPE_FIELDS: dict[str, set[str]] = {
    "numbered_list_item": {"list_format"},
    "bulleted_list_item": {"list_format"},
}


def _strip_block_for_new(b: dict) -> dict:
    """Recursively strip a block JSON for reuse as a new-block input."""
    out: dict = {"object": "block"}
    t = b["type"]
    out["type"] = t
    out[t] = _strip_block_ids(b.get(t, {}), type_name=t)
    # Container blocks (table, lists with nested children, toggle, etc.) return
    # has_children=True from GET but do NOT include the nested `children` inline.
    # We must explicitly fetch them, otherwise PATCH fails with
    # "body.children[N].<type>.children should be defined".
    if b.get("has_children"):
        child_blocks = _fetch_all_children(b["id"])
        nested = [_strip_block_for_new(c) for c in child_blocks]
        if nested:
            out[t]["children"] = nested
    return out


def cmd_append_markdown(args: argparse.Namespace) -> None:
    """Append markdown content as new children at the end of a page."""
    if args.content_file:
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read()
    elif args.content:
        content = args.content
    else:
        content = sys.stdin.read()
    n = _append_markdown(args.page_id, content, timeout=60)
    print(json.dumps({"ok": True, "appended_blocks": n}, ensure_ascii=False))


def _strip_block_ids(node: Any, type_name: str | None = None) -> Any:
    """Recursively strip id/parent/created_time etc. so a block payload can be
    re-used as new-block input. Drops null values (paragraph.icon:null breaks
    PATCH validation) and empty children arrays. Also strips per-type read-only
    fields surfaced by Notion's PATCH validator (e.g. numbered_list_item.list_format).

    `type_name` names the block type whose payload `node` represents (None when
    recursing into nested dicts like rich_text spans, file_upload objects).
    """
    if isinstance(node, dict):
        out = {}
        read_only = _READ_ONLY_TYPE_FIELDS.get(type_name or "", set())
        for k, v in node.items():
            if k in ("id", "parent", "created_time", "last_edited_time",
                     "created_by", "last_edited_by", "in_trash", "object",
                     "has_children", "archived", "is_toggleable"):
                continue
            if k in read_only:
                continue
            if v is None:
                continue
            if k == "children" and isinstance(v, list) and len(v) == 0:
                continue
            # Drop broken external references (url == "")
            if k == "external" and isinstance(v, dict) and not v.get("url"):
                continue
            # Presigned S3 URLs expire; drop them (keep file_upload ids, external urls)
            if k == "file" and isinstance(v, dict) and "url" in v and not v.get("file_upload"):
                continue
            out[k] = _strip_block_ids(v, type_name=None)
        return out
    if isinstance(node, list):
        return [_strip_block_ids(v, type_name=None) for v in node if v is not None]
    return node


def cmd_append_blocks(args: argparse.Namespace) -> None:
    """Append raw block JSON (from file or arg) to a page/block."""
    raw = args.blocks_json
    if args.blocks_file:
        with open(args.blocks_file, "r", encoding="utf-8") as f:
            raw = f.read()
    blocks_data = json.loads(raw)
    blocks = blocks_data if isinstance(blocks_data, list) else blocks_data.get("children", [])
    BATCH = 50
    total = 0
    for i in range(0, len(blocks), BATCH):
        batch = blocks[i:i+BATCH]
        api_call("PATCH", f"v1/blocks/{args.block_id}/children",
                 body={"children": batch}, timeout=30)
        total += len(batch)
    print(json.dumps({"ok": True, "appended": total}, ensure_ascii=False))


def cmd_clear_children(args: argparse.Namespace) -> None:
    """Delete all children blocks of a page/block."""
    blocks = _fetch_all_children(args.block_id)
    for b in reversed(blocks):
        api_call("DELETE", f"v1/blocks/{b['id']}", timeout=15)
    print(json.dumps({"ok": True, "deleted": len(blocks)}, ensure_ascii=False))


# ---------- CLI ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ntn_cli",
        description="Wrapper around `ntn` CLI with pitfalls handled and a sentinel-image flow.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("probe", help="Probe a Notion target URL/ID; return its type and schema")
    sp.add_argument("target", help="Notion URL, ntn-style ref (page:<id>), or raw ID")
    sp.set_defaults(func=cmd_probe)

    sp = sub.add_parser("upload-file", help="Upload a local file to Notion; print file_upload ID")
    sp.add_argument("path", nargs="?", help="Path to local file, or - for stdin")
    sp.add_argument("--filename")
    sp.add_argument("--content-type")
    sp.add_argument("--external-url", help="Instead of local bytes, register an external URL (async)")
    sp.add_argument("--json", action="store_true", help="Output JSON instead of raw ID")
    sp.set_defaults(func=cmd_upload_file)

    sp = sub.add_parser("create-page", help="Create a page from Markdown (stdin, --content, or --content-file)")
    sp.add_argument("--parent", help="Parent ref (Notion URL, page:<id>, data-source:<id>)")
    sp.add_argument("--content", help="Markdown content as string")
    sp.add_argument("--content-file", help="Path to markdown file")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_create_page)

    sp = sub.add_parser("get-page", help="Retrieve a page as Markdown")
    sp.add_argument("page_id")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_get_page)

    sp = sub.add_parser("trash-page", help="Move a page to trash")
    sp.add_argument("page_id")
    sp.set_defaults(func=cmd_trash_page)

    sp = sub.add_parser("set-cover", help="Set page cover to a file_upload image")
    sp.add_argument("page_id")
    sp.add_argument("--file-id", required=True, help="file_upload ID from upload-file")
    sp.set_defaults(func=cmd_set_cover)

    sp = sub.add_parser("set-icon", help="Set page icon (emoji or file_upload)")
    sp.add_argument("page_id")
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--emoji")
    g.add_argument("--file-id")
    g.add_argument("--external-url")
    sp.set_defaults(func=cmd_set_icon)

    sp = sub.add_parser("set-properties", help="Set database-row properties from JSON")
    sp.add_argument("page_id")
    sp.add_argument("--properties-json", help="JSON literal of properties (flat or Notion-shaped)")
    sp.add_argument("--properties-file", help="Path to JSON file")
    sp.add_argument("--data-source-id", help="Data source ID (for schema lookup in flat mode)")
    sp.set_defaults(func=cmd_set_properties)

    sp = sub.add_parser("list-blocks", help="List children blocks of a page/block")
    sp.add_argument("block_id")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_list_blocks)

    sp = sub.add_parser("create-page-with-images",
                        help="Create a page with Markdown text interleaved with local images (via NTN_IMG_MARKER_<key> sentinels)")
    sp.add_argument("--parent", required=True, help="Parent ref (Notion URL, page:<id>, data-source:<id>)")
    sp.add_argument("--content", help="Markdown content as string")
    sp.add_argument("--content-file", help="Path to markdown file with NTN_IMG_MARKER_<key> sentinels")
    sp.add_argument("--image", dest="images", action="append", default=[],
                    help="Image mapping as key=path (repeatable; path is a local file)")
    sp.add_argument("--images-file", help="JSON file mapping key → local path")
    sp.add_argument("-v", "--verbose", action="store_true")
    sp.set_defaults(func=cmd_create_page_with_images)

    sp = sub.add_parser("overwrite-page-with-images",
                        help="Overwrite an existing page (clear + append) with Markdown interleaved with images")
    sp.add_argument("--page-id", required=True, help="Existing page/row ID to overwrite")
    sp.add_argument("--content", help="Markdown content as string")
    sp.add_argument("--content-file", help="Path to markdown file with NTN_IMG_MARKER_<key> sentinels")
    sp.add_argument("--image", dest="images", action="append", default=[],
                    help="Image mapping as key=path (repeatable)")
    sp.add_argument("--images-file", help="JSON file mapping key → local path")
    sp.add_argument("-v", "--verbose", action="store_true")
    sp.set_defaults(func=cmd_overwrite_page_with_images)

    sp = sub.add_parser("append-markdown", help="Append Markdown content to end of a page")
    sp.add_argument("page_id")
    sp.add_argument("--content", help="Markdown content as string")
    sp.add_argument("--content-file", help="Path to markdown file")
    sp.set_defaults(func=cmd_append_markdown)

    sp = sub.add_parser("append-blocks", help="Append raw block JSON to a page/block")
    sp.add_argument("block_id")
    sp.add_argument("--blocks-json", help="JSON array of blocks, or {children:[...]}")
    sp.add_argument("--blocks-file")
    sp.set_defaults(func=cmd_append_blocks)

    sp = sub.add_parser("clear-children", help="Delete all children blocks of a page/block")
    sp.add_argument("block_id")
    sp.set_defaults(func=cmd_clear_children)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
