#!/usr/bin/env python3

from __future__ import annotations

import subprocess
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "TALK_CATALOG.md"

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


def main() -> None:
    by_folder: dict[str, list[Path]] = defaultdict(list)
    for path in tracked_files():
        if len(path.parts) < 2:
            continue
        if path.parts[0] == "scripts":
            continue
        if path.suffix.lower() not in SOURCE_SUFFIXES | OUTPUT_SUFFIXES | ASSET_SUFFIXES:
            continue
        by_folder[path.parts[0]].append(path)

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
        "## Talks",
        "",
        "| Talk | Date | Sources | Outputs | Assets | Published |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]

    for folder in sorted(by_folder):
        files = by_folder[folder]
        sources = [path for path in files if path.suffix.lower() in SOURCE_SUFFIXES]
        outputs = [path for path in files if path.suffix.lower() in OUTPUT_SUFFIXES]
        assets = [path for path in files if path.suffix.lower() in ASSET_SUFFIXES]
        published = PUBLISHED_URLS.get(folder, "")
        published_cell = f"[link]({published})" if published else ""
        lines.append(
            "| "
            + f"{markdown_link(Path(folder))} | {talk_date(sources)} | {len(sources)} | "
            + f"{len(outputs)} | {len(assets)} | {published_cell} |"
        )

    lines.append("")

    for folder in sorted(by_folder):
        files = by_folder[folder]
        sources = [path for path in files if path.suffix.lower() in SOURCE_SUFFIXES]
        outputs = [path for path in files if path.suffix.lower() in OUTPUT_SUFFIXES]
        assets = [path for path in files if path.suffix.lower() in ASSET_SUFFIXES]
        counts = Counter(path.suffix.lower()[1:] for path in files)

        lines.extend(
            [
                f"## {talk_title(folder, sources)}",
                "",
                f"- Folder: `{folder}`",
                "- File types: "
                + ", ".join(f"`{suffix}` ({count})" for suffix, count in sorted(counts.items())),
                "",
                "### Sources",
                "",
            ]
        )
        lines.extend(rows_for(sources) if sources else ["No source files indexed."])
        lines.extend(["", "### Rendered Outputs", ""])
        lines.extend(rows_for(outputs) if outputs else ["No rendered outputs indexed."])
        lines.extend(["", "### Assets", ""])
        lines.extend(rows_for(assets) if assets else ["No assets indexed."])
        lines.append("")

    TARGET.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
