<div align="center">
<h1>
  <img src="assets/auto-resubmit-banner.png" alt="Auto-Resubmit logo" width="104" />
  Auto-Resubmit
</h1>

<p><strong>面向会议重投的 LaTeX 模板无损迁移工具。</strong></p>

<p>
  <img src="https://img.shields.io/badge/ACL-0f766e?style=flat-square" alt="ACL" />
  <img src="https://img.shields.io/badge/EMNLP-0ea5e9?style=flat-square" alt="EMNLP" />
  <img src="https://img.shields.io/badge/NeurIPS-7c3aed?style=flat-square" alt="NeurIPS" />
  <img src="https://img.shields.io/badge/NIPS-a855f7?style=flat-square" alt="NIPS" />
  <img src="https://img.shields.io/badge/ICML-f97316?style=flat-square" alt="ICML" />
  <img src="https://img.shields.io/badge/ICLR-ef4444?style=flat-square" alt="ICLR" />
  <img src="https://img.shields.io/badge/CVPR-2563eb?style=flat-square" alt="CVPR" />
  <img src="https://img.shields.io/badge/ICCV-1d4ed8?style=flat-square" alt="ICCV" />
  <img src="https://img.shields.io/badge/AAAI-0891b2?style=flat-square" alt="AAAI" />
</p>

<p><strong>支持这些会议家族之间的相互转换</strong></p>

<p><code>源论文 Zip</code> → <code>Auto-Resubmit 自动迁移</code> → <code>目标会议模板 Zip</code></p>

<p>
  <a href="README.md">English</a> ·
  <a href="SUPPORT_MATRIX.md">支持矩阵</a>
</p>

<p>
  <img src="https://img.shields.io/badge/Offline-First-1f6feb?style=flat-square" alt="Offline First" />
  <img src="https://img.shields.io/badge/Lossless-Migration-0f766e?style=flat-square" alt="Lossless Migration" />
  <img src="https://img.shields.io/badge/Families-ACL%20%7C%20NeurIPS%20%7C%20ICML%20%7C%20ICLR%20%7C%20CVPR%20%7C%20AAAI-7c3aed?style=flat-square" alt="Supported Families" />
</p>
</div>

## 项目简介

Auto-Resubmit 用来把源 LaTeX 论文项目 zip 迁移到目标会议模板 zip，同时尽量保持论文内容不变。

它主要解决 ACL、EMNLP、NeurIPS、NIPS、ICML、ICLR、CVPR、ICCV、AAAI 等会议家族之间的重投模板迁移问题：

- 读取源论文项目 zip
- 读取目标会议模板 zip
- 自动识别主稿入口
- 抽取标题、摘要、正文、参考文献块、附录和所需宏定义
- 按目标会议模板家族重新组装论文
- 复制图片、`.bib` 和本地资源
- 编译并打包输出

## 当前支持的会议家族

| 家族 | 会议别名 |
| --- | --- |
| ACL 家族 | `acl`, `emnlp` |
| NeurIPS 家族 | `neurips`, `nips` |
| ICML 家族 | `icml` |
| ICLR 家族 | `iclr` |
| CVPR 家族 | `cvpr`, `iccv` |
| AAAI 家族 | `aaai` |

详细说明见 [SUPPORT_MATRIX.md](SUPPORT_MATRIX.md)

## 安装

- Python 3.10+
- 可用的 `tectonic` 编译器，用于生成 PDF

先创建并安装 Python 环境：

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

再确认 LaTeX 编译器可用：

```bash
tectonic --version
```

## 快速开始

```bash
auto_resubmit run \
  --source-zip /path/to/source-paper.zip \
  --target-template-zip /path/to/target-template.zip \
  --output-dir /path/to/output-dir
```

## 输出内容

运行成功后，输出目录通常包含：

- `converted_project.zip`
- `converted_project/resubmitted.tex`
- `converted_project/resubmitted.pdf`
- `conversion_manifest.json`
- `content_audit.json`
- `converted_project/tectonic.log`

## 输入建议

- 源输入应为 LaTeX 项目 zip，而不是 PDF
- 目标输入应为官方会议模板 zip
- 源 zip 最好只包含一个真正的主稿入口
- 图片、`.bib`、本地 `.sty` 等依赖文件应一并打包
- 依赖私有脚本或缺失外部资源的项目不在当前支持范围内

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=LilanOvO/Auto-Resubmit&type=Date)](https://star-history.com/#LilanOvO/Auto-Resubmit&Date)

## 后续计划

这个仓库目前还是 Auto-Resubmit 的初步版本。

我后续希望把它继续做成一个多 agent 系统，能够：

- 自动识别审稿意见里真正有价值、可执行的部分
- 基于上一会的论文自动完成进一步优化和修改
- 在内容更新后，把论文更完整、更稳定地迁移到目标会议模板

如果你对这个方向感兴趣，欢迎一起合作、加入 contributor。联系邮箱：`zjuqww@gmail.com`
