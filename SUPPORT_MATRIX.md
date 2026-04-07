# Support Matrix

The project is organized around template families rather than per-year venue names.

## Supported Families

| Family | Venue Aliases | Representative Template Signal | Rendering Strategy | Bibliography Strategy |
|---|---|---|---|---|
| ACL family | `acl`, `emnlp` | `acl.sty` | standard `\maketitle` | `acl_natbib` |
| NeurIPS family | `neurips`, `nips` | `neurips_2026.sty` | standard `\maketitle` | `plainnat` fallback |
| ICML family | `icml` | `icml2026.sty` | `\icmltitle` + `\twocolumn[...]` + `\printAffiliationsAndNotice{}` | `icml2026` |
| ICLR family | `iclr` | `iclr2026_conference.sty` | standard `\maketitle` | `iclr2026_conference` |
| CVPR family | `cvpr`, `iccv` | `cvpr.sty` | standard `\maketitle` | `ieeenat_fullname` |
| AAAI family | `aaai` | `aaai2026.sty` | standard `\maketitle` + `\affiliations{}` | template-managed |

## Supported Coverage

Current supported family matrix:

| Source \ Target | ACL | NeurIPS | ICML | ICLR | CVPR | AAAI |
|---|---|---|---|---|---|---|
| ACL | ok | ok | ok | ok | ok | ok |
| NeurIPS | ok | ok | ok | ok | ok | ok |
| ICML | ok | ok | ok | ok | ok | ok |
| ICLR | ok | ok | ok | ok | ok | ok |
| CVPR | ok | ok | ok | ok | ok | ok |
| AAAI | ok | ok | ok | ok | ok | ok |

## What “Supported” Means

- The converter preserves extracted manuscript segments and migrates them into the target template family.
- Template-specific title-page and bibliography handling are implemented for the families above.
- Generated projects are intended to match the target template family structure closely enough to continue manual submission work.

## Known Boundaries

- Support is family-based, not a blanket guarantee for every future year or every custom workshop fork.
- Bibliography database quality is inherited from the source project.
- This repository does not claim responsibility for desk-reject causes unrelated to conversion, such as page limits, anonymity content, or policy declarations.
