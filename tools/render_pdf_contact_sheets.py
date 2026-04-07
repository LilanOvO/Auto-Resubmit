from __future__ import annotations

import argparse
import math
import shutil
import subprocess
from pathlib import Path


def find_pdfs(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("resubmitted.pdf") if path.is_file())


def render_pages(pdf_path: Path, page_dir: Path, dpi: int) -> list[Path]:
    page_dir.mkdir(parents=True, exist_ok=True)
    prefix = page_dir / "page"
    command = [
        "pdftoppm",
        "-png",
        "-r",
        str(dpi),
        str(pdf_path),
        str(prefix),
    ]
    subprocess.run(command, check=True)
    return sorted(page_dir.glob("page-*.png"))


def build_contact_sheet(page_paths: list[Path], output_path: Path, columns: int) -> None:
    if not page_paths:
        return
    rows = math.ceil(len(page_paths) / columns)
    tile = f"{columns}x{rows}"
    command = [
        "ffmpeg",
        "-y",
        "-pattern_type",
        "glob",
        "-i",
        str(page_paths[0].parent / "page-*.png"),
        "-frames:v",
        "1",
        "-filter_complex",
        f"tile={tile}:padding=24:margin=24:color=white",
        str(output_path),
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render resubmitted PDFs into per-document contact sheets.")
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory containing converted project outputs.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory where sheets are written.")
    parser.add_argument("--dpi", type=int, default=120, help="Rasterization DPI for page images.")
    parser.add_argument("--columns", type=int, default=3, help="Number of columns in each contact sheet.")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove any previous contact sheet directory before rendering.",
    )
    args = parser.parse_args()

    if shutil.which("pdftoppm") is None:
        raise SystemExit("pdftoppm is required but was not found in PATH")
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required but was not found in PATH")

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    if args.clean:
        shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_paths = find_pdfs(input_dir)
    if not pdf_paths:
        raise SystemExit(f"No resubmitted.pdf files found under {input_dir}")

    for pdf_path in pdf_paths:
        rel_parent = pdf_path.parent.relative_to(input_dir)
        page_dir = output_dir / rel_parent / "pages"
        sheet_path = output_dir / rel_parent / "contact-sheet.png"
        page_paths = render_pages(pdf_path, page_dir, dpi=args.dpi)
        build_contact_sheet(page_paths, sheet_path, columns=args.columns)
        print(f"{pdf_path} -> {sheet_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
