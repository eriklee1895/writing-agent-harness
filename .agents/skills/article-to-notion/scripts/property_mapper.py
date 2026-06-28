#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
Map article metadata to Notion database properties.

Given:
  - Notion data_source schema (raw API shape from GET /v1/data_sources/{id})
  - Article metadata: title, url, summary, tags[], author, date, ...

Produce a properties dict ready for PATCH /v1/pages/{id}.

Behavior:
  - Best-effort heuristic matching. If a semantic field has no matching
    property in the schema, skip it. Never raise on missing match.
  - Respects each Notion property's type (title / rich_text / url / date /
    select / multi_select / etc.) and builds the correct payload shape.
  - For select / multi_select, prefers existing options. If a tag doesn't
    match any existing option, it is added as a new option only when the
    field's options list is non-empty (most user dbs allow this).

Aliases come from references/property-aliases.md; the table here is the
authoritative version.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any, Iterable

# ────────────────────────────────────────────────────────────────────
# Semantic alias table
# ────────────────────────────────────────────────────────────────────

ALIASES: dict[str, tuple[str, ...]] = {
    "title": ("name", "title", "标题", "名称", "名字"),
    "url": ("url", "link", "links", "链接", "原文", "source", "source_url"),
    "summary": ("summary", "description", "intro", "introduction", "介绍",
                "摘要", "描述", "note", "notes"),
    "tags": ("tags", "type", "types", "类型", "标签", "tag",
             "category", "categories"),
    "author": ("author", "account", "source", "来源", "作者",
               "公众号", "账号", "publisher"),
    "date": ("date", "published", "publish_date", "发布时间",
             "发布日期", "创建时间", "created_time"),
}


# ────────────────────────────────────────────────────────────────────
# Matching
# ────────────────────────────────────────────────────────────────────

def _normalize(name: str) -> str:
    return re.sub(r"\s+", "", name.strip().lower())


def find_property(
    schema: dict,
    semantic: str,
    used: set[str],
) -> tuple[str, dict] | None:
    """Find the first property in `schema` matching the given semantic key.

    `used` is the set of property names already assigned, to avoid one
    schema property serving two semantic roles.

    Returns (property_name, property_definition) or None.
    """
    aliases = ALIASES.get(semantic, ())
    norm_aliases = [_normalize(a) for a in aliases]
    # Exact normalized matches first
    for prop_name, prop_def in schema.items():
        if prop_name in used:
            continue
        if _normalize(prop_name) in norm_aliases:
            return prop_name, prop_def
    # Substring fallback (e.g., "url to original" should match "url")
    for prop_name, prop_def in schema.items():
        if prop_name in used:
            continue
        norm = _normalize(prop_name)
        if any(a in norm or norm in a for a in norm_aliases):
            return prop_name, prop_def
    return None


def find_title_property(schema: dict) -> tuple[str, dict] | None:
    """Find the database's title property (every database has exactly one).

    Notion guarantees there is a property with type=title; its name varies.
    """
    for prop_name, prop_def in schema.items():
        if prop_def.get("type") == "title":
            return prop_name, prop_def
    return None


# ────────────────────────────────────────────────────────────────────
# Payload builders per property type
# ────────────────────────────────────────────────────────────────────

def _payload_title(value: str) -> dict:
    return {"title": [{"type": "text", "text": {"content": value[:2000]}}]}


def _payload_rich_text(value: str) -> dict:
    # Notion caps rich_text segments at 2000 chars; chunk if needed.
    parts: list[dict] = []
    for i in range(0, len(value), 1900):
        parts.append({"type": "text", "text": {"content": value[i:i + 1900]}})
    return {"rich_text": parts}


def _payload_url(value: str) -> dict:
    return {"url": value or None}


def _payload_email(value: str) -> dict:
    return {"email": value or None}


def _payload_date(value: str) -> dict:
    """value should be ISO 8601: YYYY-MM-DD or full datetime."""
    if not value:
        return {"date": None}
    # Normalize: try to extract YYYY-MM-DD
    m = re.match(r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})", value)
    if m:
        y, mo, d = m.groups()
        return {"date": {"start": f"{y}-{int(mo):02d}-{int(d):02d}"}}
    return {"date": {"start": value}}


def _payload_select(value: str, options: list[dict]) -> dict:
    if not value:
        return {"select": None}
    # Match an existing option by name (case-insensitive)
    for opt in options:
        if opt.get("name", "").lower() == value.lower():
            return {"select": {"name": opt["name"]}}
    # Allow new option
    return {"select": {"name": value}}


