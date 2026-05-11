#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


METRIC_ASSUMPTIONS = [
    {
        "metric": "female_employed_share",
        "label": "여성 취업자 비중",
        "direction": "higher_is_better",
        "dimension": "포용성",
        "caution": "고용률이 아니라 취업자 구성비다. 여성 노동시장 참여의 proxy로만 해석한다.",
    },
    {
        "metric": "male_female_employed_share_gap",
        "label": "남녀 취업자 구성비 격차",
        "direction": "lower_is_better",
        "dimension": "포용성",
        "caution": "고용률 격차가 아니라 취업자 구성비 격차다.",
    },
    {
        "metric": "youth_employed_share",
        "label": "청년층 취업자 비중",
        "direction": "higher_is_better",
        "dimension": "청년 고용 여건",
        "caution": "청년 고용률이 아니라 취업자 중 청년층 비중이다. 지역 연령구조 영향을 받는다.",
    },
    {
        "metric": "wage_worker_share",
        "label": "임금근로자 비중",
        "direction": "higher_is_better",
        "dimension": "고용 안정성",
        "caution": "임금근로자 비중을 안정성 proxy로 사용한다. 일자리 질 전체를 대표하지는 않는다.",
    },
    {
        "metric": "temporary_worker_ratio",
        "label": "임시근로자 비율",
        "direction": "lower_is_better",
        "dimension": "고용 안정성",
        "caution": "전체 취업자 대비 임시근로자 비율이다.",
    },
    {
        "metric": "daily_worker_ratio",
        "label": "일용근로자 비율",
        "direction": "lower_is_better",
        "dimension": "고용 안정성",
        "caution": "전체 취업자 대비 일용근로자 비율이다.",
    },
    {
        "metric": "self_employed_ratio",
        "label": "자영업자 비율",
        "direction": "lower_is_better",
        "dimension": "고용 안정성",
        "caution": "자영업이 항상 낮은 삶의 질을 의미하지는 않는다. 불안정성 proxy로만 제한 해석한다.",
    },
    {
        "metric": "short_hours_worker_ratio",
        "label": "단시간 취업자 비율",
        "direction": "lower_is_better",
        "dimension": "노동시간",
        "caution": "단시간 근로는 자발적 선택일 수도 있다. 불완전취업 가능성 proxy로만 해석한다.",
    },
    {
        "metric": "long_hours_worker_ratio",
        "label": "장시간 취업자 비율",
        "direction": "lower_is_better",
        "dimension": "노동시간",
        "caution": "장시간 노동 부담 proxy로 해석한다.",
    },
]

REFERENCE_METRICS = [
    {
        "metric": "senior_employed_share",
        "label": "고령층 취업자 비중",
        "direction": "reference_only",
        "dimension": "인구·노동시장 구조",
        "caution": "높고 낮음 자체를 삶의 질 좋고 나쁨으로 점수화하지 않는다.",
    },
]


def resolve_repo_root() -> Path:
    current = Path.cwd().resolve()
    for path in [current, *current.parents]:
        if (path / "data").exists() and (path / "employment_wage").exists():
            return path
    fallback = Path("/Users/choewonbin/Desktop/socialInteli/Projct")
    if (fallback / "data").exists() and (fallback / "employment_wage").exists():
        return fallback
    raise FileNotFoundError("저장소 루트를 찾을 수 없습니다.")


def set_korean_font() -> None:
    installed = {font.name for font in fm.fontManager.ttflist}
    for name in ["AppleGothic", "Apple SD Gothic Neo", "Arial Unicode MS", "Malgun Gothic", "Nanum Gothic", "DejaVu Sans"]:
        if name in installed:
            matplotlib.rcParams["font.family"] = name
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


def minmax_score(series: pd.Series, direction: str) -> pd.Series:
    valid = series.dropna()
    if valid.empty or valid.max() == valid.min():
        return pd.Series(np.nan, index=series.index)
    score = (series - valid.min()) / (valid.max() - valid.min()) * 100
    if direction == "lower_is_better":
        score = 100 - score
    return score


