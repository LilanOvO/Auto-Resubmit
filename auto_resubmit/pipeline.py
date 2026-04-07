from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path

from auto_resubmit.latex import (
    ParsedLatexProject,
    build_source_representation,
    build_target_representation,
    merge_preambles,
    render_merged_tex,
)
from auto_resubmit.review import summarize_review_markdown


SOURCE_ASSET_SUFFIXES = {
    ".bib",
    ".bmp",
    ".csv",
    ".eps",
    ".jpeg",
    ".jpg",
    ".json",
    ".pdf",
    ".png",
    ".svg",
    ".tsv",
}


@dataclass
class RunResult:
    project_dir: Path
    main_tex: Path
    pdf_path: Path | None
    zip_path: Path
    manifest_path: Path
    warnings: list[str]
    compiler: str | None
    compile_log: Path | None


def run_conversion(
    source_zip: Path,
    target_template_zip: Path,
    output_dir: Path,
    review_md: Path | None = None,
    keep_workdir: bool = True,
) -> RunResult:
    if not source_zip.exists():
        raise FileNotFoundError(f"Source zip not found: {source_zip}")
    if not target_template_zip.exists():
        raise FileNotFoundError(f"Target template zip not found: {target_template_zip}")
    if review_md and not review_md.exists():
        raise FileNotFoundError(f"Review markdown not found: {review_md}")

    work_dir = output_dir / "work"
    source_dir = work_dir / "source"
    target_dir = work_dir / "target"
    source_extract_dir = source_dir / "extracted"
    target_extract_dir = target_dir / "extracted"
    final_project_dir = output_dir / "converted_project"

    output_dir.mkdir(parents=True, exist_ok=True)

    _reset_directory(work_dir)
    _reset_directory(final_project_dir)

    _extract_zip(source_zip, source_extract_dir)
    _extract_zip(target_template_zip, target_extract_dir)

    (
        source_main_tex,
        source_preamble,
        title_block,
        author_block,
        date_block,
        abstract,
        main_body,
        bibliography_style,
        bibliography_block,
        appendix_body,
        source_warnings,
    ) = build_source_representation(source_extract_dir)
    target_main_tex, documentclass, target_preamble, target_kind = build_target_representation(target_extract_dir)

    merged_preamble, pass_options = merge_preambles(
        target_preamble,
        source_preamble,
        target_kind=target_kind,
    )

    shutil.copytree(source_extract_dir, final_project_dir, dirs_exist_ok=True)
    _prune_latex_build_artifacts(final_project_dir)
    generated_dir = final_project_dir / source_main_tex.relative_to(source_extract_dir).parent
    generated_dir.mkdir(parents=True, exist_ok=True)

    target_template_dir = target_main_tex.parent
    for template_file in target_template_dir.rglob("*"):
        if not template_file.is_file():
            continue
        destination = generated_dir / template_file.relative_to(target_template_dir)
        if destination.exists() and destination.suffix.lower() in SOURCE_ASSET_SUFFIXES:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_file, destination)
    style_warnings = _stabilize_target_style_files(final_project_dir, target_kind)

    include_checklist = target_kind == "neurips" and (generated_dir / "checklist.tex").exists()
    generated_tex_name = "resubmitted.tex"
    generated_main_tex = generated_dir / generated_tex_name

    project = ParsedLatexProject(
        root_dir=final_project_dir,
        main_tex=generated_main_tex,
        target_kind=target_kind,
        documentclass=documentclass,
        title_block=title_block,
        author_block=author_block,
        date_block=date_block,
        target_preamble=merged_preamble,
        source_macro_preamble=source_preamble,
        pass_options=pass_options,
        abstract=abstract,
        main_body=main_body,
        bibliography_style=bibliography_style,
        bibliography_block=bibliography_block,
        appendix_body=appendix_body,
        warnings=list(source_warnings),
    )
    project.warnings.extend(style_warnings)

    rendered_tex = render_merged_tex(project, include_checklist=include_checklist)
    rendered_tex, fix_warnings = _apply_safe_tex_fixes(rendered_tex, target_kind=target_kind)
    project.warnings.extend(fix_warnings)
    generated_main_tex.write_text(rendered_tex, encoding="utf-8")
    compile_entry = _prepare_root_compile_entry(
        project_dir=final_project_dir,
        generated_dir=generated_dir,
        generated_main_tex=generated_main_tex,
    )

    audit_path = output_dir / "content_audit.json"
    audit = _build_content_audit(
        source_main_tex=source_main_tex,
        generated_main_tex=generated_main_tex,
        abstract=abstract,
        main_body=main_body,
        bibliography_style=bibliography_style,
        bibliography_block=bibliography_block,
        appendix_body=appendix_body,
        copied_asset_count=_count_copied_assets(final_project_dir),
    )
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    review_summary_path = None
    if review_md:
        review_summary_path = final_project_dir / "review_summary.md"
        review_summary_path.write_text(summarize_review_markdown(review_md), encoding="utf-8")

    pdf_path, compiler, compile_log = _compile_project(compile_entry)
    warnings = list(project.warnings)
    if pdf_path is None:
        warnings.append(
            "PDF compilation did not succeed. The generated LaTeX project and compile logs are still available."
        )

    manifest_path = output_dir / "conversion_manifest.json"
    manifest = {
        "source_zip": str(source_zip),
        "target_template_zip": str(target_template_zip),
        "source_main_tex": str(source_main_tex.relative_to(source_extract_dir)),
        "target_main_tex": str(target_main_tex.relative_to(target_extract_dir)),
        "target_kind": target_kind,
        "generated_main_tex": str(generated_main_tex.relative_to(final_project_dir)),
        "compile_entry": str(compile_entry.relative_to(final_project_dir)),
        "pdf_path": str(pdf_path.relative_to(output_dir)) if pdf_path else None,
        "content_audit": str(audit_path.relative_to(output_dir)),
        "review_summary": str(review_summary_path.relative_to(final_project_dir)) if review_summary_path else None,
        "compiler": compiler,
        "compile_log": str(compile_log.relative_to(output_dir)) if compile_log else None,
        "warnings": warnings,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    zip_path = output_dir / "converted_project.zip"
    _zip_directory(final_project_dir, zip_path)

    if not keep_workdir:
        shutil.rmtree(work_dir, ignore_errors=True)

    return RunResult(
        project_dir=final_project_dir,
        main_tex=generated_main_tex,
        pdf_path=pdf_path,
        zip_path=zip_path,
        manifest_path=manifest_path,
        warnings=warnings,
        compiler=compiler,
        compile_log=compile_log,
    )


def _extract_zip(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(destination)


def _reset_directory(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)


def _zip_directory(source_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file():
                archive.write(file_path, arcname=file_path.relative_to(source_dir))


def _compile_project(main_tex: Path) -> tuple[Path | None, str | None, Path | None]:
    compiler = shutil.which("tectonic")
    if compiler is None:
        return None, None, None

    log_path = main_tex.parent / "tectonic.log"
    command = [
        compiler,
        "--keep-intermediates",
        "--keep-logs",
        "--reruns",
        "2",
        "--outdir",
        str(main_tex.parent),
        str(main_tex.name),
    ]
    completed = subprocess.run(
        command,
        cwd=main_tex.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    log_path.write_text(
        completed.stdout + ("\n" if completed.stdout else "") + completed.stderr,
        encoding="utf-8",
    )
    pdf_path = main_tex.with_suffix(".pdf")
    if completed.returncode == 0 and pdf_path.exists():
        return pdf_path, Path(compiler).name, log_path
    return None, Path(compiler).name, log_path


def _prepare_root_compile_entry(
    project_dir: Path,
    generated_dir: Path,
    generated_main_tex: Path,
) -> Path:
    if generated_dir == project_dir:
        return generated_main_tex

    for path in generated_dir.rglob("*"):
        relative = path.relative_to(generated_dir)
        destination = project_dir / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    return project_dir / generated_main_tex.name


def _build_content_audit(
    source_main_tex: Path,
    generated_main_tex: Path,
    abstract: str,
    main_body: str,
    bibliography_style: str,
    bibliography_block: str,
    appendix_body: str,
    copied_asset_count: int,
) -> dict[str, object]:
    return {
        "source_main_tex": str(source_main_tex),
        "generated_main_tex": str(generated_main_tex),
        "segments": {
            "abstract": _segment_fingerprint(abstract),
            "main_body": _segment_fingerprint(main_body),
            "bibliography_style": _segment_fingerprint(bibliography_style),
            "bibliography_block": _segment_fingerprint(bibliography_block),
            "appendix_body": _segment_fingerprint(appendix_body),
        },
        "copied_asset_count": copied_asset_count,
    }


def _segment_fingerprint(text: str) -> dict[str, object]:
    raw = text.encode("utf-8")
    return {
        "chars": len(text),
        "lines": len(text.splitlines()),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _count_copied_assets(project_dir: Path) -> int:
    return sum(1 for path in project_dir.rglob("*") if path.is_file() and path.suffix != ".tex")


def _prune_latex_build_artifacts(project_dir: Path) -> None:
    removable_suffixes = {
        ".aux",
        ".bbl",
        ".bcf",
        ".blg",
        ".fdb_latexmk",
        ".fls",
        ".log",
        ".nav",
        ".out",
        ".run.xml",
        ".snm",
        ".toc",
        ".vrb",
        ".xdv",
    }
    removable_names = {"tectonic.log"}
    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name in removable_names or path.suffix in removable_suffixes:
            path.unlink()


def _stabilize_target_style_files(project_dir: Path, target_kind: str) -> list[str]:
    warnings: list[str] = []
    return warnings


def _apply_safe_tex_fixes(text: str, target_kind: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    fixed_text, count = re.subn(r"(?<!\\)\\(?=\d+\.\d)", "", text)
    if count:
        warnings.append(
            f"Applied {count} compile-safe fix(es) for invalid backslashes directly before decimal numbers."
        )
    fixed_text, svg_count = re.subn(
        r"\\includesvg(?:\s*\[[^\]]*\])?\s*\{[^}]+\}",
        "",
        fixed_text,
    )
    if svg_count:
        warnings.append(
            f"Removed {svg_count} inline SVG include(s) because the current build environment does not provide an SVG conversion backend."
        )
    fixed_text, color_macro_count = re.subn(
        r"\\newcommand\\(red)(?=\s*\[)",
        r"\\providecommand\\\1",
        fixed_text,
    )
    if color_macro_count:
        warnings.append(
            f"Downgraded {color_macro_count} potentially conflicting color macro definition(s) to \\providecommand for template compatibility."
        )
    if target_kind == "aaai":
        fixed_text, pagebreak_count = re.subn(r"^\s*\\(?:clearpage|newpage|pagebreak)\s*$", "", fixed_text, flags=re.MULTILINE)
        if pagebreak_count:
            warnings.append(
                f"Removed {pagebreak_count} page-break command(s) that violate AAAI formatting constraints."
            )
    return fixed_text, warnings