def _payload_multi_select(values: list[str], options: list[dict]) -> dict:
    if not values:
        return {"multi_select": []}
    existing = {opt.get("name", "").lower(): opt["name"] for opt in options}
    chosen: list[dict] = []
    for v in values:
        v = v.strip()
        if not v:
            continue
        # Prefer existing option (case-preserving)
        mapped = existing.get(v.lower(), v)
        chosen.append({"name": mapped})
    return {"multi_select": chosen}


def _build_value(
    prop_def: dict,
    value: Any,
) -> dict | None:
    """Convert `value` into the payload shape for prop_def's type.

    Returns None if value is empty/unsuitable for this type.
    """
    ptype = prop_def.get("type")
    if value is None or value == "" or value == []:
        return None

    if ptype == "title":
        return _payload_title(str(value))
    if ptype == "rich_text":
        return _payload_rich_text(str(value))
    if ptype == "url":
        return _payload_url(str(value))
    if ptype == "email":
        return _payload_email(str(value))
    if ptype == "date":
        return _payload_date(str(value))
    if ptype == "select":
        options = prop_def.get("select", {}).get("options", [])
        if isinstance(value, list):
            value = value[0] if value else ""
        return _payload_select(str(value), options)
    if ptype == "multi_select":
        options = prop_def.get("multi_select", {}).get("options", [])
        if isinstance(value, str):
            # Split comma-separated string
            values = [v.strip() for v in re.split(r"[,，;；]", value) if v.strip()]
        else:
            values = list(value)
        return _payload_multi_select(values, options)
    if ptype == "number":
        try:
            return {"number": float(value)}
        except (TypeError, ValueError):
            return None
    if ptype == "checkbox":
        return {"checkbox": bool(value)}
    if ptype == "phone_number":
        return {"phone_number": str(value)}
    # Unsupported types (people, files, relation, rollup, formula, etc.) — skip
    return None


# ────────────────────────────────────────────────────────────────────
# Top-level builder
# ────────────────────────────────────────────────────────────────────

def build_properties(
    schema: dict,
    metadata: dict,
) -> tuple[dict, dict]:
    """Map metadata onto schema, returning (properties_payload, report).

    metadata keys (all optional):
      - title: str
      - url: str
      - summary: str
      - tags: list[str] | str
      - author: str
      - date: str (any reasonable format)

    Report shape:
      {
        "filled": {"semantic": "property_name", ...},
        "skipped": [{"semantic": "...", "reason": "..."}, ...],
      }
    """
    properties: dict[str, Any] = {}
    used: set[str] = set()
    filled: dict[str, str] = {}
    skipped: list[dict] = []

    # Title is special: required for every page in a database.
    # Always map article title to the schema's title property.
    title_value = metadata.get("title")
    if title_value:
        title_prop = find_title_property(schema)
        if title_prop:
            name, prop_def = title_prop
            payload = _build_value(prop_def, title_value)
            if payload:
                properties[name] = payload
                used.add(name)
                filled["title"] = name
            else:
                skipped.append({"semantic": "title", "reason": "payload empty"})
        else:
            skipped.append({"semantic": "title", "reason": "no title property in schema"})

    # Other semantics
    for semantic in ("url", "summary", "tags", "author", "date"):
        value = metadata.get(semantic)
        if not value:
            continue
        match = find_property(schema, semantic, used)
        if not match:
            skipped.append({"semantic": semantic, "reason": "no matching property"})
            continue
        name, prop_def = match
        payload = _build_value(prop_def, value)
        if payload is None:
            skipped.append({
                "semantic": semantic,
                "reason": f"type {prop_def.get('type')} unsupported or empty value",
            })
            continue
        properties[name] = payload
        used.add(name)
        filled[semantic] = name

    return properties, {"filled": filled, "skipped": skipped}


# ────────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Map article metadata to Notion database properties (debug)."
    )
    parser.add_argument("--schema", required=True,
                        help="Path to a JSON file with the database schema (or '-' for stdin)")
    parser.add_argument("--metadata", required=True,
                        help="Path to a JSON file with metadata (or '-' for stdin)")
    args = parser.parse_args(argv)

    def _read(arg: str) -> dict:
        if arg == "-":
            return json.load(sys.stdin)
        return json.loads(open(arg, encoding="utf-8").read())

    schema = _read(args.schema)
    metadata = _read(args.metadata)
    properties, report = build_properties(schema, metadata)
    print(json.dumps({"properties": properties, "report": report},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