def save_plot(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def main() -> None:
    repo_root = resolve_repo_root()
    panel_path = repo_root / "data" / "processed" / "kosis_life_quality_employment_panel.csv"
    tables_dir = repo_root / "employment_wage" / "outputs" / "tables"
    figures_dir = repo_root / "employment_wage" / "outputs" / "figures"
    output_md = repo_root / "employment_wage" / "outputs" / "employment_qol_proxy_analysis.md"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    set_korean_font()
    sns.set_theme(style="whitegrid")
    set_korean_font()

    panel = pd.read_csv(panel_path)
    assumptions = pd.DataFrame(METRIC_ASSUMPTIONS + REFERENCE_METRICS)
    assumptions.to_csv(tables_dir / "10_employment_qol_proxy_metric_assumptions.csv", index=False, encoding="utf-8-sig")

    available = [row["metric"] for row in METRIC_ASSUMPTIONS if row["metric"] in panel.columns and panel[row["metric"]].notna().any()]
    if not available:
        raise ValueError("고용 기반 삶의 질 proxy를 만들 수 있는 변수가 없습니다.")

    score_df = panel[["year", "region", "metro_area"] + available].copy()
    for row in METRIC_ASSUMPTIONS:
        metric = row["metric"]
        if metric not in score_df.columns:
            continue
        score_col = f"{metric}_score"
        score_df[score_col] = minmax_score(score_df[metric], row["direction"])

    score_cols = [col for col in score_df.columns if col.endswith("_score")]
    score_df["employment_qol_proxy_score"] = score_df[score_cols].mean(axis=1)
    score_df.to_csv(tables_dir / "10_employment_qol_proxy_panel.csv", index=False, encoding="utf-8-sig")

    metro_summary = (
        score_df.groupby(["year", "metro_area"], as_index=False)
        .agg(employment_qol_proxy_score=("employment_qol_proxy_score", "mean"))
    )
    metro_summary.to_csv(tables_dir / "10_employment_qol_proxy_metro_year.csv", index=False, encoding="utf-8-sig")

    overall_metro = (
        score_df.groupby("metro_area", as_index=False)
        .agg(employment_qol_proxy_score=("employment_qol_proxy_score", "mean"))
    )
    overall_metro.to_csv(tables_dir / "10_employment_qol_proxy_metro_summary.csv", index=False, encoding="utf-8-sig")

    latest_year = int(score_df["year"].max())
    latest = score_df[score_df["year"] == latest_year].copy()
    ranking = latest.sort_values("employment_qol_proxy_score", ascending=False)[
        ["year", "region", "metro_area", "employment_qol_proxy_score"]
    ]
    ranking.to_csv(tables_dir / "10_employment_qol_proxy_region_ranking_2026.csv", index=False, encoding="utf-8-sig")

    component_records = []
    for row in METRIC_ASSUMPTIONS:
        metric = row["metric"]
        if metric not in panel.columns:
            continue
        means = panel.groupby("metro_area")[metric].mean()
        component_records.append(
            {
                "metric": metric,
                "label": row["label"],
                "dimension": row["dimension"],
                "direction": row["direction"],
                "metro_mean": means.get("수도권", np.nan),
                "nonmetro_mean": means.get("비수도권", np.nan),
                "gap_metro_minus_nonmetro": means.get("수도권", np.nan) - means.get("비수도권", np.nan),
                "caution": row["caution"],
            }
        )
    component_gap = pd.DataFrame(component_records)
    component_gap.to_csv(tables_dir / "10_employment_qol_proxy_component_gap.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(8, 5))
    sns.lineplot(data=metro_summary, x="year", y="employment_qol_proxy_score", hue="metro_area", marker="o")
    plt.title("고용 기반 삶의 질 proxy 점수 추이")
    plt.xlabel("연도")
    plt.ylabel("proxy 점수(0~100)")
    plt.legend(title="권역")
    save_plot(figures_dir / "10_employment_qol_proxy_score_trend_metro.png")

    latest_rank = ranking.sort_values("employment_qol_proxy_score", ascending=True)
    colors = latest_rank["metro_area"].map({"수도권": "#2F6F73", "비수도권": "#D08C60"})
    plt.figure(figsize=(9, 7))
    plt.barh(latest_rank["region"], latest_rank["employment_qol_proxy_score"], color=colors)
    plt.title(f"시도별 고용 기반 삶의 질 proxy 점수 ({latest_year}, 부분자료)")
    plt.xlabel("proxy 점수(0~100)")
    plt.ylabel("시도")
    save_plot(figures_dir / "10_employment_qol_proxy_region_ranking_2026.png")

    gap_plot = component_gap.sort_values("gap_metro_minus_nonmetro")
    plt.figure(figsize=(9, 6))
    plt.barh(gap_plot["label"], gap_plot["gap_metro_minus_nonmetro"], color="#2F6F73")
    plt.axvline(0, color="#444444", linewidth=1)
    plt.title("수도권-비수도권 고용 proxy 구성 변수 격차")
    plt.xlabel("수도권 평균 - 비수도권 평균")
    plt.ylabel("변수")
    save_plot(figures_dir / "10_employment_qol_proxy_component_gap.png")

    heat_cols = [f"{metric}_score" for metric in available]
    heat_labels = {f"{row['metric']}_score": row["label"] for row in METRIC_ASSUMPTIONS}
    heat_df = latest.set_index("region")[heat_cols].rename(columns=heat_labels)
    plt.figure(figsize=(11, 7))
    sns.heatmap(heat_df, annot=True, fmt=".1f", cmap="YlGnBu", linewidths=0.4, cbar_kws={"label": "score"})
    plt.title(f"고용 기반 삶의 질 proxy 구성 점수 heatmap ({latest_year}, 부분자료)")
    plt.xlabel("구성 변수")
    plt.ylabel("시도")
    save_plot(figures_dir / "10_employment_qol_proxy_heatmap_2026.png")

    metro_score = overall_metro.set_index("metro_area")["employment_qol_proxy_score"]
    metro_score_gap = metro_score.get("수도권", np.nan) - metro_score.get("비수도권", np.nan)
    top_regions = ranking.head(5)
    bottom_regions = ranking.tail(5).sort_values("employment_qol_proxy_score")

    md = [
        "# 고용 키워드 기반 삶의 질 proxy 비교",
        "",
        "## 1. 분석 전제",
        "현재 데이터에는 실제 삶의 만족도 값이 없다. 따라서 이 문서는 실제 삶의 질을 직접 측정하지 않고, 현재 보유한 고용 키워드로 `고용 여건 관점의 삶의 질 proxy`를 비교한다.",
        "",
        "이 proxy는 탐색용이다. 변수 방향과 가중치를 공개하고, 결과를 삶의 만족도 자체로 해석하지 않는다.",
        "",
        "## 2. 사용한 변수와 방향",
        "",
        "| 변수 | 방향 | 해석 주의 |",
        "|---|---|---|",
    ]
    for row in METRIC_ASSUMPTIONS:
        if row["metric"] not in available:
            continue
        direction = "높을수록 유리" if row["direction"] == "higher_is_better" else "낮을수록 유리"
        md.append(f"| {row['label']} | {direction} | {row['caution']} |")
    md.extend(
        [
            "",
            "## 3. 수도권 vs 비수도권 결과",
            "",
            f"- 수도권 평균 proxy 점수: {metro_score.get('수도권', np.nan):.2f}",
            f"- 비수도권 평균 proxy 점수: {metro_score.get('비수도권', np.nan):.2f}",
            f"- 격차(수도권 - 비수도권): {metro_score_gap:.2f}",
            "",
        ]
    )
    if pd.notna(metro_score_gap):
        if metro_score_gap > 3:
            md.append("현재 고용 구조 proxy 기준으로는 수도권이 비수도권보다 유리하게 관찰된다.")
        elif metro_score_gap < -3:
            md.append("현재 고용 구조 proxy 기준으로는 비수도권이 수도권보다 유리하게 관찰된다.")
        else:
            md.append("현재 고용 구조 proxy 기준으로는 수도권과 비수도권 차이가 크지 않게 관찰된다.")
    md.extend(
        [
            "",
            "## 4. 구성 변수별 관찰",
            "",
            "| 변수 | 수도권 | 비수도권 | 수도권-비수도권 | 해석 |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for _, row in component_gap.iterrows():
        gap = row["gap_metro_minus_nonmetro"]
        if row["direction"] == "higher_is_better":
            interpretation = "수도권 유리" if gap > 0 else "비수도권 유리" if gap < 0 else "차이 작음"
        else:
            interpretation = "수도권 유리" if gap < 0 else "비수도권 유리" if gap > 0 else "차이 작음"
        md.append(f"| {row['label']} | {row['metro_mean']:.2f} | {row['nonmetro_mean']:.2f} | {gap:.2f} | {interpretation} |")
    md.extend(
        [
            "",
            "## 5. 2026년 시도별 proxy 순위",
            "",
            "2026년은 부분자료이므로 확정 순위가 아니라 구조 점검으로만 본다.",
            "",
            "상위 지역:",
        ]
    )
    for _, row in top_regions.iterrows():
        md.append(f"- {row['region']}({row['metro_area']}): {row['employment_qol_proxy_score']:.2f}")
    md.append("")
    md.append("하위 지역:")
    for _, row in bottom_regions.iterrows():
        md.append(f"- {row['region']}({row['metro_area']}): {row['employment_qol_proxy_score']:.2f}")
    md.extend(
        [
            "",
            "## 6. 결론",
            "현재 보유한 고용 키워드만 놓고 보면, 수도권은 청년층 취업자 비중과 임금근로자 비중에서 유리하고, 비수도권은 고령층 취업자 비중·자영업자 비율·단시간 취업자 비중이 높게 관찰된다.",
            "",
            "다만 이 결과는 실제 삶의 만족도 비교가 아니다. 삶의 만족도 원자료가 들어와야 `고용 여건이 삶의 만족도 격차와 관련되는지`를 검증할 수 있다.",
        ]
    )
    output_md.write_text("\n".join(md), encoding="utf-8")
    print(output_md)
    print(overall_metro.to_string(index=False))


if __name__ == "__main__":
    main()
