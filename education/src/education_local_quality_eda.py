#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "education" / "data"
VIZ_DIR = ROOT / "education" / "viz"

LONG_CSV = DATA_DIR / "education_quality_environment_2016_2024_long.csv"
FEATURE_CSV = DATA_DIR / "education_quality_environment_2016_2024.csv"
LATEST_SUMMARY_CSV = DATA_DIR / "education_quality_environment_top15_2024.csv"

BASE_URL = "https://kosis.kr/visual/eRegionIndex"
YEARS = list(range(2016, 2025))
LATEST_YEAR = max(YEARS)


@dataclass(frozen=True)
class Indicator:
    metric_id: str
    metric_name: str
    unity_srvc_id: str
    std_id: str
    category: str
    direction: str = "higher"
    transform: str = "linear"
    clsf_group_cd: str = ""
    clsf_cd: str = ""


INDICATORS = [
    Indicator(
        "private_academies_per_1000",
        "인구 천명당 사설학원수",
        "1284",
        "376",
        "사교육 및 교육시설 접근성",
    ),
    Indicator(
        "elementary_students",
        "초등학교 학생수",
        "1281",
        "372",
        "지역 교육 수요 및 규모 안정성",
        transform="log",
    ),
    Indicator(
        "elementary_schools",
        "초등학교수",
        "1286",
        "380",
        "학교 인프라",
        transform="log",
    ),
    Indicator(
        "elementary_teachers",
        "초등학교 교원수",
        "1279",
        "371",
        "학교 인프라",
        transform="log",
    ),
    Indicator(
        "kindergartens",
        "유치원수",
        "1283",
        "375",
        "학교 인프라",
        transform="log",
    ),
    Indicator(
        "teacher_per_student",
        "교원 1인당 학생수",
        "1273",
        "362",
        "학교 인프라",
        direction="lower",
    ),
    Indicator(
        "class_size_total",
        "학급당 학생수",
        "1282",
        "374",
        "학교 인프라",
        direction="lower",
        clsf_group_cd="A000000058",
        clsf_cd="00",
    ),
    Indicator(
        "population",
        "주민등록인구",
        "816",
        "230",
        "지역 교육 수요 및 규모 안정성",
        transform="log",
        clsf_group_cd="A000000001",
        clsf_cd="00",
    ),
    Indicator(
        "fiscal_self_reliance",
        "재정자립도",
        "955",
        "381",
        "지역 교육 수요 및 규모 안정성",
    ),
]

REQUIRED_METRICS = [indicator.metric_id for indicator in INDICATORS]


def set_korean_font() -> None:
    installed = {font.name for font in fm.fontManager.ttflist}
    for name in ["Malgun Gothic", "AppleGothic", "NanumGothic", "DejaVu Sans"]:
        if name in installed:
            matplotlib.rcParams["font.family"] = name
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


