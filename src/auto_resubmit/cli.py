from __future__ import annotations

import argparse
from pathlib import Path

from auto_resubmit.pipeline import run_conversion


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="auto_resubmit",
        description="Convert a source LaTeX paper project into a target conference template.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a paper conversion job.")
    run_parser.add_argument("--source-zip", type=Path, required=True, help="Path to the source paper zip.")
    run_parser.add_argument(
        "--target-template-zip",
        type=Path,
        required=True,
        help="Path to the target conference template zip.",
    )
    run_parser.add_argument("--output-dir", type=Path, required=True, help="Directory for all generated outputs.")
    run_parser.add_argument("--review-md", type=Path, help="Optional review markdown used for revision notes.")
    run_parser.add_argument(
        "--disable-llm",
        action="store_true",
        help="Accepted for compatibility. The current MVP runs fully offline.",
    )
    run_parser.add_argument(
        "--clean-workdir",
        action="store_true",
        help="Delete extracted working files after packaging the final project.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        source_zip = args.source_zip.expanduser().resolve()
        target_template_zip = args.target_template_zip.expanduser().resolve()
        output_dir = args.output_dir.expanduser().resolve()
        review_md = args.review_md.expanduser().resolve() if args.review_md else None

        result = run_conversion(
            source_zip=source_zip,
            target_template_zip=target_template_zip,
            output_dir=output_dir,
            review_md=review_md,
            keep_workdir=not args.clean_workdir,
        )
        print(f"project_dir: {result.project_dir}")
        print(f"main_tex: {result.main_tex}")
        print(f"zip_path: {result.zip_path}")
        print(f"manifest_path: {result.manifest_path}")
        print(f"compiler: {result.compiler or 'not_found'}")
        print(f"pdf_path: {result.pdf_path or 'not_generated'}")
        if result.compile_log:
            print(f"compile_log: {result.compile_log}")
        if result.warnings:
            print("warnings:")
            for warning in result.warnings:
                print(f"- {warning}")
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2
