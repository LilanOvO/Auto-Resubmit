import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auto_resubmit.latex import (
    build_source_representation,
    collapse_title_for_running_head,
    detect_project_kind_from_text,
    default_bibliographystyle,
    detect_target_kind,
    discover_main_tex,
    extract_preserved_source_preamble,
    find_matching_brace,
    merge_preambles,
    normalize_target_submission_mode,
    render_merged_tex,
    ParsedLatexProject,
    strip_autoresubmit_injected_blocks,
    strip_layout_modifying_commands,
)


class LatexParsingTests(unittest.TestCase):
    def test_find_matching_brace_handles_nested_content(self) -> None:
        text = r"\title{A {Nested} Title}"
        open_brace = text.index("{")
        self.assertEqual(find_matching_brace(text, open_brace), len(text) - 1)

    def test_discover_main_tex_prefers_root_main_tex(self) -> None:
        root = Path("test_prefer_root_main")
        nested = root / "latex"
        root.mkdir(exist_ok=True)
        nested.mkdir(exist_ok=True)
        (root / "main.tex").write_text(
            r"\documentclass{article}\title{Root}\begin{document}\maketitle\end{document}",
            encoding="utf-8",
        )
        (nested / "Formatting-Instructions-LaTeX-2026.tex").write_text(
            r"\documentclass{article}\title{Nested}\begin{document}\maketitle\begin{abstract}x\end{abstract}\end{document}",
            encoding="utf-8",
        )
        main_tex = discover_main_tex(root, preferred_names=("main.tex",))
        self.assertEqual(main_tex, root / "main.tex")
        (nested / "Formatting-Instructions-LaTeX-2026.tex").unlink()
        (root / "main.tex").unlink()
        nested.rmdir()
        root.rmdir()

    def test_collapse_title_for_running_head_strips_comments_and_spacing_commands(self) -> None:
        title = r"\includesvg[height=2em]{logo}\hspace{0.3em}% comment" "\n" r"Demo \\ Title"
        collapsed = collapse_title_for_running_head(title)
        self.assertEqual(collapsed, "Demo Title")

    def test_merge_preambles_keeps_source_macros_and_passes_options(self) -> None:
        target = r"""
\usepackage{xcolor}
\usepackage{booktabs}
"""
        source = r"""
\usepackage[table]{xcolor}
\usepackage{tikz}
\newcommand{\foo}{bar}
"""
        merged, pass_options = merge_preambles(target, source)
        self.assertIn(r"\usepackage{tikz}", merged)
        self.assertIn(r"\newcommand{\foo}{bar}", merged)
        self.assertEqual(pass_options["xcolor"], {"table"})

    def test_normalize_target_submission_mode_for_supported_families(self) -> None:
        self.assertEqual(
            normalize_target_submission_mode(r"\usepackage{acl}", "acl"),
            r"\usepackage[review]{acl}",
        )
        self.assertEqual(
            normalize_target_submission_mode(r"\usepackage[pagenumbers]{cvpr}", "cvpr"),
            r"\usepackage[review]{cvpr}",
        )
        self.assertEqual(
            normalize_target_submission_mode(r"\usepackage[main,final]{neurips_2026}", "neurips"),
            r"\usepackage[main]{neurips_2026}",
        )
        self.assertEqual(
            normalize_target_submission_mode(r"\usepackage[accepted]{icml2026}", "icml"),
            r"\usepackage{icml2026}",
        )
        self.assertEqual(
            normalize_target_submission_mode(r"\iclrfinalcopy" "\n" r"\usepackage{iclr2026_conference}", "iclr"),
            r"\usepackage{iclr2026_conference}",
        )
        self.assertEqual(
            normalize_target_submission_mode(r"\usepackage{aaai2026}", "aaai"),
            r"\usepackage[submission]{aaai2026}",
        )

    def test_strip_layout_modifying_commands_removes_pagination_and_geometry_tweaks(self) -> None:
        preamble = r"""
\setlength{\pdfpagewidth}{8.5in}
\setlength\columnsep{0.2in}
\geometry{margin=1in}
\pagestyle{empty}
\newcommand{\foo}{bar}
""".strip()
        cleaned, warnings = strip_layout_modifying_commands(preamble)
        self.assertNotIn(r"\setlength{\pdfpagewidth}{8.5in}", cleaned)
        self.assertNotIn(r"\setlength\columnsep{0.2in}", cleaned)
        self.assertNotIn(r"\geometry{margin=1in}", cleaned)
        self.assertNotIn(r"\pagestyle{empty}", cleaned)
        self.assertIn(r"\newcommand{\foo}{bar}", cleaned)
        self.assertTrue(warnings)

    def test_strip_autoresubmit_injected_blocks_removes_generated_review_guard(self) -> None:
        preamble = r"""
% Added from the source project to preserve paper content
\usepackage{tikz}
% Keep review-mode line numbers readable around wide floats in direct submission PDFs.
\usepackage{etoolbox}
\setlength{\linenumbersep}{1.25cm}
\makeatletter
\providecommand{\autoresubmit@resume@reviewlinenumbers}{\par\linenumbers}
\AtBeginEnvironment{table}{\par\nolinenumbers}
\AtEndEnvironment{table}{\autoresubmit@resume@reviewlinenumbers}
\makeatother
% Source project macros and local configuration
\newcommand{\foo}{bar}
""".strip()
        cleaned = strip_autoresubmit_injected_blocks(preamble)
        self.assertIn(r"\usepackage{tikz}", cleaned)
        self.assertIn(r"\newcommand{\foo}{bar}", cleaned)
        self.assertNotIn(r"\autoresubmit@resume@reviewlinenumbers", cleaned)
        self.assertNotIn(r"\setlength{\linenumbersep}{1.25cm}", cleaned)

    def test_strip_autoresubmit_injected_blocks_removes_acl_review_guard(self) -> None:
        preamble = r"""
\makeatletter
% lineno's built-in switching is page-based, so in two-column ACL review mode it leaves
% one column's rulers in the center gutter. Force the active column to choose its outer side.
\AtBeginDocument{%
  \runninglinenumbers
  \def\autoresubmit@makeLineNumberOuter{%
    \if@firstcolumn
      \makeLineNumberLeft
    \else
      \makeLineNumberRight
    \fi
  }%
  \setmakelinenumbers\autoresubmit@makeLineNumberOuter
}
\AtBeginEnvironment{thebibliography}{\nolinenumbers}
\AtEndEnvironment{thebibliography}{\runninglinenumbers}
\makeatother
""".strip()
        cleaned = strip_autoresubmit_injected_blocks(preamble)
        self.assertNotIn(r"\autoresubmit@makeLineNumberOuter", cleaned)
        self.assertNotIn(r"\runninglinenumbers", cleaned)
        self.assertNotIn(r"\AtBeginEnvironment{thebibliography}{\nolinenumbers}", cleaned)

    def test_detect_project_kind_from_text_prefers_main_tex_packages(self) -> None:
        preamble = r"""
\documentclass{article}
\usepackage[final]{neurips_2026}
""".strip()
        self.assertEqual(detect_project_kind_from_text(preamble), "neurips")

    def test_extract_preserved_source_preamble_prefers_inserted_source_block(self) -> None:
        preamble = r"""
\documentclass{article}
\usepackage{icml2026}
\newcommand{\fix}{\marginpar{FIX}}
% Added from the source project to preserve paper content
\usepackage{tikz}
% Source project macros and local configuration
\newcommand{\foo}{bar}
""".strip()
        preserved = extract_preserved_source_preamble(preamble)
        self.assertNotIn(r"\usepackage{icml2026}", preserved)
        self.assertNotIn(r"\newcommand{\fix}", preserved)
        self.assertIn(r"\usepackage{tikz}", preserved)
        self.assertIn(r"\newcommand{\foo}{bar}", preserved)

    def test_icml_target_detection_and_rendering(self) -> None:
        temp_dir = Path("test_icml_target")
        temp_dir.mkdir(exist_ok=True)
        (temp_dir / "icml2026.sty").write_text("", encoding="utf-8")
        target_kind = detect_target_kind(temp_dir)
        self.assertEqual(target_kind, "icml")

        project = ParsedLatexProject(
            root_dir=Path("."),
            main_tex=Path("resubmitted.tex"),
            target_kind="icml",
            documentclass=r"\documentclass{article}",
            title_block=r"\title{Demo \\ Title}",
            author_block=r"\author{}",
            date_block=r"\date{}",
            target_preamble=r"\usepackage{icml2026}",
            source_macro_preamble="",
            pass_options={},
            abstract="Abstract",
            main_body=r"\section{Intro}",
            bibliography_style="",
            bibliography_block=r"\bibliography{refs}",
            appendix_body=r"\appendix",
            warnings=[],
        )
        rendered = render_merged_tex(project, include_checklist=False)
        self.assertIn(r"\icmltitle{Demo \\ Title}", rendered)
        self.assertIn(r"\printAffiliationsAndNotice{}", rendered)
        self.assertIn(r"\bibliographystyle{icml2026}", rendered)
        (temp_dir / "icml2026.sty").unlink()
        temp_dir.rmdir()

    def test_cvpr_review_rendering_adds_submission_line_number_safeguards(self) -> None:
        project = ParsedLatexProject(
            root_dir=Path("."),
            main_tex=Path("resubmitted.tex"),
            target_kind="cvpr",
            documentclass=r"\documentclass[10pt,twocolumn,letterpaper]{article}",
            title_block=r"\title{Demo}",
            author_block=r"\author{}",
            date_block=r"\date{}",
            target_preamble=r"\usepackage[review]{cvpr}",
            source_macro_preamble="",
            pass_options={},
            abstract="Abstract",
            main_body=r"\begin{table*}\caption{Wide}\end{table*}",
            bibliography_style="",
            bibliography_block="",
            appendix_body="",
            warnings=[],
        )
        rendered = render_merged_tex(project, include_checklist=False)
        self.assertIn(r"\AtBeginDocument{\nolinenumbers}", rendered)
        self.assertNotIn(r"\AtBeginEnvironment{thebibliography}{\par\nolinenumbers}", rendered)

    def test_acl_rendering_preserves_official_review_line_number_behavior(self) -> None:
        project = ParsedLatexProject(
            root_dir=Path("."),
            main_tex=Path("resubmitted.tex"),
            target_kind="acl",
            documentclass=r"\documentclass[11pt]{article}",
            title_block=r"\title{Demo}",
            author_block=r"\author{}",
            date_block=r"\date{}",
            target_preamble=r"\usepackage[review]{acl}",
            source_macro_preamble="",
            pass_options={},
            abstract="Abstract",
            main_body=r"\section{Intro}",
            bibliography_style="",
            bibliography_block="",
            appendix_body="",
            warnings=[],
        )
        rendered = render_merged_tex(project, include_checklist=False)
        self.assertIn(r"\AtBeginDocument{\nolinenumbers}", rendered)
        self.assertNotIn(r"\AtBeginEnvironment{thebibliography}{\nolinenumbers}", rendered)

    def test_neurips_rendering_does_not_add_review_line_number_safeguards(self) -> None:
        project = ParsedLatexProject(
            root_dir=Path("."),
            main_tex=Path("resubmitted.tex"),
            target_kind="neurips",
            documentclass=r"\documentclass{article}",
            title_block=r"\title{Demo}",
            author_block=r"\author{}",
            date_block=r"\date{}",
            target_preamble=r"\usepackage{neurips_2026}",
            source_macro_preamble="",
            pass_options={},
            abstract="Abstract",
            main_body=r"\section{Intro}",
            bibliography_style="",
            bibliography_block="",
            appendix_body="",
            warnings=[],
        )
        rendered = render_merged_tex(project, include_checklist=False)
        self.assertNotIn(r"\setlength{\linenumbersep}{1.25cm}", rendered)
        self.assertNotIn(r"\AtBeginEnvironment{table*}{\par\nolinenumbers}", rendered)

    def test_detect_target_kind_for_aaai_and_defaults(self) -> None:
        temp_dir = Path("test_aaai_target")
        temp_dir.mkdir(exist_ok=True)
        (temp_dir / "aaai2026.sty").write_text("", encoding="utf-8")
        self.assertEqual(detect_target_kind(temp_dir), "aaai")
        self.assertEqual(default_bibliographystyle("cvpr"), r"\bibliographystyle{ieeenat_fullname}")
        self.assertEqual(default_bibliographystyle("iclr"), r"\bibliographystyle{iclr2026_conference}")
        (temp_dir / "aaai2026.sty").unlink()
        temp_dir.rmdir()

    def test_build_source_representation_from_cvpr_style_source(self) -> None:
        root = Path("test_cvpr_source")
        sec = root / "sec"
        root.mkdir(exist_ok=True)
        sec.mkdir(exist_ok=True)
        (root / "cvpr.sty").write_text("", encoding="utf-8")
        (sec / "0_abstract.tex").write_text("Abstract from input.", encoding="utf-8")
        (root / "main.tex").write_text(
            r"""
\documentclass{article}
\usepackage[review]{cvpr}
\title{Demo}
\author{Anon}
\begin{document}
\maketitle
\input{sec/0_abstract}
\section{Intro}
Hello.
{\small
\bibliographystyle{ieeenat_fullname}
\bibliography{main}
}
\end{document}
""".strip(),
            encoding="utf-8",
        )
        (
            _main_tex,
            source_preamble,
            _title_block,
            _author_block,
            _date_block,
            abstract,
            main_body,
            bibliography_style,
            bibliography_block,
            _appendix_body,
            _warnings,
        ) = build_source_representation(root)
        self.assertEqual(abstract, "Abstract from input.")
        self.assertIn(r"\section{Intro}", main_body)
        self.assertEqual(bibliography_style, r"\bibliographystyle{ieeenat_fullname}")
        self.assertEqual(bibliography_block, r"\bibliography{main}")
        (root / "main.tex").unlink()
        (root / "cvpr.sty").unlink()
        (sec / "0_abstract.tex").unlink()
        sec.rmdir()
        root.rmdir()

    def test_build_source_representation_from_icml_style_source(self) -> None:
        root = Path("test_icml_source")
        root.mkdir(exist_ok=True)
        (root / "icml2026.sty").write_text("", encoding="utf-8")
        (root / "example_paper.tex").write_text(
            r"""
\documentclass{article}
\usepackage{icml2026}
\icmltitlerunning{Demo}
\title{Ignored}
\begin{document}
\twocolumn[
  \icmltitle{Demo}
  \vskip 0.3in
]
\printAffiliationsAndNotice{}
\begin{abstract}
ICML abstract.
\end{abstract}
\section{Intro}
Hello.
\bibliography{refs}
\end{document}
""".strip(),
            encoding="utf-8",
        )
        (
            _main_tex,
            source_preamble,
            _title_block,
            _author_block,
            _date_block,
            abstract,
            main_body,
            _bibliography_style,
            bibliography_block,
            _appendix_body,
            _warnings,
        ) = build_source_representation(root)
        self.assertNotIn(r"\newcommand{\theHalgorithm}", source_preamble)
        self.assertEqual(abstract, "ICML abstract.")
        self.assertNotIn(r"\twocolumn[", main_body)
        self.assertIn(r"\section{Intro}", main_body)
        self.assertEqual(bibliography_block, r"\bibliography{refs}")
        (root / "example_paper.tex").unlink()
        (root / "icml2026.sty").unlink()
        root.rmdir()

    def test_build_source_representation_strips_aaai_pdfinfo_from_source_preamble(self) -> None:
        root = Path("test_aaai_source")
        root.mkdir(exist_ok=True)
        (root / "aaai2026.sty").write_text("", encoding="utf-8")
        (root / "anonymous-submission-latex-2026.tex").write_text(
            r"""
\documentclass{article}
\usepackage{aaai2026}
\usepackage[hyphens]{url}
\usepackage{natbib}
\pdfinfo{
/TemplateVersion (2026.1)
}
\title{Demo}
\author{Anon}
\affiliations{}
\begin{document}
\maketitle
\begin{abstract}
AAAI abstract.
\end{abstract}
\section{Intro}
Hello.
\bibliography{refs}
\end{document}
""".strip(),
            encoding="utf-8",
        )
        (
            _main_tex,
            source_preamble,
            _title_block,
            _author_block,
            _date_block,
            _abstract,
            _main_body,
            _bibliography_style,
            _bibliography_block,
            _appendix_body,
            _warnings,
        ) = build_source_representation(root)
        self.assertNotIn(r"\pdfinfo", source_preamble)
        self.assertNotIn(r"\affiliations{}", source_preamble)
        self.assertNotIn(r"\usepackage[hyphens]{url}", source_preamble)
        self.assertNotIn(r"\usepackage{natbib}", source_preamble)
        self.assertNotIn(r"\nocopyright", source_preamble)
        (root / "anonymous-submission-latex-2026.tex").unlink()
        (root / "aaai2026.sty").unlink()
        root.rmdir()

    def test_build_source_representation_strips_neurips_checklist_input(self) -> None:
        root = Path("test_neurips_source")
        root.mkdir(exist_ok=True)
        (root / "neurips_2026.sty").write_text("", encoding="utf-8")
        (root / "resubmitted.tex").write_text(
            r"""
\documentclass{article}
\usepackage{neurips_2026}
\title{Demo}
\author{Anon}
\begin{document}
\maketitle
\begin{abstract}
NeurIPS abstract.
\end{abstract}
\section{Intro}
Hello.
\bibliography{refs}
\appendix
\section{Extra}
World.
\newpage
\input{checklist.tex}
\end{document}
""".strip(),
            encoding="utf-8",
        )
        (
            _main_tex,
            _source_preamble,
            _title_block,
            _author_block,
            _date_block,
            _abstract,
            _main_body,
            _bibliography_style,
            _bibliography_block,
            appendix_body,
            _warnings,
        ) = build_source_representation(root)
        self.assertNotIn(r"\input{checklist.tex}", appendix_body)
        self.assertNotIn(r"\newpage", appendix_body)
        (root / "resubmitted.tex").unlink()
        (root / "neurips_2026.sty").unlink()
        root.rmdir()

    def test_build_source_representation_infers_algorithm_packages(self) -> None:
        root = Path("test_inferred_algorithm_source")
        root.mkdir(exist_ok=True)
        (root / "icml2026.sty").write_text("", encoding="utf-8")
        (root / "resubmitted.tex").write_text(
            r"""
\documentclass{article}
\usepackage{icml2026}
\title{Demo}
\begin{document}
\twocolumn[
  \icmltitle{Demo}
]
\begin{abstract}
Abstract.
\end{abstract}
\begin{algorithm}[t]
\caption{Demo}
\begin{algorithmic}[1]
\State hello
\end{algorithmic}
\end{algorithm}
\end{document}
""".strip(),
            encoding="utf-8",
        )
        (
            _main_tex,
            source_preamble,
            _title_block,
            _author_block,
            _date_block,
            _abstract,
            _main_body,
            _bibliography_style,
            _bibliography_block,
            _appendix_body,
            _warnings,
        ) = build_source_representation(root)
        self.assertIn(r"\usepackage{algorithm}", source_preamble)
        self.assertIn(r"\usepackage{algorithmic}", source_preamble)
        (root / "resubmitted.tex").unlink()
        (root / "icml2026.sty").unlink()
        root.rmdir()

    def test_build_source_representation_infers_table_and_math_packages(self) -> None:
        root = Path("test_inferred_table_math_source")
        root.mkdir(exist_ok=True)
        (root / "neurips_2026.sty").write_text("", encoding="utf-8")
        (root / "resubmitted.tex").write_text(
            r"""
\documentclass{article}
\usepackage{neurips_2026}
\title{Demo}
\begin{document}
\maketitle
\begin{abstract}
Abstract.
\end{abstract}
\begin{table}
\resizebox{\textwidth}{!}{
\begin{tabular}{ll}
\toprule
\multirow{2}{*}{A} & B \\
\bottomrule
\end{tabular}
}
\end{table}
\begin{equation}
\triangleq \mathbb{R}
\end{equation}
\end{document}
""".strip(),
            encoding="utf-8",
        )
        (
            _main_tex,
            source_preamble,
            _title_block,
            _author_block,
            _date_block,
            _abstract,
            _main_body,
            _bibliography_style,
            _bibliography_block,
            _appendix_body,
            _warnings,
        ) = build_source_representation(root)
        self.assertIn(r"\usepackage{graphicx}", source_preamble)
        self.assertIn(r"\usepackage{multirow}", source_preamble)
        self.assertIn(r"\usepackage{booktabs}", source_preamble)
        self.assertIn(r"\usepackage{amssymb}", source_preamble)
        (root / "resubmitted.tex").unlink()
        (root / "neurips_2026.sty").unlink()
        root.rmdir()

    def test_build_source_representation_infers_caption_from_source_preamble_macros(self) -> None:
        root = Path("test_inferred_caption_source")
        root.mkdir(exist_ok=True)
        (root / "aaai2026.sty").write_text("", encoding="utf-8")
        (root / "main.tex").write_text(
            r"""
\documentclass{article}
\usepackage[submission]{aaai2026}
\usepackage{graphicx}
\DeclareCaptionStyle{ruled}{labelfont=normalfont}
\title{Demo}
\author{Anon}
\begin{document}
\maketitle
\begin{abstract}
Abstract.
\end{abstract}
\section{Intro}
Hello.
\end{document}
""".strip(),
            encoding="utf-8",
        )
        (
            _main_tex,
            source_preamble,
            _title_block,
            _author_block,
            _date_block,
            _abstract,
            _main_body,
            _bibliography_style,
            _bibliography_block,
            _appendix_body,
            _warnings,
        ) = build_source_representation(root)
        self.assertIn(r"\usepackage{caption}", source_preamble)
        (root / "main.tex").unlink()
        (root / "aaai2026.sty").unlink()
        root.rmdir()

    def test_build_source_representation_infers_links_environment_compatibility(self) -> None:
        root = Path("test_links_source")
        root.mkdir(exist_ok=True)
        (root / "aaai2026.sty").write_text("", encoding="utf-8")
        (root / "main.tex").write_text(
            r"""
\documentclass{article}
\usepackage{aaai2026}
\title{Demo}
\begin{document}
\maketitle
\begin{abstract}
Abstract.
\end{abstract}
\begin{links}
\link{Code}{https://example.com/code}
\end{links}
\section{Intro}
Hello.
\end{document}
""".strip(),
            encoding="utf-8",
        )
        (
            _main_tex,
            source_preamble,
            _title_block,
            _author_block,
            _date_block,
            _abstract,
            _main_body,
            _bibliography_style,
            _bibliography_block,
            _appendix_body,
            _warnings,
        ) = build_source_representation(root)
        self.assertIn(r"\providecommand{\link}[2]{\item \textbf{#1}: \url{#2}}", source_preamble)
        self.assertIn(r"\newenvironment{links}{\begin{itemize}}{\end{itemize}}", source_preamble)
        (root / "main.tex").unlink()
        (root / "aaai2026.sty").unlink()
        root.rmdir()

    def test_build_source_representation_extracts_title_and_bibliography(self) -> None:
        tmp_path = Path(self._testMethodName)
        if tmp_path.exists():
            for file_path in tmp_path.rglob("*"):
                if file_path.is_file():
                    file_path.unlink()
            for dir_path in sorted((path for path in tmp_path.rglob("*") if path.is_dir()), reverse=True):
                dir_path.rmdir()
            tmp_path.rmdir()
        tmp_path.mkdir()

        tex = tmp_path / "paper.tex"
        tex.write_text(
            r"""
\documentclass{article}
\title{Demo}
\author{Anonymous}
\begin{document}
\maketitle
\begin{abstract}
Abstract text.
\end{abstract}
\section{Intro}
Hello.
\bibliography{refs}
\appendix
\section{Extra}
World.
\end{document}
""".strip(),
            encoding="utf-8",
        )
        (
            _main_tex,
            _preamble,
            title_block,
            author_block,
            _date_block,
            abstract,
            main_body,
            _bibliography_style,
            bibliography_block,
            appendix_body,
            _warnings,
        ) = build_source_representation(tmp_path)
        self.assertEqual(title_block, r"\title{Demo}")
        self.assertEqual(author_block, r"\author{Anonymous}")
        self.assertEqual(abstract, "Abstract text.")
        self.assertIn(r"\section{Intro}", main_body)
        self.assertEqual(bibliography_block, r"\bibliography{refs}")
        self.assertTrue(appendix_body.startswith(r"\appendix"))

        tex.unlink()
        tmp_path.rmdir()


if __name__ == "__main__":
    unittest.main()
