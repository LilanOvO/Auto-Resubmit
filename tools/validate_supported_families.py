from __future__ import annotations

import argparse
from pathlib import Path

from auto_resubmit.conferences import TESTDATA_TEMPLATE_BY_FAMILY
from auto_resubmit.pipeline import run_conversion


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate supported conference families using local testdata.")
    parser.add_argument("--source-zip", type=Path, required=True, help="Source paper zip used for validation.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory where validation outputs are written.")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for family, template_zip in TESTDATA_TEMPLATE_BY_FAMILY.items():
        family_output = args.output_dir / family
        result = run_conversion(
            source_zip=args.source_zip.resolve(),
            target_template_zip=template_zip.resolve(),
            output_dir=family_output.resolve(),
            review_md=None,
            keep_workdir=False,
        )
        print(f"{family}: {'ok' if result.pdf_path else 'failed'} -> {family_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
