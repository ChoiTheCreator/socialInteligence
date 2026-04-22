#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd


def set_korean_font() -> None:
    # Pick an installed Korean-capable font for axis labels/titles.
    installed = {f.name for f in fm.fontManager.ttflist}
    for name in ["AppleGothic", "Malgun Gothic", "NanumGothic", "DejaVu Sans"]:
        if name in installed:
            matplotlib.rcParams["font.family"] = name
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot latest month employment by age group")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="CSV input path (default: first CSV under employment_wage/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("employment_wage/viz/employment_by_age_latest.png"),
        help="Output PNG path",
    )
    return parser.parse_args()


def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    for enc in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("csv", b"", 0, 1, f"Failed to decode: {path}")


def age_sort_key(label: str) -> int:
    if label.strip() == "계":
        return -1
    m = re.search(r"(\d+)\s*-\s*(\d+)세", label)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)세\s*이상", label)
    if m:
        return int(m.group(1))
    return 999


def main() -> None:
    args = parse_args()
    root = Path.cwd()

    if args.input is None:
        candidates = sorted((root / "employment_wage").glob("*.csv"))
        if not candidates:
            raise FileNotFoundError("No CSV found under employment_wage/")
        input_csv = candidates[0]
    else:
        input_csv = args.input

    df = read_csv_with_fallback(input_csv)

    # Keep national total row-group and remove the all-ages total.
    if "시도별(1)" in df.columns:
        df = df[df["시도별(1)"] == "계"].copy()

    age_col = "연령계층별(1)"
    df = df[df[age_col] != "계"].copy()

    month_cols = [c for c in df.columns if re.fullmatch(r"\d{4}\.\d{2}", str(c))]
    if not month_cols:
        raise ValueError("No YYYY.MM columns found")
    latest_col = sorted(month_cols)[-1]

    df[latest_col] = pd.to_numeric(df[latest_col], errors="coerce")
    plot_df = df[[age_col, latest_col]].dropna().copy()
    canonical_ages = ["15 - 19세", "20 - 29세", "30 - 39세", "40 - 49세", "50 - 59세", "60세이상"]
    if set(canonical_ages).issubset(set(plot_df[age_col])):
        # Avoid overlapping ranges such as 15-29, 15-64 when detailed bins exist.
        plot_df = plot_df[plot_df[age_col].isin(canonical_ages)].copy()
    plot_df = plot_df.sort_values(by=age_col, key=lambda s: s.map(age_sort_key))

    set_korean_font()
    plt.figure(figsize=(10, 6))
    bars = plt.bar(plot_df[age_col], plot_df[latest_col], color="#1f77b4")
    plt.title(f"연령계층별 취업자 수 ({latest_col}, 전국)")
    plt.xlabel("연령계층")
    plt.ylabel("취업자 수")
    plt.xticks(rotation=35, ha="right")

    # Add compact value labels on bars.
    for b in bars:
        height = b.get_height()
        plt.text(b.get_x() + b.get_width() / 2, height, f"{int(height):,}", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(args.output, dpi=180)
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
