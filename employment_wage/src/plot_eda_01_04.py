#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from eda_utils import set_korean_font


KEY_FEATURES = [
    "female_employed_share",
    "male_female_employed_share_gap",
    "youth_employed_share",
    "senior_employed_share",
    "wage_worker_share",
    "temporary_worker_share",
    "daily_worker_share",
    "short_hours_worker_share",
    "long_hours_worker_share",
]

FEATURE_LABELS = {
    "female_employed_share": "여성 취업자 비중",
    "male_female_employed_share_gap": "남녀 구성비 격차",
    "youth_employed_share": "청년층 취업자 비중",
    "senior_employed_share": "고령층 취업자 비중",
    "wage_worker_share": "임금근로자 비중",
    "temporary_worker_share": "임시근로자 비중",
    "daily_worker_share": "일용근로자 비중",
    "short_hours_worker_share": "단시간 취업자 비중",
    "long_hours_worker_share": "장시간 취업자 비중",
}

REGION_ORDER = [
    "서울",
    "부산",
    "대구",
    "인천",
    "광주",
    "대전",
    "울산",
    "세종",
    "경기",
    "강원",
    "충북",
    "충남",
    "전북",
    "전남",
    "경북",
    "경남",
    "제주",
]


def resolve_repo_root() -> Path:
    current = Path.cwd().resolve()
    for path in [current, *current.parents]:
        if (path / "data").exists() and (path / "employment_wage").exists():
            return path
    raise FileNotFoundError("저장소 루트를 찾을 수 없습니다.")


