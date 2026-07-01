#!/usr/bin/env python3

from __future__ import annotations

import html
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_TARGET = ROOT / "TALK_CATALOG.md"
JSON_TARGET = ROOT / "TALK_CATALOG.json"
HTML_TARGET = ROOT / "index.html"

SOURCE_SUFFIXES = {".rmd", ".qmd", ".tex", ".md"}
OUTPUT_SUFFIXES = {".html", ".pdf", ".pptx"}
ASSET_SUFFIXES = {".css", ".jpg", ".jpeg", ".png", ".svg"}

PUBLISHED_URLS = {
    "20250925 Volz HAWAII Vibe Coding": "http://rpubs.com/raphaelvolz/1347548",
}


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    return [Path(line) for line in output.splitlines() if line.strip()]


def parse_front_matter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip().lower()] = value.strip().strip('"')
    return fields


def markdown_link(path: Path) -> str:
    encoded = str(path).replace(" ", "%20")
    return f"[`{path}`]({encoded})"


def url_path(path: Path) -> str:
    return str(path).replace(" ", "%20")


def file_entry(path: Path) -> dict[str, str]:
    return {
        "path": str(path),
        "url": url_path(path),
        "type": path.suffix.lower()[1:],
    }


def talk_title(folder: str, sources: list[Path]) -> str:
    for source in sources:
        if source.suffix.lower() == ".rmd":
            metadata = parse_front_matter(ROOT / source)
            if metadata.get("title"):
                return metadata["title"]
    return folder


def talk_date(sources: list[Path]) -> str:
    for source in sources:
        if source.suffix.lower() == ".rmd":
            metadata = parse_front_matter(ROOT / source)
            if metadata.get("date"):
                return metadata["date"]
    return ""


def rows_for(paths: list[Path]) -> list[str]:
    rows = ["| File | Type |", "| --- | --- |"]
    for path in sorted(paths, key=lambda item: str(item).lower()):
        rows.append(f"| {markdown_link(path)} | `{path.suffix.lower()[1:]}` |")
    return rows


def collect_talks() -> list[dict[str, Any]]:
    by_folder: dict[str, list[Path]] = defaultdict(list)
    for path in tracked_files():
        if len(path.parts) < 2:
            continue
        if path.parts[0] == "scripts":
            continue
        if path.suffix.lower() not in SOURCE_SUFFIXES | OUTPUT_SUFFIXES | ASSET_SUFFIXES:
            continue
        by_folder[path.parts[0]].append(path)

    talks: list[dict[str, Any]] = []
    for folder in sorted(by_folder):
        files = by_folder[folder]
        sources = sorted(
            [path for path in files if path.suffix.lower() in SOURCE_SUFFIXES],
            key=lambda item: str(item).lower(),
        )
        outputs = sorted(
            [path for path in files if path.suffix.lower() in OUTPUT_SUFFIXES],
            key=lambda item: str(item).lower(),
        )
        assets = sorted(
            [path for path in files if path.suffix.lower() in ASSET_SUFFIXES],
            key=lambda item: str(item).lower(),
        )
        counts = Counter(path.suffix.lower()[1:] for path in files)
        talks.append(
            {
                "folder": folder,
                "folder_url": url_path(Path(folder)),
                "title": talk_title(folder, sources),
                "date": talk_date(sources),
                "published_url": PUBLISHED_URLS.get(folder, ""),
                "sources": [file_entry(path) for path in sources],
                "outputs": [file_entry(path) for path in outputs],
                "assets": [file_entry(path) for path in assets],
                "file_types": dict(sorted(counts.items())),
            }
        )
    return talks


