# Feed queue

Watchers write one Atom `<entry>` per file under `working/` (gitignored).
Feed bot merges them into `feed.xml` and pushes.

## File naming

Use a filesystem-safe form of the entry `<id>` (prefer `sha256(<id>).xml`, or a short prefix + hash).
Do not overwrite an existing file with the same name unless correcting the same item.

## Entry file shape

Each file is a single Atom entry fragment (UTF-8), for example:

```xml
<entry xmlns="http://www.w3.org/2005/Atom">
  <title>Short title</title>
  <id>https://example.com/stable-id</id>
  <updated>2026-10-03T12:00:00Z</updated>
  <published>2026-10-03T12:00:00Z</published>
  <link href="https://example.com/stable-id" rel="alternate" type="text/html"/>
  <category term="x"/>
  <content type="html"><![CDATA[
    <p>…</p>
  ]]></content>
</entry>
```

- X: `category term="x"`; `id` and alternate link = post URL; HTML body mirrors the post; embed images with `<img src="…">`; if English, append Japanese translation at the end.
- Mail: `category term="mail"`; `id` = `urn:mail:<Message-ID>` (or similar stable id); alternate link optional (first http(s) URL in body if useful); HTML = rendered mail; if English, add Japanese translation per paragraph.
- Keep titles/subtitles free of account names; do not put X handles or mailbox addresses in the public feed metadata beyond what the content itself needs.