def post_json(path: str, data: dict[str, str]) -> dict:
    response = requests.post(
        f"{BASE_URL}/{path}",
        data=data,
        headers={"X-Requested-With": "XMLHttpRequest"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_indicator_year(indicator: Indicator, year: int) -> pd.DataFrame:
    frames = []
    for level in ["2", "1"]:
        payload = {
            "unitySrvcId": indicator.unity_srvc_id,
            "stdIdctId": indicator.std_id,
            "clsfGroupCd": indicator.clsf_group_cd,
            "clsfCd": indicator.clsf_cd,
            "cyclSe": "Y",
            "year": str(year),
            "clsfLevel": level,
            "regionCd": "",
        }
        data = post_json("selectYearToRegionData.do", payload)
        rows = data.get("resultList", [])
        if rows:
            frame = pd.DataFrame(rows)
            if level == "1":
                additions = []
                sejong = frame[frame["regionCd"].astype(str) == "29"].copy()
                if not sejong.empty:
                    sejong["regionCd"] = "29000"
                    sejong["regionUpNm"] = "세종"
                    sejong["regionNm"] = "세종시"
                    additions.append(sejong)

                if indicator.metric_id == "fiscal_self_reliance":
                    jeju = frame[frame["regionCd"].astype(str) == "39"].copy()
                    if not jeju.empty:
                        jeju_city = jeju.copy()
                        jeju_city["regionCd"] = "39010"
                        jeju_city["regionUpNm"] = "제주"
                        jeju_city["regionNm"] = "제주시"
                        seogwipo = jeju.copy()
                        seogwipo["regionCd"] = "39020"
                        seogwipo["regionUpNm"] = "제주"
                        seogwipo["regionNm"] = "서귀포시"
                        additions.extend([jeju_city, seogwipo])

                frame = pd.concat(additions, ignore_index=True) if additions else frame.iloc[0:0]
            frames.append(frame)

    if not frames:
        return pd.DataFrame()

    frame = pd.concat(frames, ignore_index=True)
    if indicator.clsf_cd and "otherCd" in frame:
        frame = frame[frame["otherCd"].fillna("") == indicator.clsf_cd].copy()
    if frame.empty:
        return pd.DataFrame()

    result = pd.DataFrame(
        {
            "region_cd": frame["regionCd"].astype(str),
            "province": frame["regionUpNm"],
            "district": frame["regionNm"],
            "region": (frame["regionUpNm"] + " " + frame["regionNm"]).str.strip(),
            "year": pd.to_numeric(frame["wrtPnttm"], errors="coerce").astype("Int64"),
            "metric_id": indicator.metric_id,
            "metric_name": indicator.metric_name,
            "category": indicator.category,
            "direction": indicator.direction,
            "value": pd.to_numeric(frame["vl"], errors="coerce"),
        }
    )
    result = result[result["region_cd"].str.len() == 5]
    return result.dropna(subset=["value", "year"])


def fetch_panel_data() -> pd.DataFrame:
    frames = []
    for indicator in INDICATORS:
        for year in YEARS:
            frame = fetch_indicator_year(indicator, year)
            if not frame.empty:
                frames.append(frame)
    if not frames:
        raise ValueError("No KOSIS e-지방지표 data returned")
    return pd.concat(frames, ignore_index=True)


def winsorized_minmax(
    series: pd.Series,
    *,
    lower_is_better: bool = False,
    log_transform: bool = False,
    lower_q: float = 0.01,
    upper_q: float = 0.99,
) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if log_transform:
        values = np.log1p(values.clip(lower=0))

    lo = values.quantile(lower_q)
    hi = values.quantile(upper_q)
    values = values.clip(lo, hi)

    min_value = values.min()
    max_value = values.max()
    if pd.isna(min_value) or pd.isna(max_value) or min_value == max_value:
        score = pd.Series(50.0, index=series.index)
    else:
        score = (values - min_value) / (max_value - min_value) * 100

    return 100 - score if lower_is_better else score


def add_metric_scores(features: pd.DataFrame) -> pd.DataFrame:
    features = features.copy()
    for indicator in INDICATORS:
        score_col = f"{indicator.metric_id}_score"
        features[score_col] = features.groupby("year")[indicator.metric_id].transform(
            lambda item: winsorized_minmax(
                item,
                lower_is_better=indicator.direction == "lower",
                log_transform=indicator.transform == "log",
            )
        )
    return features


def build_features(long_df: pd.DataFrame) -> pd.DataFrame:
    features = (
        long_df.pivot_table(
            index=["region_cd", "province", "district", "region", "year"],
            columns="metric_id",
            values="value",
            aggfunc="first",
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )

    features = features.dropna(subset=REQUIRED_METRICS).copy()
    features = add_metric_scores(features)

    features["stability_score"] = (
        features["elementary_students_score"] * 0.50
        + features["population_score"] * 0.30
        + features["elementary_schools_score"] * 0.20
    )

    features["private_education_access_score"] = (
        features["private_academies_per_1000_score"] * 0.75
        + features["fiscal_self_reliance_score"] * 0.15
        + features["elementary_students_score"] * 0.10
    )

    features["school_infra_score"] = (
        features["elementary_teachers_score"] * 0.25
        + features["elementary_schools_score"] * 0.20
        + features["kindergartens_score"] * 0.15
        + features["class_size_total_score"] * 0.20
        + features["teacher_per_student_score"] * 0.20
    )

    features["education_demand_score"] = (
        features["fiscal_self_reliance_score"] * 0.55
        + features["elementary_students_score"] * 0.20
        + features["population_score"] * 0.15
        + features["elementary_schools_score"] * 0.10
    )

    features["academic_admissions_proxy_score"] = (
        features["private_education_access_score"] * 0.50
        + features["fiscal_self_reliance_score"] * 0.35
        + features["education_demand_score"] * 0.15
    )

    features["education_quality_score"] = (
        features["academic_admissions_proxy_score"] * 0.30
        + features["private_education_access_score"] * 0.30
        + features["school_infra_score"] * 0.20
        + features["education_demand_score"] * 0.15
        + features["stability_score"] * 0.05
    )

    return features.sort_values(["year", "education_quality_score"], ascending=[True, False])


def latest_features(features: pd.DataFrame) -> pd.DataFrame:
    latest = features[features["year"] == LATEST_YEAR].copy()
    if latest.empty:
        latest_year = int(features["year"].max())
        latest = features[features["year"] == latest_year].copy()
    return latest


def save_top15_summary(features: pd.DataFrame) -> pd.DataFrame:
    latest = latest_features(features)
    cols = [
        "region",
        "province",
        "district",
        "education_quality_score",
        "academic_admissions_proxy_score",
        "school_infra_score",
        "private_education_access_score",
        "education_demand_score",
        "stability_score",
        "private_academies_per_1000",
        "elementary_students",
        "elementary_schools",
        "teacher_per_student",
        "class_size_total",
        "population",
        "fiscal_self_reliance",
    ]
    summary = latest[cols].sort_values("education_quality_score", ascending=False).head(15)
    summary.to_csv(LATEST_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    return summary


def save_top15_plot(features: pd.DataFrame) -> None:
    latest = latest_features(features)
    plot_df = latest.nlargest(15, "education_quality_score").sort_values(
        "education_quality_score"
    )

    plt.figure(figsize=(11, 8))
    sns.barplot(
        data=plot_df,
        x="education_quality_score",
        y="region",
        color="#2F6F73",
    )
    plt.title(f"전국 시군구 교육의 질·교육환경 종합점수 TOP 15({LATEST_YEAR})")
    plt.xlabel("교육의 질·교육환경 종합점수(0~100)")
    plt.ylabel("시군구")
    plt.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    plt.savefig(VIZ_DIR / f"education_quality_environment_top15_{LATEST_YEAR}.png", dpi=180)
    plt.close()


def save_component_heatmap(features: pd.DataFrame) -> None:
    latest = latest_features(features)
    selected = latest.nlargest(15, "education_quality_score").sort_values(
        "education_quality_score", ascending=False
    )
    cols = [
        "academic_admissions_proxy_score",
        "private_education_access_score",
        "school_infra_score",
        "education_demand_score",
        "stability_score",
    ]
    label_map = {
        "academic_admissions_proxy_score": "학업·진학 대체",
        "private_education_access_score": "사교육 접근성",
        "school_infra_score": "학교 인프라",
        "education_demand_score": "교육 수요",
        "stability_score": "안정성",
    }
    heatmap_df = selected.set_index("region")[cols].rename(columns=label_map)

    plt.figure(figsize=(9, 8))
    sns.heatmap(heatmap_df, annot=True, fmt=".1f", cmap="YlGnBu", vmin=0, vmax=100)
    plt.title(f"교육환경 TOP 15 세부 점수({LATEST_YEAR})")
    plt.xlabel("평가 영역")
    plt.ylabel("시군구")
    plt.tight_layout()
    plt.savefig(VIZ_DIR / f"education_quality_environment_components_{LATEST_YEAR}.png", dpi=180)
    plt.close()


def save_trend_plot(features: pd.DataFrame) -> None:
    latest = latest_features(features)
    top_regions = latest.nlargest(10, "education_quality_score")["region"].tolist()
    trend = features[features["region"].isin(top_regions)].copy()

    plt.figure(figsize=(12, 7))
    sns.lineplot(
        data=trend,
        x="year",
        y="education_quality_score",
        hue="region",
        marker="o",
    )
    plt.title("교육의 질·교육환경 상위권 지역 2016~2024 추세")
    plt.xlabel("연도")
    plt.ylabel("종합점수(0~100)")
    plt.grid(alpha=0.25)
    plt.legend(title="시군구", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(VIZ_DIR / "education_quality_environment_trend_2016_2024.png", dpi=180)
    plt.close()


def save_correlation_heatmap(features: pd.DataFrame) -> None:
    latest = latest_features(features)
    cols = [
        "education_quality_score",
        "private_academies_per_1000",
        "fiscal_self_reliance",
        "elementary_students",
        "elementary_schools",
        "teacher_per_student",
        "class_size_total",
        "population",
    ]
    label_map = {
        "education_quality_score": "종합점수",
        "private_academies_per_1000": "사설학원 밀도",
        "fiscal_self_reliance": "재정자립도",
        "elementary_students": "초등학생수",
        "elementary_schools": "초등학교수",
        "teacher_per_student": "교원 1인당 학생수",
        "class_size_total": "학급당 학생수",
        "population": "주민등록인구",
    }
    corr = latest[cols].corr().rename(index=label_map, columns=label_map)

    plt.figure(figsize=(9, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", vmin=-1, vmax=1, square=True)
    plt.title(f"교육환경 종합점수와 주요 지표 상관관계({LATEST_YEAR})")
    plt.tight_layout()
    plt.savefig(VIZ_DIR / f"education_quality_environment_correlation_{LATEST_YEAR}.png", dpi=180)
    plt.close()


def main() -> None:
    set_korean_font()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    VIZ_DIR.mkdir(parents=True, exist_ok=True)

    long_df = fetch_panel_data()
    features = build_features(long_df)

    long_df.to_csv(LONG_CSV, index=False, encoding="utf-8-sig")
    features.to_csv(FEATURE_CSV, index=False, encoding="utf-8-sig")

    summary = save_top15_summary(features)
    save_top15_plot(features)
    save_component_heatmap(features)
    save_trend_plot(features)
    save_correlation_heatmap(features)

    print(f"Saved long data: {LONG_CSV}")
    print(f"Saved feature data: {FEATURE_CSV}")
    print(f"Saved top15 summary: {LATEST_SUMMARY_CSV}")
    print(f"Saved visualizations: {VIZ_DIR}")
    print(summary.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
