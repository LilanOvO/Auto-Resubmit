from __future__ import annotations

from pathlib import Path


CONFERENCE_TO_FAMILY = {
    "acl": "acl",
    "emnlp": "acl",
    "neurips": "neurips",
    "nips": "neurips",
    "icml": "icml",
    "iclr": "iclr",
    "cvpr": "cvpr",
    "iccv": "cvpr",
    "aaai": "aaai",
}


TESTDATA_TEMPLATE_BY_FAMILY = {
    "acl": Path("testdata/acl-style-files-master.zip"),
    "neurips": Path("testdata/Formatting_Instructions_For_NeurIPS_2026 (1).zip"),
    "icml": Path("testdata/icml2026.zip"),
    "iclr": Path("testdata/iclr2026.zip"),
    "cvpr": Path("testdata/author-kit-CVPR2026-v1-latex-.zip"),
    "aaai": Path("testdata/AAAI.zip"),
}


def normalize_conference_name(name: str) -> str:
    lowered = name.strip().lower()
    if lowered not in CONFERENCE_TO_FAMILY:
        raise KeyError(f"Unsupported conference alias: {name}")
    return lowered


def conference_family(name: str) -> str:
    return CONFERENCE_TO_FAMILY[normalize_conference_name(name)]


def template_zip_for_conference(name: str) -> Path:
    return TESTDATA_TEMPLATE_BY_FAMILY[conference_family(name)]
