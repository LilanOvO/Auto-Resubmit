<div align="center">
  <img src="assets/auto-resubmit-header.png" alt="Auto-Resubmit" width="860" />

<p><strong>Lossless LaTeX template migration for conference resubmission.</strong></p>

<p>
  <img src="https://img.shields.io/badge/ACL-0f766e?style=flat-square" alt="ACL" />
  <img src="https://img.shields.io/badge/EMNLP-0ea5e9?style=flat-square" alt="EMNLP" />
  <img src="https://img.shields.io/badge/NeurIPS-7c3aed?style=flat-square" alt="NeurIPS" />
  <img src="https://img.shields.io/badge/ICML-f97316?style=flat-square" alt="ICML" />
  <img src="https://img.shields.io/badge/ICLR-ef4444?style=flat-square" alt="ICLR" />
  <img src="https://img.shields.io/badge/CVPR-2563eb?style=flat-square" alt="CVPR" />
  <img src="https://img.shields.io/badge/ICCV-1d4ed8?style=flat-square" alt="ICCV" />
  <img src="https://img.shields.io/badge/AAAI-0891b2?style=flat-square" alt="AAAI" />
</p>

<p><strong>Mutual Conversion Across Supported Conference Families</strong></p>

<p><code>Source Paper Zip</code> → <code>Auto-Resubmit Lossless Migration</code> → <code>Target Conference Template Zip</code></p>

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

## Overview 🧭

Auto-Resubmit converts a source LaTeX paper zip into a target conference template zip while keeping the manuscript content intact.

自动重投：支持 ACL、EMNLP、NeurIPS、NIPS、ICML、ICLR、CVPR、ICCV、AAAI 等会议家族之间的模板互转。给定“源论文 LaTeX 项目 zip”和“目标会议模板 zip”，工具会自动抽取论文主体内容，并按目标会议模板重新组装、编译和打包，尽量减少手工改模板的工作量。

It is designed for the common resubmission workflow:

- read a source paper project zip
- read a target template zip
- detect the main manuscript entry
- extract title, abstract, body, bibliography block, appendix, and required macros
- rebuild the paper in the target template family
- copy figures, `.bib`, and local assets
- compile the converted project and package the result

## Supported Families 🔁

| Family | Venue Names |
| --- | --- |
| ACL family | `acl`, `emnlp` |
| NeurIPS family | `neurips`, `nips` |
| ICML family | `icml` |
| ICLR family | `iclr` |
| CVPR family | `cvpr`, `iccv` |
| AAAI family | `aaai` |

Details: [SUPPORT_MATRIX.md](SUPPORT_MATRIX.md)

## Installation ⚙️

### Requirements

- Python `3.10+`
- `pip`
- `tectonic`

### Python Dependencies

Auto-Resubmit currently uses only the Python standard library.

- Third-party Python packages: none
- External tool required for PDF compilation: `tectonic`

`python -m pip install --editable .` installs the current repository itself and exposes the `auto_resubmit` command-line entrypoint.

### Option A: `conda`

```bash
git clone https://github.com/LilanOvO/Auto-Resubmit.git
cd Auto-Resubmit

conda create -n auto-resubmit python=3.10 -y
conda activate auto-resubmit
python -m pip install --editable .
```

### Option B: `venv`

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --editable .
```

If you do not need editable mode, you can also use:

```bash
python -m pip install .
```

### Install `tectonic`

Install `tectonic` separately. After installation, this command should work:

```bash
tectonic --version
```

Typical install options:

```bash
# conda
conda install -c conda-forge tectonic
```

```bash
# cargo
cargo install tectonic
```

```bash
# macOS
brew install tectonic
```

If `tectonic` is missing, the project can still generate the converted LaTeX project, but it will not produce the final PDF.

### Verify the Installation

After `pip install --editable .`, at least one of the following should work:

```bash
auto_resubmit --help
```

```bash
python -m auto_resubmit --help
```

## Quick Start 🚀

```bash
auto_resubmit run \
  --source-zip /path/to/source-paper.zip \
  --target-template-zip /path/to/target-template.zip \
  --output-dir /path/to/output-dir
```

If `auto_resubmit` is not found in your shell, use:

```bash
python -m auto_resubmit run \
  --source-zip /path/to/source-paper.zip \
  --target-template-zip /path/to/target-template.zip \
  --output-dir /path/to/output-dir
```

## Output 📦

On success, the output directory contains:

- `converted_project.zip`
- `converted_project/resubmitted.tex`
- `converted_project/resubmitted.pdf`
- `conversion_manifest.json`
- `content_audit.json`
- `converted_project/tectonic.log`

## Input Guidelines 📝

- Source input should be a LaTeX project zip, not a PDF
- Target input should be an official conference template zip
- The source zip should contain one real manuscript entrypoint
- Figures, `.bib`, and local `.sty` files should be included in the zip
- Projects that depend on private shell scripts or missing external assets are out of scope

## Troubleshooting 🩺

- `auto_resubmit: command not found`
  Use `python -m auto_resubmit --help` first. If that works, your environment is fine and only the shell entrypoint is missing.
- `compiler: not_found`
  `tectonic` is not installed or not on `PATH`.
- `pdf_path: not_generated`
  The converted LaTeX project was generated, but PDF compilation failed. Check `converted_project/tectonic.log`.
- first `tectonic` run is slow
  This is normal. `tectonic` may need to populate its local cache on first use.

## Star History ⭐

<a href="https://www.star-history.com/?repos=LilanOvO%2FAuto-Resubmit&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=LilanOvO/Auto-Resubmit&type=date&theme=dark&legend=top-left&v=1" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=LilanOvO/Auto-Resubmit&type=date&legend=top-left&v=1" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=LilanOvO/Auto-Resubmit&type=date&legend=top-left&v=1" />
 </picture>
</a>

## Roadmap 🛣️

This repository is still an early version of Auto-Resubmit.

The longer-term goal is to evolve it into a multi-agent system that can:

- identify the reviewer feedback that is actually actionable
- revise and improve a paper from the previous venue
- migrate the final manuscript into the target conference template with cleaner automation

If this direction interests you, collaborations are welcome. If you would like to contribute and join as a contributor, feel free to contact me at `zjuqww@gmail.com`.
