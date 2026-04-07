from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


DOCUMENT_RE = re.compile(
    r"(?P<prefix>.*?)(?P<begin>\\begin\{document\})(?P<document>.*?)(?P<end>\\end\{document\})",
    re.DOTALL,
)

TEMPLATE_CONFIGS: dict[str, dict[str, object]] = {
    "acl": {
        "preferred_main_names": ("acl_latex.tex", "acl_lualatex.tex"),
        "default_bibliographystyle": r"\bibliographystyle{acl_natbib}",
        "skip_packages": {"acl", "times"},
        "source_strip_packages": {"acl", "times"},
        "source_strip_commands": (),
        "strip_macros": ("title", "author", "date"),
    },
    "neurips": {
        "preferred_main_names": ("neurips_2026.tex",),
        "default_bibliographystyle": r"\bibliographystyle{plainnat}",
        "skip_packages": {"neurips_2026", "times"},
        "source_strip_packages": {"neurips_2026", "times"},
        "source_strip_commands": (),
        "strip_macros": ("title", "author", "date", "pdfinfo"),
    },
    "icml": {
        "preferred_main_names": ("example_paper.tex",),
        "default_bibliographystyle": r"\bibliographystyle{icml2026}",
        "skip_packages": {"icml2026", "times", "algorithm", "algorithmicx", "algpseudocode"},
        "source_strip_packages": {"icml2026", "times"},
        "source_strip_commands": (),
        "strip_macros": ("title", "author", "date", "icmltitlerunning"),
    },
    "iclr": {
        "preferred_main_names": ("iclr2026_conference.tex",),
        "default_bibliographystyle": r"\bibliographystyle{iclr2026_conference}",
        "skip_packages": {"iclr2026_conference", "times"},
        "source_strip_packages": {"iclr2026_conference", "times"},
        "source_strip_commands": (),
        "strip_macros": ("title", "author", "date"),
    },
    "cvpr": {
        "preferred_main_names": ("main.tex",),
        "default_bibliographystyle": r"\bibliographystyle{ieeenat_fullname}",
        "skip_packages": {"cvpr"},
        "source_strip_packages": {"cvpr"},
        "source_strip_commands": (),
        "strip_macros": ("title", "author", "date"),
    },
    "aaai": {
        "preferred_main_names": (
            "anonymous-submission-latex-2026.tex",
            "Formatting-Instructions-LaTeX-2026.tex",
        ),
        "default_bibliographystyle": "",
        "skip_packages": {
            "aaai2026",
            "times",
            "helvet",
            "courier",
            "url",
            "graphicx",
            "natbib",
            "caption",
            "algorithm",
            "algorithmicx",
            "algpseudocode",
            "hyperref",
            "fontenc",
        },
        "source_strip_packages": {
            "aaai2026",
            "times",
            "helvet",
            "courier",
            "url",
            "natbib",
            "caption",
        },
        "source_strip_commands": ("nocopyright",),
        "strip_macros": ("title", "author", "date", "affiliations", "pdfinfo"),
    },
    "generic": {
        "preferred_main_names": (),
        "default_bibliographystyle": r"\bibliographystyle{plainnat}",
        "skip_packages": {"times"},
        "source_strip_packages": set(),
        "source_strip_commands": (),
        "strip_macros": ("title", "author", "date"),
    },
}


@dataclass
class PackageSpec:
    name: str
    options: tuple[str, ...]
    raw: str


@dataclass
class ParsedLatexProject:
    root_dir: Path
    main_tex: Path
    target_kind: str
    documentclass: str
    title_block: str
    author_block: str
    date_block: str
    target_preamble: str
    source_macro_preamble: str
    pass_options: dict[str, set[str]]
    abstract: str
    main_body: str
    bibliography_style: str
    bibliography_block: str
    appendix_body: str
    warnings: list[str] = field(default_factory=list)


