#!/usr/bin/env python3
"""Merge working/*.xml Atom entry fragments into feed.xml. Exit 0 if nothing to do."""
from __future__ import annotations

import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

NS = "http://www.w3.org/2005/Atom"
ET.register_namespace("", NS)


def q(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def text(el: ET.Element | None, default: str = "") -> str:
    if el is None or el.text is None:
        return default
    return el.text.strip()


def parse_entry(path: Path) -> ET.Element | None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        print(f"skip bad xml {path.name}: {e}", file=sys.stderr)
        return None
    if root.tag != q("entry"):
        # allow bare <entry> without default ns by rewriting
        if root.tag.endswith("entry") or root.tag == "entry":
            root.tag = q("entry")
        else:
            print(f"skip non-entry {path.name}", file=sys.stderr)
            return None
    eid = text(root.find(q("id")))
    if not eid:
        print(f"skip no id {path.name}", file=sys.stderr)
        return None
    return root


def entry_updated(entry: ET.Element) -> str:
    return text(entry.find(q("updated"))) or text(entry.find(q("published"))) or ""


def load_feed(path: Path) -> ET.Element:
    if path.exists():
        return ET.parse(path).getroot()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    feed = ET.Element(q("feed"))
    ET.SubElement(feed, q("title")).text = "Watchers"
    ET.SubElement(feed, q("subtitle")).text = "Digest"
    link_self = ET.SubElement(feed, q("link"))
    link_self.set("href", "https://kiyo-agent.github.io/feeds/feed.xml")
    link_self.set("rel", "self")
    link_self.set("type", "application/atom+xml")
    link_alt = ET.SubElement(feed, q("link"))
    link_alt.set("href", "https://github.com/kiyo-agent/feeds")
    link_alt.set("rel", "alternate")
    link_alt.set("type", "text/html")
    ET.SubElement(feed, q("id")).text = "https://kiyo-agent.github.io/feeds/feed.xml"
    ET.SubElement(feed, q("updated")).text = now
    author = ET.SubElement(feed, q("author"))
    ET.SubElement(author, q("name")).text = "kiyo-agent"
    return feed


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    working = root / "working"
    done = working / "done"
    feed_path = root / "feed.xml"
    working.mkdir(exist_ok=True)
    done.mkdir(exist_ok=True)

    pending = sorted(p for p in working.glob("*.xml") if p.is_file())
    if not pending:
        print("no pending entries")
        return 0

    parsed: list[tuple[Path, ET.Element]] = []
    for path in pending:
        entry = parse_entry(path)
        if entry is not None:
            parsed.append((path, entry))
    if not parsed:
        return 0

    feed = load_feed(feed_path)
    by_id: dict[str, ET.Element] = {}
    others: list[ET.Element] = []
    for child in list(feed):
        if child.tag == q("entry"):
            eid = text(child.find(q("id")))
            if eid:
                by_id[eid] = child
            feed.remove(child)
        else:
            others.append(child)

    added = 0
    for path, entry in parsed:
        eid = text(entry.find(q("id")))
        if eid in by_id:
            # same id: keep existing; drop duplicate queue file
            path.rename(done / path.name)
            continue
        by_id[eid] = entry
        path.rename(done / path.name)
        added += 1

    # rebuild feed children: metadata then entries newest-first
    for child in list(feed):
        feed.remove(child)
    # restore metadata in stable order from others if present, else rebuild minimal
    meta_tags = {q("title"), q("subtitle"), q("link"), q("id"), q("updated"), q("author")}
    for child in others:
        if child.tag in meta_tags or child.tag == q("link"):
            feed.append(child)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    updated_el = feed.find(q("updated"))
    if updated_el is None:
        updated_el = ET.SubElement(feed, q("updated"))
    updated_el.text = now

    entries = list(by_id.values())
    entries.sort(key=entry_updated, reverse=True)
    # cap feed size
    max_entries = 200
    entries = entries[:max_entries]
    for entry in entries:
        feed.append(entry)

    tree = ET.ElementTree(feed)
    ET.indent(tree, space="  ")
    tree.write(feed_path, encoding="utf-8", xml_declaration=True)
    print(f"merged {added} new entries; feed now {len(entries)} entries")
    return 0 if added else 0


if __name__ == "__main__":
    raise SystemExit(main())
