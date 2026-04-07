<div align="center">
  <img src="assets/auto-resubmit-banner.png" alt="Auto-Resubmit banner" width="320" />

# Auto-Resubmit

<p><strong>Lossless LaTeX template migration for conference resubmission.</strong></p>

<p>
  <a href="README_zh.md">简体中文</a> ·
  <a href="SUPPORT_MATRIX.md">Support Matrix</a>
</p>

<p>
  <img src="https://img.shields.io/badge/Offline-First-1f6feb?style=flat-square" alt="Offline First" />
  <img src="https://img.shields.io/badge/Lossless-Migration-0f766e?style=flat-square" alt="Lossless Migration" />
  <img src="https://img.shields.io/badge/Families-ACL%20%7C%20NeurIPS%20%7C%20ICML%20%7C%20ICLR%20%7C%20CVPR%20%7C%20AAAI-7c3aed?style=flat-square" alt="Supported Families" />
</p>
</div>

## Overview

Auto-Resubmit converts a source LaTeX paper zip into a target conference template zip while keeping the manuscript content intact.

中文说明：给定“源论文 LaTeX 项目 zip”和“目标会议模板 zip”，工具会自动抽取论文主体内容，并按目标会议模板重新组装、编译和打包，尽量减少手工改模板的工作量。

It is designed for the common resubmission workflow:

- read a source paper project zip
- read a target template zip
- detect the main manuscript entry
- extract title, abstract, body, bibliography block, appendix, and required macros
- rebuild the paper in the target template family
- copy figures, `.bib`, and local assets
- compile the converted project and package the result

## Supported Families

| Family | Venue Names |
| --- | --- |
| ACL family | `acl`, `emnlp` |
| NeurIPS family | `neurips`, `nips` |
| ICML family | `icml` |
| ICLR family | `iclr` |
| CVPR family | `cvpr`, `iccv` |
| AAAI family | `aaai` |

Details: [SUPPORT_MATRIX.md](SUPPORT_MATRIX.md)

## Installation

- Python 3.10+
- A working `tectonic` installation for PDF compilation

Set up the Python environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Check that the LaTeX compiler is available:

```bash
tectonic --version
```

## Quick Start

```bash
PYTHONPATH=src python -m auto_resubmit run \
  --source-zip /path/to/source-paper.zip \
  --target-template-zip /path/to/target-template.zip \
  --output-dir /path/to/output-dir
```

## Output

On success, the output directory contains:

- `converted_project.zip`
- `converted_project/resubmitted.tex`
- `converted_project/resubmitted.pdf`
- `conversion_manifest.json`
- `content_audit.json`
- `converted_project/tectonic.log`

## Input Guidelines

- Source input should be a LaTeX project zip, not a PDF
- Target input should be an official conference template zip
- The source zip should contain one real manuscript entrypoint
- Figures, `.bib`, and local `.sty` files should be included in the zip
- Projects that depend on private shell scripts or missing external assets are out of scope

## Validation Tools

Validate one source project against all supported families:

```bash
PYTHONPATH=src python tools/validate_supported_families.py \
  --source-zip /path/to/source-paper.zip \
  --output-dir outputs/supported-families
```

Run the pairwise family-to-family validation matrix:

```bash
PYTHONPATH=src python tools/validate_mutual_families.py \
  --seed-source-zip /path/to/source-paper.zip \
  --output-dir outputs/mutual-matrix
```

Render PDF contact sheets for manual inspection:

```bash
python tools/render_pdf_contact_sheets.py \
  --input-dir outputs/mutual-matrix \
  --output-dir outputs/contact-sheets \
  --clean
```

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=LilanOvO/Auto-Resubmit&type=Date)](https://star-history.com/#LilanOvO/Auto-Resubmit&Date)