def discover_main_tex(root_dir: Path, preferred_names: tuple[str, ...] = ()) -> Path:
    for preferred_name in preferred_names:
        matches = sorted(path for path in root_dir.rglob(preferred_name) if path.is_file())
        if matches:
            return matches[0]

    tex_files = sorted(root_dir.rglob("*.tex"))
    if not tex_files:
        raise FileNotFoundError(f"No .tex files found under {root_dir}")

    best_file = None
    best_score = None
    for candidate in tex_files:
        text = candidate.read_text(encoding="utf-8", errors="ignore")
        if "\\documentclass" not in text or "\\begin{document}" not in text:
            continue
        score = 0
        score += 50 if "\\title" in text else 0
        score += 30 if "\\begin{abstract}" in text else 0
        score += 20 if "\\bibliography" in text or "\\printbibliography" in text else 0
        score += min(len(text) // 500, 100)
        if best_score is None or score > best_score:
            best_score = score
            best_file = candidate

    if best_file is None:
        raise FileNotFoundError(f"Unable to identify main LaTeX file under {root_dir}")
    return best_file


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def mask_comments(text: str) -> str:
    lines = []
    for raw_line in text.splitlines(keepends=True):
        line = list(raw_line)
        escaped = False
        for index, char in enumerate(line):
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == "%":
                for fill_index in range(index, len(line)):
                    if line[fill_index] not in {"\n", "\r"}:
                        line[fill_index] = " "
                break
        lines.append("".join(line))
    return "".join(lines)


def extract_documentclass(text: str) -> str:
    match = re.search(r"^\s*\\documentclass(?:\[[^\]]*\])?\{[^}]+\}", text, re.MULTILINE)
    if not match:
        raise ValueError("Missing \\documentclass in target template")
    return match.group(0).strip()


def detect_project_kind_from_text(text: str, root_dir: Path | None = None) -> str:
    masked = mask_comments(text)
    package_markers = (
        ("acl", r"\\usepackage(?:\[[^\]]*\])?\{acl\}"),
        ("neurips", r"\\usepackage(?:\[[^\]]*\])?\{neurips_2026\}"),
        ("icml", r"\\usepackage(?:\[[^\]]*\])?\{icml2026\}"),
        ("iclr", r"\\usepackage(?:\[[^\]]*\])?\{iclr2026_conference\}"),
        ("cvpr", r"\\usepackage(?:\[[^\]]*\])?\{cvpr\}"),
        ("aaai", r"\\usepackage(?:\[[^\]]*\])?\{aaai2026\}"),
    )
    for kind, pattern in package_markers:
        if re.search(pattern, masked):
            return kind
    return detect_target_kind(root_dir) if root_dir is not None else "generic"


def strip_documentclass(preamble: str) -> str:
    return re.sub(
        r"^\s*\\documentclass(?:\[[^\]]*\])?\{[^}]+\}\s*",
        "",
        preamble,
        count=1,
        flags=re.MULTILINE,
    ).strip()


def strip_title_author_blocks(preamble: str) -> str:
    cleaned = strip_documentclass(preamble)
    for macro in TEMPLATE_CONFIGS["generic"]["strip_macros"]:
        while True:
            block = extract_macro_block(cleaned, macro)
            if not block:
                break
            cleaned = cleaned.replace(block, "", 1)
    return cleaned.strip()


def strip_template_macros(preamble: str, target_kind: str) -> str:
    cleaned = strip_documentclass(preamble)
    macro_names = TEMPLATE_CONFIGS.get(target_kind, TEMPLATE_CONFIGS["generic"])["strip_macros"]
    for macro in macro_names:
        while True:
            block = extract_macro_block(cleaned, macro)
            if not block:
                break
            cleaned = cleaned.replace(block, "", 1)
    return cleaned.strip()


def split_document(text: str) -> tuple[str, str]:
    match = DOCUMENT_RE.search(text)
    if not match:
        raise ValueError("Invalid LaTeX file: missing document environment")
    return match.group("prefix"), match.group("document")


def extract_macro_block(text: str, macro_name: str) -> str | None:
    masked = mask_comments(text)
    pattern = re.compile(rf"\\{re.escape(macro_name)}(?:\s*\[[^\]]*\])?\s*\{{", re.MULTILINE)
    match = pattern.search(masked)
    if not match:
        return None

    open_brace = masked.find("{", match.start())
    if open_brace == -1:
        return None
    end_index = find_matching_brace(masked, open_brace)
    return text[match.start() : end_index + 1]


def extract_environment(text: str, env_name: str) -> tuple[str, str] | None:
    masked = mask_comments(text)
    begin = re.search(rf"\\begin\{{{re.escape(env_name)}\}}", masked)
    if not begin:
        return None
    end = re.search(rf"\\end\{{{re.escape(env_name)}\}}", masked[begin.end() :])
    if not end:
        return None
    block_end = begin.end() + end.end()
    block = text[begin.start() : block_end]
    inner = text[begin.end() : begin.end() + end.start()]
    return block, inner.strip()


def find_matching_brace(text: str, open_brace: int) -> int:
    depth = 0
    escaped = False
    for index in range(open_brace, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("Unbalanced braces in LaTeX content")


def find_matching_bracket(text: str, open_bracket: int) -> int:
    depth = 0
    escaped = False
    for index in range(open_bracket, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("Unbalanced brackets in LaTeX content")


def parse_usepackage_lines(preamble: str) -> tuple[list[PackageSpec], str]:
    packages: list[PackageSpec] = []
    remaining_lines: list[str] = []
    package_re = re.compile(r"^\s*\\usepackage(?:\[(?P<options>[^\]]*)\])?\{(?P<names>[^}]*)\}", re.MULTILINE)

    for line in preamble.splitlines():
        match = package_re.match(line)
        if not match:
            remaining_lines.append(line)
            continue

        options = tuple(
            part.strip()
            for part in (match.group("options") or "").split(",")
            if part.strip()
        )
        names = [name.strip() for name in match.group("names").split(",") if name.strip()]
        for name in names:
            packages.append(PackageSpec(name=name, options=options, raw=line.rstrip()))

    return packages, "\n".join(remaining_lines).strip()


def merge_preambles(
    target_preamble: str,
    source_preamble: str,
    target_kind: str = "generic",
) -> tuple[str, dict[str, set[str]]]:
    cleaned_source = strip_title_author_blocks(source_preamble)
    source_packages, source_other = parse_usepackage_lines(cleaned_source)
    target_packages, _ = parse_usepackage_lines(strip_template_macros(target_preamble, target_kind))
    skip_packages = {
        "acl",
        "neurips_2026",
        "icml2026",
        "iclr2026_conference",
        "cvpr",
        "aaai2026",
    }
    skip_packages.update(set(TEMPLATE_CONFIGS.get(target_kind, TEMPLATE_CONFIGS["generic"])["skip_packages"]))

    target_package_options = {
        package.name: set(package.options)
        for package in target_packages
    }
    pass_options: dict[str, set[str]] = {}
    added_packages: list[str] = []
    added_seen: set[str] = set()

    for package in source_packages:
        if package.name in skip_packages:
            continue
        if package.name in target_package_options:
            missing = set(package.options) - target_package_options[package.name]
            if missing:
                pass_options.setdefault(package.name, set()).update(missing)
            continue
        if package.name in added_seen:
            continue
        options_prefix = f"[{','.join(package.options)}]" if package.options else ""
        added_packages.append(f"\\usepackage{options_prefix}" + f"{{{package.name}}}")
        added_seen.add(package.name)

    additions: list[str] = []
    if added_packages:
        additions.append("% Added from the source project to preserve paper content")
        additions.extend(added_packages)
    if source_other.strip():
        additions.append("% Source project macros and local configuration")
        additions.append(source_other.strip())

    merged = target_preamble.strip()
    if additions:
        merged = f"{merged}\n\n" + "\n".join(additions).strip()
    return merged.strip(), pass_options


def split_appendix(document_body: str) -> tuple[str, str]:
    marker = re.search(r"(^|\n)\s*\\appendix\b", mask_comments(document_body))
    if not marker:
        return document_body.strip(), ""
    start = marker.start()
    return document_body[:start].strip(), document_body[start:].strip()


def split_bibliography(document_body: str) -> tuple[str, str]:
    masked = mask_comments(document_body)
    bibliography_patterns = [
        r"\\bibliographystyle(?:\s*\[[^\]]*\])?\s*\{",
        r"\\bibliography(?:\s*\[[^\]]*\])?\s*\{",
        r"\\printbibliography\b",
        r"\\begin\{thebibliography\}",
    ]
    locations: list[int] = []
    for pattern in bibliography_patterns:
        match = re.search(pattern, masked)
        if match:
            locations.append(match.start())
    if not locations:
        return document_body.strip(), ""
    start = min(locations)
    prefix = document_body[:start]
    bibliography_body = document_body[start:].strip()
    group_match = re.search(r"\{\s*\\small\s*$", prefix, re.DOTALL)
    if group_match:
        prefix = prefix[: group_match.start()]
        bibliography_body = bibliography_body.removesuffix("}").strip()
    return prefix.rstrip(), bibliography_body


def extract_bibliography_style(text: str) -> tuple[str, str]:
    block = extract_macro_block(text, "bibliographystyle")
    if not block:
        return text.strip(), ""
    return text.replace(block, "", 1).strip(), block.strip()


def strip_frontmatter(document_body: str, source_kind: str, main_tex: Path) -> tuple[str, str]:
    body = document_body
    abstract_text = ""

    if source_kind == "icml":
        body = strip_icml_frontmatter(body)
    if source_kind == "neurips":
        body = strip_neurips_artifacts(body)

    abstract_env = extract_environment(body, "abstract")
    if abstract_env:
        block, abstract_text = abstract_env
        body = body.replace(block, "", 1)
    elif source_kind == "cvpr":
        abstract_text, body = extract_cvpr_abstract_from_inputs(body, main_tex)

    body = re.sub(r"^\s*\\maketitle\s*", "", body, count=1)
    body = body.strip()
    return abstract_text.strip(), body


def strip_icml_frontmatter(body: str) -> str:
    masked = mask_comments(body)
    start = masked.find(r"\twocolumn[")
    if start != -1:
        open_bracket = masked.find("[", start)
        if open_bracket != -1:
            close_bracket = find_matching_bracket(masked, open_bracket)
            body = body[:start] + body[close_bracket + 1 :]
    body = re.sub(
        r"^\s*\\printAffiliationsAndNotice\s*\{.*?\}\s*",
        "",
        body,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    return body


def strip_neurips_artifacts(body: str) -> str:
    body = re.sub(
        r"^\s*\\newpage\s*\n\s*\\input\{checklist\.tex\}\s*$",
        "",
        body,
        flags=re.MULTILINE,
    )
    body = re.sub(r"^\s*\\input\{checklist\.tex\}\s*$", "", body, flags=re.MULTILINE)
    return body


def extract_cvpr_abstract_from_inputs(body: str, main_tex: Path) -> tuple[str, str]:
    masked = mask_comments(body)
    patterns = [
        re.compile(r"^\s*\\input\{(?P<path>[^}]*abstract[^}]*)\}\s*$", re.MULTILINE),
        re.compile(r"^\s*\\input\{(?P<path>sec/0_abstract)\}\s*$", re.MULTILINE),
    ]
    for pattern in patterns:
        match = pattern.search(masked)
        if not match:
            continue
        input_path = resolve_tex_input_path(main_tex.parent, match.group("path"))
        abstract_text = load_text(input_path).strip() if input_path else ""
        body = body[: match.start()] + body[match.end() :]
        return abstract_text, body
    return "", body


def resolve_tex_input_path(base_dir: Path, relative_path: str) -> Path | None:
    candidates = [base_dir / relative_path]
    if not relative_path.endswith(".tex"):
        candidates.append(base_dir / f"{relative_path}.tex")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def build_source_representation(root_dir: Path) -> tuple[Path, str, str, str, str, str, str, str, list[str]]:
    main_tex = discover_main_tex(root_dir, preferred_names=("resubmitted.tex", "main.tex"))
    text = load_text(main_tex)
    preamble, document_body = split_document(text)
    source_kind = detect_project_kind_from_text(preamble, root_dir=root_dir)
    source_preamble = extract_preserved_source_preamble(preamble)
    source_preamble = strip_algorithm_compatibility_lines(strip_template_macros(source_preamble, source_kind))
    source_preamble = strip_source_template_packages(source_preamble, source_kind)
    source_preamble = strip_source_template_commands(source_preamble, source_kind)
    source_preamble = strip_autoresubmit_injected_blocks(source_preamble)
    source_preamble, layout_warnings = strip_layout_modifying_commands(source_preamble)

    warnings: list[str] = []
    warnings.extend(layout_warnings)
    title_block = extract_macro_block(preamble, "title") or "\\title{Untitled Submission}"
    author_block = extract_macro_block(preamble, "author") or "\\author{}"
    date_block = extract_macro_block(preamble, "date") or "\\date{}"
    if "\\author{}" == author_block:
        warnings.append("Source paper does not define \\author; generated output keeps authors blank.")

    abstract, body_without_frontmatter = strip_frontmatter(document_body, source_kind, main_tex)
    if not abstract:
        warnings.append("Source paper does not contain an abstract environment.")

    main_plus_bib, appendix = split_appendix(body_without_frontmatter)
    main_body, bibliography_block = split_bibliography(main_plus_bib)
    bibliography_block, bibliography_style = extract_bibliography_style(bibliography_block)
    source_preamble = add_inferred_source_packages(
        source_preamble,
        "\n".join(part for part in (abstract, main_body, appendix) if part.strip()),
    )

    return (
        main_tex,
        source_preamble.strip(),
        title_block.strip(),
        author_block.strip(),
        date_block.strip(),
        abstract.strip(),
        main_body.strip(),
        bibliography_style.strip(),
        bibliography_block.strip(),
        appendix.strip(),
        warnings,
    )


def build_target_representation(root_dir: Path) -> tuple[Path, str, str, str]:
    target_kind = detect_target_kind(root_dir)
    preferred_names = tuple(TEMPLATE_CONFIGS.get(target_kind, TEMPLATE_CONFIGS["generic"])["preferred_main_names"])
    main_tex = discover_main_tex(root_dir, preferred_names=preferred_names)
    text = load_text(main_tex)
    preamble, _ = split_document(text)
    documentclass = extract_documentclass(text)
    normalized_preamble = normalize_target_submission_mode(strip_template_macros(preamble, target_kind), target_kind)
    return main_tex, documentclass, normalized_preamble, target_kind


def render_merged_tex(project: ParsedLatexProject, include_checklist: bool) -> str:
    if project.target_kind == "icml":
        return render_icml_merged_tex(project)
    if project.target_kind == "aaai":
        return render_aaai_merged_tex(project)

    pass_option_lines = []
    for package_name in sorted(project.pass_options):
        options = ",".join(sorted(project.pass_options[package_name]))
        pass_option_lines.append(f"\\PassOptionsToPackage{{{options}}}{{{package_name}}}")

    parts = [project.documentclass]
    if pass_option_lines:
        parts.append("\n".join(pass_option_lines))
    parts.append(project.target_preamble.strip())
    submission_safeguards = render_submission_safeguards(project)
    if submission_safeguards:
        parts.append(submission_safeguards)
    parts.append(project.title_block.strip())
    parts.append(project.author_block.strip())
    if project.date_block.strip():
        parts.append(project.date_block.strip())
    parts.append("\\begin{document}")
    parts.append("\\maketitle")
    post_maketitle_hook = render_post_maketitle_submission_safeguards(project)
    if post_maketitle_hook:
        parts.append(post_maketitle_hook)
    if project.abstract:
        parts.append("\\begin{abstract}\n" + project.abstract.strip() + "\n\\end{abstract}")
    if project.main_body:
        parts.append(project.main_body.strip())

    bibliography_style = project.bibliography_style.strip()
    bibliography_block = project.bibliography_block.strip()
    if bibliography_block:
        if not bibliography_style:
            bibliography_style = default_bibliographystyle(project.target_kind)
        if bibliography_style:
            parts.append(bibliography_style)
        parts.append(bibliography_block)

    if project.appendix_body.strip():
        parts.append(project.appendix_body.strip())

    if include_checklist:
        parts.append("\\newpage")
        parts.append("\\input{checklist.tex}")

    parts.append("\\end{document}")
    return "\n\n".join(part for part in parts if part and part.strip()) + "\n"


def render_aaai_merged_tex(project: ParsedLatexProject) -> str:
    pass_option_lines = []
    for package_name in sorted(project.pass_options):
        options = ",".join(sorted(project.pass_options[package_name]))
        pass_option_lines.append(f"\\PassOptionsToPackage{{{options}}}{{{package_name}}}")

    title_content = extract_macro_content(project.title_block) or "Untitled Submission"
    author_content = "Anonymous Submission"
    compatibility_macros = r"""
\usepackage{iftex}
\ifPDFTeX\else
% AAAI's PSNFSS times/helvet/courier stack falls back to Latin Modern under
% TU/XeTeX. Re-select the T1 text encoding so tectonic/XeTeX uses the intended
% Times-compatible Type1 fonts without requiring extra packages.
\renewcommand{\encodingdefault}{T1}
\AtBeginDocument{\normalfont\selectfont}
\fi
\providecommand{\texorpdfstring}[2]{#1}
\providecommand{\State}{\STATE}
\providecommand{\Statex}{\item[]}
\providecommand{\Require}{\REQUIRE}
\providecommand{\Ensure}{\ENSURE}
\providecommand{\Return}{\textbf{return}}
\providecommand{\Comment}[1]{\COMMENT{#1}}
""".strip()

    parts = [project.documentclass]
    if pass_option_lines:
        parts.append("\n".join(pass_option_lines))
    parts.append(project.target_preamble.strip())
    parts.append(compatibility_macros)
    parts.append(f"\\title{{{title_content}}}")
    parts.append(f"\\author{{{author_content}}}")
    parts.append("\\affiliations{}")
    parts.append("\\begin{document}")
    parts.append("\\maketitle")
    if project.abstract:
        parts.append("\\begin{abstract}\n" + project.abstract.strip() + "\n\\end{abstract}")
    if project.main_body:
        parts.append(project.main_body.strip())

    bibliography_block = project.bibliography_block.strip()
    if bibliography_block:
        parts.append(bibliography_block)

    if project.appendix_body.strip():
        parts.append(project.appendix_body.strip())

    parts.append("\\end{document}")
    return "\n\n".join(part for part in parts if part and part.strip()) + "\n"


def render_icml_merged_tex(project: ParsedLatexProject) -> str:
    pass_option_lines = []
    for package_name in sorted(project.pass_options):
        options = ",".join(sorted(project.pass_options[package_name]))
        pass_option_lines.append(f"\\PassOptionsToPackage{{{options}}}{{{package_name}}}")

    title_content = extract_macro_content(project.title_block) or "Untitled Submission"
    running_title = collapse_title_for_running_head(title_content)

    compatibility_macros = r"""
% Compatibility layer for source projects that use algpseudocode-style commands.
\providecommand{\State}{\STATE}
\providecommand{\Statex}{\item[]}
\providecommand{\Require}{\REQUIRE}
\providecommand{\Ensure}{\ENSURE}
\providecommand{\Return}{\textbf{return}}
""".strip()

    parts = [project.documentclass]
    if pass_option_lines:
        parts.append("\n".join(pass_option_lines))
    parts.append(project.target_preamble.strip())
    parts.append(f"\\icmltitlerunning{{{running_title}}}")
    parts.append(compatibility_macros)
    parts.append("\\begin{document}")
    parts.append(
        "\n".join(
            [
                "\\twocolumn[",
                f"  \\icmltitle{{{title_content}}}",
                "  \\vskip 0.3in",
                "]",
                "\\printAffiliationsAndNotice{}",
            ]
        )
    )
    if project.abstract:
        parts.append("\\begin{abstract}\n" + project.abstract.strip() + "\n\\end{abstract}")
    if project.main_body:
        parts.append(project.main_body.strip())

    bibliography_style = project.bibliography_style.strip() or default_bibliographystyle(project.target_kind)
    bibliography_block = project.bibliography_block.strip()
    if bibliography_block:
        parts.append(bibliography_style)
        parts.append(bibliography_block)

    if project.appendix_body.strip():
        parts.append(project.appendix_body.strip())

    parts.append("\\end{document}")
    return "\n\n".join(part for part in parts if part and part.strip()) + "\n"


def render_submission_safeguards(project: ParsedLatexProject) -> str:
    if project.target_kind == "acl":
        if not re.search(
            r"\\usepackage\[[^\]]*\breview\b[^\]]*\]\{acl\}",
            project.target_preamble,
        ):
            return ""
        return r"""
% Keep anonymous review mode, but disable visible line numbers in the generated
% submission package.
\AtBeginDocument{\nolinenumbers}
""".strip()

    if project.target_kind != "cvpr":
        return ""

    if not re.search(
        r"\\usepackage\[[^\]]*\breview\b[^\]]*\]\{cvpr\}",
        project.target_preamble,
    ):
        return ""

    return r"""
% Keep anonymous review mode, but disable visible line numbers in the generated
% submission package.
\AtBeginDocument{\nolinenumbers}
""".strip()


def render_post_maketitle_submission_safeguards(project: ParsedLatexProject) -> str:
    return ""


LAYOUT_LENGTH_NAMES = (
    "pdfpagewidth",
    "pdfpageheight",
    "paperwidth",
    "paperheight",
    "textwidth",
    "textheight",
    "columnsep",
    "oddsidemargin",
    "evensidemargin",
    "topmargin",
    "headheight",
    "headsep",
    "footskip",
    "parindent",
    "parskip",
    "floatsep",
    "textfloatsep",
    "intextsep",
)


def strip_layout_modifying_commands(source_preamble: str) -> tuple[str, list[str]]:
    cleaned = source_preamble
    removed = 0
    length_pattern = "|".join(LAYOUT_LENGTH_NAMES)
    patterns = (
        rf"^\s*\\(?:setlength|addtolength)\s*\{{\\(?:{length_pattern})\}}\s*\{{[^}}]*\}}\s*$",
        rf"^\s*\\(?:setlength|addtolength)\s*\\(?:{length_pattern})\s*\{{[^}}]*\}}\s*$",
        r"^\s*\\(?:geometry|newgeometry)\s*\{[^}]*\}\s*$",
        r"^\s*\\restoregeometry\s*$",
        r"^\s*\\(?:pagestyle|thispagestyle|pagenumbering)\s*\{[^}]*\}\s*$",
    )
    for pattern in patterns:
        cleaned, count = re.subn(pattern, "", cleaned, flags=re.MULTILINE)
        removed += count
    warnings: list[str] = []
    if removed:
        warnings.append(
            f"Removed {removed} source preamble command(s) that alter page layout or pagination so the output stays within the target template."
        )
    return cleaned.strip(), warnings


def strip_autoresubmit_injected_blocks(source_preamble: str) -> str:
    cleaned = re.sub(
        r"% Keep review-mode line numbers readable around wide floats in direct submission PDFs\..*?\\makeatother\s*",
        "",
        source_preamble,
        flags=re.DOTALL,
    )
    cleaned = re.sub(
        r"\\makeatletter\s*% lineno's built-in switching is page-based, so in two-column ACL review mode it leaves.*?\\makeatother\s*",
        "",
        cleaned,
        flags=re.DOTALL,
    )
    return cleaned.strip()


def normalize_target_submission_mode(target_preamble: str, target_kind: str) -> str:
    normalized = target_preamble
    if target_kind == "acl":
        return normalize_usepackage_options(normalized, "acl", add={"review"}, remove={"final", "preprint"})
    if target_kind == "cvpr":
        return normalize_usepackage_options(normalized, "cvpr", add={"review"}, remove={"pagenumbers"})
    if target_kind == "neurips":
        return normalize_usepackage_options(
            normalized,
            "neurips_2026",
            add=set(),
            remove={"final", "preprint", "nonanonymous"},
        )
    if target_kind == "icml":
        return normalize_usepackage_options(normalized, "icml2026", add=set(), remove={"accepted", "preprint"})
    if target_kind == "iclr":
        return re.sub(r"^\s*\\iclrfinalcopy\s*$", "", normalized, flags=re.MULTILINE).strip()
    if target_kind == "aaai":
        return normalize_usepackage_options(normalized, "aaai2026", add={"submission"}, remove=set())
    return normalized.strip()


def normalize_usepackage_options(
    preamble: str,
    package_name: str,
    add: set[str],
    remove: set[str],
) -> str:
    pattern = re.compile(
        rf"^(?P<indent>\s*)\\usepackage(?:\[(?P<options>[^\]]*)\])?\{{{re.escape(package_name)}\}}(?P<suffix>\s*(?:%.*)?)$",
        re.MULTILINE,
    )

    def replacer(match: re.Match[str]) -> str:
        existing = [
            option.strip()
            for option in (match.group("options") or "").split(",")
            if option.strip()
        ]
        filtered = [option for option in existing if option not in remove]
        for option in sorted(add):
            if option not in filtered:
                filtered.append(option)
        option_block = f"[{','.join(filtered)}]" if filtered else ""
        suffix = match.group("suffix") or ""
        return f"{match.group('indent')}\\usepackage{option_block}{{{package_name}}}{suffix}"

    normalized, count = pattern.subn(replacer, preamble, count=1)
    return normalized.strip() if count else preamble.strip()


def detect_target_kind(root_dir: Path) -> str:
    filenames = {path.name.lower() for path in root_dir.rglob("*") if path.is_file()}
    if "aaai2026.sty" in filenames:
        return "aaai"
    if "cvpr.sty" in filenames:
        return "cvpr"
    if "iclr2026_conference.sty" in filenames:
        return "iclr"
    if "icml2026.sty" in filenames:
        return "icml"
    if "neurips_2026.sty" in filenames:
        return "neurips"
    if "acl.sty" in filenames:
        return "acl"
    return "generic"


def default_bibliographystyle(target_kind: str) -> str:
    return str(TEMPLATE_CONFIGS.get(target_kind, TEMPLATE_CONFIGS["generic"])["default_bibliographystyle"])


def extract_macro_content(block: str) -> str:
    if not block:
        return ""
    open_brace = block.find("{")
    if open_brace == -1:
        return ""
    close_brace = find_matching_brace(block, open_brace)
    return block[open_brace + 1 : close_brace].strip()


def collapse_title_for_running_head(title: str) -> str:
    collapsed = re.sub(r"(?<!\\)%.*", "", title)
    collapsed = re.sub(r"\\includesvg(?:\s*\[[^\]]*\])?\s*\{[^}]+\}", "", collapsed)
    collapsed = re.sub(r"\\hspace\*?\s*\{[^}]+\}", " ", collapsed)
    collapsed = collapsed.replace("\\\\", " ")
    collapsed = re.sub(r"\s+", " ", collapsed)
    return collapsed.strip()


def add_inferred_source_packages(source_preamble: str, body_text: str) -> str:
    existing_packages, _ = parse_usepackage_lines(source_preamble)
    existing_package_names = {package.name for package in existing_packages}
    inferred_packages: list[str] = []
    inferred_macros: list[str] = []
    combined_text = f"{source_preamble}\n{body_text}"

    inference_rules = (
        ((r"\begin{algorithm}", r"\begin{algorithm*}"), "algorithm"),
        (
            (
                r"\begin{algorithmic}",
                r"\State",
                r"\Statex",
                r"\Require",
                r"\Ensure",
                r"\Return",
                r"\Comment",
            ),
            "algorithmic",
        ),
        ((r"\resizebox", r"\scalebox", r"\rotatebox", r"\includegraphics"), "graphicx"),
        ((r"\multirow",), "multirow"),
        ((r"\toprule", r"\midrule", r"\bottomrule", r"\cmidrule"), "booktabs"),
        ((r"\rowcolor", r"\cellcolor", r"\columncolor"), "colortbl"),
        ((r"\text{", r"\eqref{", r"\dfrac", r"\overset", r"\underset"), "amsmath"),
        ((r"\triangleq", r"\mathbb", r"\mathfrak", r"\leqslant", r"\geqslant"), "amssymb"),
        ((r"\mathscr",), "mathrsfs"),
        ((r"\DeclareCaptionStyle", r"\captionsetup", r"\captionof"), "caption"),
    )

    for tokens, package_name in inference_rules:
        if package_name in existing_package_names:
            continue
        if package_name == "algorithmic" and (
            "algorithmic" in existing_package_names
            or "algorithmicx" in existing_package_names
            or "algpseudocode" in existing_package_names
        ):
            continue
        if any(token in combined_text for token in tokens):
            inferred_packages.append(rf"\usepackage{{{package_name}}}")
            existing_package_names.add(package_name)

    if r"\begin{links}" in combined_text or r"\link{" in combined_text:
        inferred_macros.extend(
            [
                r"\providecommand{\link}[2]{\item \textbf{#1}: \url{#2}}",
                r"\newenvironment{links}{\begin{itemize}}{\end{itemize}}",
            ]
        )

    if not inferred_packages and not inferred_macros:
        return source_preamble

    additions = []
    if inferred_packages:
        additions.extend(inferred_packages)
    if inferred_macros:
        additions.extend(inferred_macros)
    return source_preamble.strip() + "\n\n% Inferred from source body during conversion\n" + "\n".join(additions)


def strip_algorithm_compatibility_lines(source_preamble: str) -> str:
    return re.sub(
        r"^\s*\\newcommand\{\\theHalgorithm\}.*$",
        "",
        source_preamble,
        flags=re.MULTILINE,
    ).strip()


def extract_preserved_source_preamble(preamble: str) -> str:
    markers = (
        "% Added from the source project to preserve paper content",
        "% Source project macros and local configuration",
    )
    starts = [preamble.find(marker) for marker in markers if marker in preamble]
    if not starts:
        return preamble
    return preamble[min(starts):].strip()


def strip_source_template_packages(source_preamble: str, source_kind: str) -> str:
    strip_packages = set(TEMPLATE_CONFIGS.get(source_kind, TEMPLATE_CONFIGS["generic"])["source_strip_packages"])
    if not strip_packages:
        return source_preamble

    packages, remaining = parse_usepackage_lines(source_preamble)
    kept_lines: list[str] = []
    for package in packages:
        if package.name in strip_packages:
            continue
        options_prefix = f"[{','.join(package.options)}]" if package.options else ""
        kept_lines.append(f"\\usepackage{options_prefix}" + f"{{{package.name}}}")

    parts = []
    if kept_lines:
        parts.append("\n".join(kept_lines))
    if remaining.strip():
        parts.append(remaining.strip())
    return "\n\n".join(parts).strip()


def strip_source_template_commands(source_preamble: str, source_kind: str) -> str:
    commands = tuple(TEMPLATE_CONFIGS.get(source_kind, TEMPLATE_CONFIGS["generic"])["source_strip_commands"])
    cleaned = source_preamble
    for command in commands:
        cleaned = re.sub(rf"^\s*\\{re.escape(command)}\s*$", "", cleaned, flags=re.MULTILINE)
    return cleaned.strip()