def save_figure(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def plot_year_region_coverage(panel: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    coverage = panel.groupby(["year", "metro_area"], as_index=False)["region"].nunique()
    plt.figure(figsize=(8, 5))
    sns.barplot(data=coverage, x="year", y="region", hue="metro_area", palette=["#2F6F73", "#D08C60"])
    plt.axhline(17, color="#444444", linestyle="--", linewidth=1, label="17개 시도 기준")
    plt.title("연도별 지역 coverage")
    plt.xlabel("연도")
    plt.ylabel("시도 수")
    plt.legend(title="권역", loc="upper right")
    path = output_dir / "eda_01_year_region_coverage.png"
    save_figure(path)
    return {
        "figure": str(path),
        "title": "연도별 지역 coverage",
        "message": "2025년과 2026년 모두 17개 시도가 포함되는지 확인한다.",
    }


def plot_partial_2026(tables_dir: Path, output_dir: Path) -> dict[str, str]:
    partial = pd.read_csv(tables_dir / "01_partial_2026_diagnostics.csv")
    plot_df = partial.copy()
    plot_df["short_name"] = plot_df["file_key"].str.replace("employment_", "", regex=False)
    plot_df = plot_df.sort_values("expected_full_year_period_count", ascending=False)

    plt.figure(figsize=(10, 5))
    x = range(len(plot_df))
    plt.bar(x, plot_df["expected_full_year_period_count"], color="#D7DCE2", label="완전 연간 기준")
    plt.bar(x, plot_df["period_count_2026"], color="#2F6F73", label="2026 확보 기간")
    plt.xticks(x, plot_df["short_name"], rotation=25, ha="right")
    plt.title("2026년 부분자료 진단")
    plt.xlabel("파일")
    plt.ylabel("기간 수")
    plt.legend()
    path = output_dir / "eda_02_partial_2026_periods.png"
    save_figure(path)
    return {
        "figure": str(path),
        "title": "2026년 부분자료 진단",
        "message": "2026년이 전체 12개월 또는 4분기 기준에 못 미치는지 보여준다.",
    }


def plot_metro_structure(panel: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    selected = [
        "female_employed_share",
        "male_female_employed_share_gap",
        "youth_employed_share",
        "senior_employed_share",
        "wage_worker_share",
        "short_hours_worker_share",
        "long_hours_worker_share",
    ]
    metro = panel.groupby("metro_area", as_index=False)[selected].mean()
    long_df = metro.melt(id_vars="metro_area", value_vars=selected, var_name="feature", value_name="value")
    long_df["feature_label"] = long_df["feature"].map(FEATURE_LABELS)

    plt.figure(figsize=(12, 6))
    sns.barplot(data=long_df, x="feature_label", y="value", hue="metro_area", palette=["#D08C60", "#2F6F73"])
    plt.title("수도권/비수도권 고용 구조 평균 비교")
    plt.xlabel("고용 구조 변수")
    plt.ylabel("비율 또는 격차(%)")
    plt.xticks(rotation=25, ha="right")
    plt.legend(title="권역")
    path = output_dir / "eda_03_metro_employment_structure.png"
    save_figure(path)
    return {
        "figure": str(path),
        "title": "수도권/비수도권 고용 구조 평균 비교",
        "message": "취업자 수 원자료 대신 구성비 변수 중심으로 권역 차이를 비교한다.",
    }


def plot_youth_senior_scatter(panel: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    latest_year = int(panel["year"].max())
    latest = panel[panel["year"] == latest_year].copy()
    plt.figure(figsize=(9, 6))
    ax = sns.scatterplot(
        data=latest,
        x="youth_employed_share",
        y="senior_employed_share",
        hue="metro_area",
        s=90,
        palette=["#D08C60", "#2F6F73"],
    )
    for _, row in latest.iterrows():
        ax.text(row["youth_employed_share"] + 0.05, row["senior_employed_share"] + 0.05, row["region"], fontsize=8)
    plt.title(f"청년층-고령층 취업자 비중 분포 ({latest_year}, 부분자료)")
    plt.xlabel("청년층 취업자 비중(%)")
    plt.ylabel("고령층 취업자 비중(%)")
    plt.legend(title="권역")
    path = output_dir / "eda_04_youth_senior_scatter_2026.png"
    save_figure(path)
    return {
        "figure": str(path),
        "title": "청년층-고령층 취업자 비중 분포",
        "message": "지역별 연령 고용 구조 차이를 산점도로 확인한다. 2026년은 부분자료다.",
    }


def plot_region_heatmap(panel: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    latest_year = int(panel["year"].max())
    selected = [
        "female_employed_share",
        "youth_employed_share",
        "senior_employed_share",
        "wage_worker_share",
        "temporary_worker_share",
        "short_hours_worker_share",
        "long_hours_worker_share",
    ]
    latest = panel[panel["year"] == latest_year].copy()
    latest["region"] = pd.Categorical(latest["region"], categories=REGION_ORDER, ordered=True)
    heatmap_df = latest.sort_values("region").set_index("region")[selected]
    heatmap_df = heatmap_df.rename(columns=FEATURE_LABELS)

    plt.figure(figsize=(11, 8))
    sns.heatmap(heatmap_df, annot=True, fmt=".1f", cmap="YlGnBu", linewidths=0.4, cbar_kws={"label": "%"})
    plt.title(f"시도별 고용 구조 heatmap ({latest_year}, 부분자료)")
    plt.xlabel("고용 구조 변수")
    plt.ylabel("시도")
    path = output_dir / "eda_05_region_employment_heatmap_2026.png"
    save_figure(path)
    return {
        "figure": str(path),
        "title": "시도별 고용 구조 heatmap",
        "message": "지역별 고용 구조 변수의 상대적 크기를 한눈에 확인한다. 2026년은 부분자료다.",
    }


def plot_gender_gap_by_region(panel: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    latest_year = int(panel["year"].max())
    latest = panel[panel["year"] == latest_year].sort_values("male_female_employed_share_gap", ascending=False)
    colors = latest["metro_area"].map({"수도권": "#2F6F73", "비수도권": "#D08C60"})

    plt.figure(figsize=(10, 6))
    plt.bar(latest["region"], latest["male_female_employed_share_gap"], color=colors)
    plt.title(f"시도별 남녀 취업자 구성비 격차 ({latest_year}, 부분자료)")
    plt.xlabel("시도")
    plt.ylabel("남성-여성 취업자 구성비 격차(%p)")
    plt.xticks(rotation=35, ha="right")
    path = output_dir / "eda_06_gender_gap_by_region_2026.png"
    save_figure(path)
    return {
        "figure": str(path),
        "title": "시도별 남녀 취업자 구성비 격차",
        "message": "고용률 격차가 아니라 취업자 구성비 격차임에 유의한다. 2026년은 부분자료다.",
    }


def plot_feature_trends(panel: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    selected = ["youth_employed_share", "senior_employed_share", "wage_worker_share", "short_hours_worker_share"]
    trend = panel.groupby(["year", "metro_area"], as_index=False)[selected].mean()
    long_df = trend.melt(id_vars=["year", "metro_area"], value_vars=selected, var_name="feature", value_name="value")
    long_df["feature_label"] = long_df["feature"].map(FEATURE_LABELS)

    grid = sns.relplot(
        data=long_df,
        x="year",
        y="value",
        hue="metro_area",
        col="feature_label",
        kind="line",
        marker="o",
        col_wrap=2,
        height=3.2,
        aspect=1.35,
        palette=["#D08C60", "#2F6F73"],
        facet_kws={"sharey": False},
    )
    grid.set_axis_labels("연도", "비율(%)")
    grid.set_titles("{col_name}")
    grid.fig.suptitle("주요 고용 구조 변수 추이", y=1.03)
    path = output_dir / "eda_07_key_feature_trends.png"
    grid.fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(grid.fig)
    return {
        "figure": str(path),
        "title": "주요 고용 구조 변수 추이",
        "message": "2025년과 2026년 일부자료의 권역별 평균 변화를 확인한다.",
    }


def main() -> None:
    repo_root = resolve_repo_root()
    panel_path = repo_root / "data" / "processed" / "kosis_life_quality_employment_panel.csv"
    tables_dir = repo_root / "employment_wage" / "outputs" / "tables"
    output_dir = repo_root / "employment_wage" / "outputs" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid")
    set_korean_font()
    panel = pd.read_csv(panel_path)

    figure_records = [
        plot_year_region_coverage(panel, output_dir),
        plot_partial_2026(tables_dir, output_dir),
        plot_metro_structure(panel, output_dir),
        plot_youth_senior_scatter(panel, output_dir),
        plot_region_heatmap(panel, output_dir),
        plot_gender_gap_by_region(panel, output_dir),
        plot_feature_trends(panel, output_dir),
    ]
    index = pd.DataFrame(figure_records)
    index.to_csv(tables_dir / "05_visualization_index.csv", index=False, encoding="utf-8-sig")
    print(index.to_string(index=False))


if __name__ == "__main__":
    main()
