from __future__ import annotations

import re
from pathlib import Path


def summarize_review_markdown(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    sections = []

    weaknesses = _collect_labeled_sections(text, "Summary Of Weaknesses")
    comments = _collect_labeled_sections(text, "Comments Suggestions And Typos")
    strengths = _collect_labeled_sections(text, "Summary Of Strengths")

    sections.append("# Review Summary")
    sections.append("")
    sections.append("This file is generated from the provided review markdown. It is not injected into the paper automatically.")
    sections.append("")

    if strengths:
        sections.append("## Strengths Mentioned By Reviewers")
        for item in strengths:
            sections.append(f"- {item}")
        sections.append("")

    if weaknesses:
        sections.append("## Weaknesses Mentioned By Reviewers")
        for item in weaknesses:
            sections.append(f"- {item}")
        sections.append("")

    if comments:
        sections.append("## Actionable Revision Suggestions")
        for item in comments:
            sections.append(f"- {item}")
        sections.append("")

    if not any((strengths, weaknesses, comments)):
        sections.append("No structured review sections were detected.")
        sections.append("")

    return "\n".join(sections).strip() + "\n"


def _collect_labeled_sections(text: str, label: str) -> list[str]:
    pattern = re.compile(
        rf"\*\*[^*]*{re.escape(label)}[^*]*\*\*(?P<body>.*?)(?=\n\*\*|\n# |\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    items: list[str] = []
    for match in pattern.finditer(text):
        body = match.group("body")
        for line in body.splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
            cleaned = cleaned.strip("* ").strip()
            if cleaned:
                items.append(cleaned)
    return items
