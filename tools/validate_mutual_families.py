from __future__ import annotations

import argparse
import json
from pathlib import Path

from auto_resubmit.conferences import TESTDATA_TEMPLATE_BY_FAMILY
from auto_resubmit.pipeline import run_conversion


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate pairwise mutual conversion across all supported conference families."
    )
    parser.add_argument(
        "--seed-source-zip",
        type=Path,
        required=True,
        help="A seed source paper zip used to generate canonical source projects for each family.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where pairwise validation outputs are written.",
    )
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    canonical_dir = output_dir / "canonical_sources"
    matrix_dir = output_dir / "pairwise"
    canonical_dir.mkdir(parents=True, exist_ok=True)
    matrix_dir.mkdir(parents=True, exist_ok=True)

    canonical_sources: dict[str, Path] = {}
    summary: dict[str, object] = {
        "seed_source_zip": str(args.seed_source_zip.resolve()),
        "families": sorted(TESTDATA_TEMPLATE_BY_FAMILY),
        "canonical_sources": {},
        "pairwise": {},
    }

    for family, template_zip in TESTDATA_TEMPLATE_BY_FAMILY.items():
        family_output = canonical_dir / family
        result = run_conversion(
            source_zip=args.seed_source_zip.resolve(),
            target_template_zip=template_zip.resolve(),
            output_dir=family_output,
            review_md=None,
            keep_workdir=False,
        )
        canonical_sources[family] = result.zip_path
        summary["canonical_sources"][family] = {
            "zip_path": str(result.zip_path),
            "pdf_path": str(result.pdf_path) if result.pdf_path else None,
            "ok": bool(result.pdf_path),
            "warnings": result.warnings,
        }

    for source_family, source_zip in canonical_sources.items():
        row: dict[str, object] = {}
        for target_family, template_zip in TESTDATA_TEMPLATE_BY_FAMILY.items():
            pair_output = matrix_dir / f"{source_family}-to-{target_family}"
            result = run_conversion(
                source_zip=source_zip.resolve(),
                target_template_zip=template_zip.resolve(),
                output_dir=pair_output,
                review_md=None,
                keep_workdir=False,
            )
            row[target_family] = {
                "ok": bool(result.pdf_path),
                "zip_path": str(result.zip_path),
                "pdf_path": str(result.pdf_path) if result.pdf_path else None,
                "manifest_path": str(result.manifest_path),
                "warnings": result.warnings,
            }
            status = "ok" if result.pdf_path else "failed"
            print(f"{source_family} -> {target_family}: {status}")
        summary["pairwise"][source_family] = row

    summary_path = output_dir / "mutual_validation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