def render_markdown(talks: list[dict[str, Any]]) -> str:
    lines = [
        "# Public Talk Catalog",
        "",
        "This generated catalog summarizes each talk folder, its source files,",
        "rendered outputs, visual assets, and known publication links.",
        "",
        "Regenerate after adding talks or rendered artifacts:",
        "",
        "```sh",
        "python3 scripts/generate_talk_catalog.py",
        "```",
        "",
        "Machine-readable and browser-friendly catalog outputs are generated at",
        "`TALK_CATALOG.json` and `index.html`.",
        "",
        "## Talks",
        "",
        "| Talk | Date | Sources | Outputs | Assets | Published |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]

    for talk in talks:
        published = talk["published_url"]
        published_cell = f"[link]({published})" if published else ""
        lines.append(
            "| "
            + f"[`{talk['folder']}`]({talk['folder_url']}) | {talk['date']} | "
            + f"{len(talk['sources'])} | {len(talk['outputs'])} | {len(talk['assets'])} | "
            + f"{published_cell} |"
        )

    lines.append("")

    for talk in talks:
        counts = talk["file_types"]
        lines.extend(
            [
                f"## {talk['title']}",
                "",
                f"- Folder: `{talk['folder']}`",
                "- File types: "
                + ", ".join(f"`{suffix}` ({count})" for suffix, count in counts.items()),
                "",
                "### Sources",
                "",
            ]
        )
        lines.extend(
            rows_for([Path(item["path"]) for item in talk["sources"]])
            if talk["sources"]
            else ["No source files indexed."]
        )
        lines.extend(["", "### Rendered Outputs", ""])
        lines.extend(
            rows_for([Path(item["path"]) for item in talk["outputs"]])
            if talk["outputs"]
            else ["No rendered outputs indexed."]
        )
        lines.extend(["", "### Assets", ""])
        lines.extend(
            rows_for([Path(item["path"]) for item in talk["assets"]])
            if talk["assets"]
            else ["No assets indexed."]
        )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_json(talks: list[dict[str, Any]]) -> str:
    payload = {
        "generated_by": "scripts/generate_talk_catalog.py",
        "talk_count": len(talks),
        "source_count": sum(len(talk["sources"]) for talk in talks),
        "output_count": sum(len(talk["outputs"]) for talk in talks),
        "asset_count": sum(len(talk["assets"]) for talk in talks),
        "talks": talks,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_file_links(items: list[dict[str, str]]) -> str:
    if not items:
        return "<p class=\"muted\">None indexed.</p>"
    links = []
    for item in items:
        label = html.escape(Path(item["path"]).name)
        file_type = html.escape(item["type"])
        url = html.escape(item["url"], quote=True)
        links.append(f'<li><a href="{url}">{label}</a><span>{file_type}</span></li>')
    return "<ul class=\"file-list\">" + "".join(links) + "</ul>"


def render_html(talks: list[dict[str, Any]]) -> str:
    cards = []
    for talk in talks:
        published = ""
        if talk["published_url"]:
            url = html.escape(talk["published_url"], quote=True)
            published = f'<a class="pill" href="{url}">Published copy</a>'
        primary_output = ""
        if talk["outputs"]:
            first_output = talk["outputs"][0]
            primary_output = (
                f'<a class="primary-link" href="{html.escape(first_output["url"], quote=True)}">'
                "Open rendered talk"
                "</a>"
            )
        file_types = ", ".join(
            f"{html.escape(kind)} ({count})" for kind, count in talk["file_types"].items()
        )
        cards.append(
            f"""
            <article class="talk-card">
              <div class="talk-card-header">
                <div>
                  <p class="eyebrow">{html.escape(talk["date"] or "Undated")}</p>
                  <h2>{html.escape(talk["title"])}</h2>
                </div>
                {published}
              </div>
              <p class="folder">{html.escape(talk["folder"])}</p>
              <div class="metrics" aria-label="Talk artifact counts">
                <span><strong>{len(talk["sources"])}</strong> sources</span>
                <span><strong>{len(talk["outputs"])}</strong> outputs</span>
                <span><strong>{len(talk["assets"])}</strong> assets</span>
              </div>
              <p class="muted">File types: {file_types}</p>
              {primary_output}
              <div class="artifact-grid">
                <section>
                  <h3>Sources</h3>
                  {render_file_links(talk["sources"])}
                </section>
                <section>
                  <h3>Outputs</h3>
                  {render_file_links(talk["outputs"])}
                </section>
              </div>
            </article>
            """.strip()
        )

    return (
        """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Public Talks Catalog</title>
    <link rel="icon" href="data:," />
    <style>
      :root {
        color-scheme: light;
        --bg: #eef3f6;
        --ink: #1f2933;
        --muted: #65717d;
        --line: #d2dee6;
        --paper: #ffffff;
        --accent: #246b73;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        background: var(--bg);
        color: var(--ink);
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        line-height: 1.55;
      }
      main {
        margin: 0 auto;
        max-width: 1120px;
        padding: 3rem 1rem;
      }
      .hero {
        border-bottom: 1px solid var(--line);
        margin-bottom: 1.5rem;
        padding-bottom: 1.5rem;
      }
      h1, h2, h3, p { margin: 0; }
      h1 {
        font-size: clamp(2rem, 6vw, 4.5rem);
        letter-spacing: 0;
        line-height: 1;
      }
      .lead {
        color: var(--muted);
        font-size: 1.05rem;
        margin-top: 0.9rem;
        max-width: 760px;
      }
      .talk-grid {
        display: grid;
        gap: 1rem;
      }
      .talk-card {
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: 0 12px 30px rgba(31, 41, 51, 0.07);
        padding: 1.25rem;
      }
      .talk-card-header {
        align-items: flex-start;
        display: flex;
        gap: 1rem;
        justify-content: space-between;
      }
      .eyebrow {
        color: var(--accent);
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      h2 {
        font-size: 1.45rem;
        letter-spacing: 0;
        line-height: 1.15;
        margin-top: 0.25rem;
      }
      h3 {
        font-size: 0.95rem;
        margin-bottom: 0.45rem;
      }
      a { color: var(--accent); font-weight: 700; }
      .folder, .muted {
        color: var(--muted);
        margin-top: 0.6rem;
      }
      .metrics {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        margin-top: 1rem;
      }
      .metrics span, .pill {
        border: 1px solid var(--line);
        border-radius: 999px;
        min-height: 2rem;
        padding: 0.35rem 0.75rem;
      }
      .pill {
        color: var(--accent);
        text-decoration: none;
        white-space: nowrap;
      }
      .primary-link {
        display: inline-flex;
        margin-top: 1rem;
      }
      .artifact-grid {
        display: grid;
        gap: 1rem;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        margin-top: 1.2rem;
      }
      .file-list {
        display: grid;
        gap: 0.35rem;
        list-style: none;
        margin: 0;
        padding: 0;
      }
      .file-list li {
        align-items: baseline;
        border-top: 1px solid var(--line);
        display: flex;
        gap: 0.75rem;
        justify-content: space-between;
        padding-top: 0.45rem;
      }
      .file-list span {
        color: var(--muted);
        font-size: 0.78rem;
        text-transform: uppercase;
      }
      @media (max-width: 760px) {
        main { padding: 2rem 1rem; }
        .talk-card-header { display: block; }
        .pill { display: inline-flex; margin-top: 0.75rem; }
        .artifact-grid { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>Public Talks</h1>
        <p class="lead">
          Generated index of public talk sources, rendered outputs, assets, and
          publication links. The same generator also writes TALK_CATALOG.md and
          TALK_CATALOG.json so CI can detect drift.
        </p>
      </section>
      <section class="talk-grid" aria-label="Talk catalog">
"""
        + "\n".join(cards)
        + """
      </section>
    </main>
  </body>
</html>
"""
    )


def main() -> None:
    talks = collect_talks()
    MARKDOWN_TARGET.write_text(render_markdown(talks), encoding="utf-8")
    JSON_TARGET.write_text(render_json(talks), encoding="utf-8")
    HTML_TARGET.write_text(render_html(talks), encoding="utf-8")


if __name__ == "__main__":
    main()
