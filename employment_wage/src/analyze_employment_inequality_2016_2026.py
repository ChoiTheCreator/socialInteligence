#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data_raw" / "employment_wage"
OUTPUT_DIR = ROOT / "employment_wage" / "outputs"
REPORT_DIR = ROOT / "employment_wage" / "report"
TABLE_DIR = OUTPUT_DIR / "tables"
FIGURE_DIR = OUTPUT_DIR / "figures"

REGION_MAP = {
    "서울특별시": "서울",
    "부산광역시": "부산",
    "대구광역시": "대구",
    "인천광역시": "인천",
    "광주광역시": "광주",
    "대전광역시": "대전",
    "울산광역시": "울산",
    "세종특별자치시": "세종",
    "경기도": "경기",
    "강원도": "강원",
    "충청북도": "충북",
    "충청남도": "충남",
    "전라북도": "전북",
    "전북특별자치도": "전북",
    "전라남도": "전남",
    "경상북도": "경북",
    "경상남도": "경남",
    "제주도": "제주",
    "제주특별자치도": "제주",
}
METRO_REGIONS = {"서울", "경기", "인천"}

ECON_ITEM_MAP = {
    "15세이상인구 (천명)": "population_15plus",
    "경제활동인구 (천명)": "labor_force",
    "비경제활동인구 (천명)": "not_in_labor_force",
    "경제활동참가율 (%)": "labor_force_participation_rate",
    "실업률 (%)": "unemployment_rate",
    "고용률 (%)": "employment_rate",
    "15~64세 고용률 (%)": "employment_rate_15_64",
}

POLICY_LABELS = {
    "labor_market_access_score": "기초 고용 접근성",
    "female_employment_score": "여성 고용 참여",
    "stable_wage_job_score": "안정적 임금일자리",
    "youth_retention_score": "청년 정착 일자리",
    "working_time_quality_score": "근로시간 안정성",
    "education_job_score": "고학력·지역산업 일자리 기반",
}

DATASET_LABELS = {
    "employment_econ_activity_sex.csv": "성별 경제활동인구 총괄",
    "employment_region_age.csv": "연령별 취업자",
    "employment_region_sex_age.csv": "성·연령별 취업자",
    "employment_status.csv": "종사상지위별 취업자",
    "employment_hours.csv": "취업시간별 취업자",
    "employment_education.csv": "교육정도별 취업자",
}

DATASET_ROLES = {
    "employment_econ_activity_sex.csv": {
        "main_columns": "고용률, 15~64세 고용률, 실업률, 경제활동참가율, 여성 고용률, 성별 고용률 격차",
        "analysis_role": "지역 노동시장의 핵심 성과와 포용성 판단",
        "life_quality_link": "일할 기회, 소득 가능성, 경제활동 참여 기반은 지역 삶의 질의 기본 조건이다.",
    },
    "employment_region_age.csv": {
        "main_columns": "청년층 취업자 비중, 고령층 취업자 비중",
        "analysis_role": "청년 정착 가능성과 지역 노동시장 고령화 확인",
        "life_quality_link": "청년이 일자리를 찾고 머물 수 있는 지역일수록 장기적 생활 기반이 안정적이다.",
    },
    "employment_region_sex_age.csv": {
        "main_columns": "성별·연령별 취업자 구조",
        "analysis_role": "성별과 연령을 동시에 고려한 보조 진단",
        "life_quality_link": "특정 성·연령 집단에 일자리 기회가 쏠리거나 배제되는지 확인한다.",
    },
    "employment_status.csv": {
        "main_columns": "임금근로자, 상용근로자, 임시근로자, 일용근로자, 자영업자 비중",
        "analysis_role": "고용 안정성과 일자리 질 판단",
        "life_quality_link": "상용·임금 일자리는 소득 안정, 사회보험, 미래 계획 가능성과 연결된다.",
    },
    "employment_hours.csv": {
        "main_columns": "단시간 취업자 비중, 장시간 취업자 비중, 평균 취업시간",
        "analysis_role": "근로시간 안정성과 불완전취업 가능성 판단",
        "life_quality_link": "과소·과잉 근로는 소득 안정성과 일-생활 균형을 모두 흔들 수 있다.",
    },
    "employment_education.csv": {
        "main_columns": "대졸이상 취업자 비중",
        "analysis_role": "고학력 인력이 일할 수 있는 지역 산업·직무 기반 판단",
        "life_quality_link": "지역 안에 전문직무와 성장 가능한 커리어가 있어야 청년·고학력 인력이 정착한다.",
    },
}


def ensure_dirs() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for path in [
        FIGURE_DIR / "eda",
        FIGURE_DIR / "trends",
        FIGURE_DIR / "policy",
        FIGURE_DIR / "regional",
        TABLE_DIR / "eda",
        TABLE_DIR / "panels",
        TABLE_DIR / "results",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def cleanup_flat_outputs() -> None:
    """Remove old flat generated outputs after moving to categorized folders."""
    old_report = OUTPUT_DIR / "employment_inequality_policy_report.md"
    if old_report.exists():
        old_report.unlink()
    for path in FIGURE_DIR.glob("*.png"):
        path.unlink()
    for path in TABLE_DIR.glob("*.csv"):
        path.unlink()


def figure_category(name: str) -> str:
    if name.startswith("00_") or name.startswith("01_") or name.startswith("02_"):
        return "eda"
    if name.startswith(("03_", "04_", "05_", "06_", "16_")):
        return "trends"
    if name.startswith(("09_", "10_", "11_")):
        return "policy"
    return "regional"


def table_category(name: str) -> str:
    if name in {"raw_eda_diagnosis.csv", "raw_dataset_roles.csv", "analysis_framework.csv"}:
        return "eda"
    if name.startswith("employment_panel_"):
        return "panels"
    return "results"


def fig_ref(name: str) -> str:
    return f"../outputs/figures/{figure_category(name)}/{name}"


def set_korean_font() -> None:
    installed = {f.name for f in fm.fontManager.ttflist}
    for name in ["AppleGothic", "Malgun Gothic", "NanumGothic", "DejaVu Sans"]:
        if name in installed:
            matplotlib.rcParams["font.family"] = name
            break
    matplotlib.rcParams["axes.unicode_minus"] = False
    sns.set_theme(style="whitegrid", font=matplotlib.rcParams["font.family"])


def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    for enc in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("csv", b"", 0, 1, f"Could not decode {path}")


def read_raw_for_diagnosis(path: Path) -> pd.DataFrame:
    return read_csv(path, header=None, dtype=str)


def quarter_columns(columns: list[object]) -> list[str]:
    return [str(c) for c in columns if re.fullmatch(r"\d{4}\.[1-4]/4", str(c))]


def parse_period(period: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{4})\.([1-4])/4", str(period))
    if not match:
        raise ValueError(f"Unexpected quarter label: {period}")
    return int(match.group(1)), int(match.group(2))


def normalize_region(value: object) -> str:
    value = str(value).strip()
    return REGION_MAP.get(value, value)


def add_region_fields(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["region"] = out["region"].map(normalize_region)
    out["metro_area"] = np.where(out["region"].isin(METRO_REGIONS), "수도권", "비수도권")
    return out


def to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False).str.strip(), errors="coerce")


def diagnose_raw_files() -> pd.DataFrame:
    rows = []
    for path in sorted(RAW_DIR.glob("employment_*.csv")):
        raw = read_raw_for_diagnosis(path)
        if path.name == "employment_econ_activity_sex.csv":
            period_labels = [str(v).strip() for v in raw.iloc[0, 2:].tolist()]
            item_labels = [str(v).strip() for v in raw.iloc[1, 2:].tolist()]
            data = raw.iloc[2:].copy()
            region_values = data.iloc[:, 0].dropna().astype(str).str.strip()
            item_values = sorted({x for x in item_labels if x and x != "nan"})
        else:
            header = [str(v).strip() for v in raw.iloc[0].tolist()]
            period_labels = header
            data = raw.iloc[1:].copy()
            region_values = data.iloc[:, 0].dropna().astype(str).str.strip()
            item_values = sorted(data.iloc[:, 1].dropna().astype(str).str.strip().unique()) if raw.shape[1] > 1 else []

        periods = [p for p in period_labels if re.fullmatch(r"\d{4}\.[1-4]/4", str(p))]
        parsed_periods = [parse_period(p) for p in periods]
        years = sorted({year for year, _ in parsed_periods})
        quarters = sorted(set(periods), key=lambda p: parse_period(p))
        regions = [normalize_region(v) for v in region_values if v != "계" and v != "시도별"]
        region_count = len(set(regions))
        missing_count = int(data.replace(r"^\s*$", np.nan, regex=True).isna().sum().sum())
        total_cells = int(data.shape[0] * data.shape[1])
        rows.append(
            {
                "file": path.name,
                "dataset": DATASET_LABELS.get(path.name, path.stem),
                "rows": int(data.shape[0]),
                "columns": int(raw.shape[1]),
                "missing_cells": missing_count,
                "missing_rate_pct": missing_count / total_cells * 100 if total_cells else np.nan,
                "duplicate_rows": int(data.duplicated().sum()),
                "period_start": quarters[0] if quarters else "",
                "period_end": quarters[-1] if quarters else "",
                "quarter_count": len(quarters),
                "value_period_columns": len(periods),
                "years_present": ", ".join(map(str, years)),
                "region_count_excluding_total": region_count,
                "item_count": len(item_values),
                "sample_items": ", ".join(item_values[:8]),
            }
        )
    return pd.DataFrame(rows)


def build_dataset_role_table(raw_diagnosis: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for file in raw_diagnosis["file"]:
        meta = DATASET_ROLES[file]
        rows.append(
            {
                "file": file,
                "dataset": DATASET_LABELS[file],
                "main_columns": meta["main_columns"],
                "analysis_role": meta["analysis_role"],
                "life_quality_link": meta["life_quality_link"],
            }
        )
    return pd.DataFrame(rows)


def build_analysis_framework() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "dimension": "기초 고용 접근성",
                "features": "고용률, 15~64세 고용률, 경제활동참가율, 실업률",
                "direction": "고용률·참가율은 높을수록, 실업률은 낮을수록 좋음",
                "life_quality_assumption": "지역 주민이 일할 기회와 소득 기반에 접근할 수 있어야 삶의 질이 안정된다.",
                "policy_interpretation": "구직 매칭, 직업훈련, 이동·주거 지원, 지역 일자리 흡수력 강화",
            },
            {
                "dimension": "여성 고용 참여",
                "features": "여성 고용률, 여성 경제활동참가율, 남녀 고용률 격차",
                "direction": "여성 고용률·참가율은 높을수록, 성별 격차는 낮을수록 좋음",
                "life_quality_assumption": "여성의 노동시장 참여는 가구소득, 돌봄 부담 완화, 지역 포용성과 연결된다.",
                "policy_interpretation": "돌봄 인프라, 경력단절 복귀, 유연근무, 여성 일자리 질 관리",
            },
            {
                "dimension": "안정적 임금일자리",
                "features": "임금근로자 비중, 상용근로자 비중, 임시·일용근로자 비중, 자영업자 비중",
                "direction": "상용·임금근로는 높을수록, 임시·일용·자영업 의존은 낮을수록 안정적이라고 봄",
                "life_quality_assumption": "안정적 임금일자리는 소득 예측 가능성, 사회보험, 주거·가계 계획 가능성과 연결된다.",
                "policy_interpretation": "상용직 채용 인센티브, 사회보험 조건부 지원, 중소기업 임금·복지 격차 완화",
            },
            {
                "dimension": "청년 정착 일자리",
                "features": "청년층 취업자 비중, 고령층 취업자 비중",
                "direction": "청년층 비중은 높을수록, 고령층 과다 의존은 낮을수록 청년 정착 여건이 좋다고 봄",
                "life_quality_assumption": "청년이 지역에서 첫 직장과 경력 경로를 찾을 수 있어야 지역의 장기 활력이 유지된다.",
                "policy_interpretation": "지역 대학-기업 연결, 청년 주거·생활 지원, 신산업·공공서비스 일자리",
            },
            {
                "dimension": "근로시간 안정성",
                "features": "단시간 취업자 비중, 장시간 취업자 비중",
                "direction": "단시간·장시간 비중은 낮을수록 안정적이라고 봄",
                "life_quality_assumption": "비자발적 단시간은 소득 불안, 장시간은 일-생활 균형 저하와 연결될 수 있다.",
                "policy_interpretation": "비자발적 단시간 근로 완화, 시간제 사회보험 사각지대 축소, 근로시간 선택권",
            },
            {
                "dimension": "고학력·지역산업 일자리 기반",
                "features": "대졸이상 취업자 비중",
                "direction": "높을수록 지역 안에 전문직무와 성장 가능한 일자리 기반이 있다고 봄",
                "life_quality_assumption": "고학력 인력이 지역에 남을 수 있는 산업·직무가 있어야 청년 유출과 지역 격차를 줄일 수 있다.",
                "policy_interpretation": "전문직무 창출, 지역 전략산업, R&D·디지털 전환, 지역 중견기업 성장",
            },
        ]
    )


def read_simple_quarterly(path: Path, region_col: str, item_col: str) -> pd.DataFrame:
    df = read_csv(path)
    q_cols = quarter_columns(list(df.columns))
    long = df.melt(
        id_vars=[region_col, item_col],
        value_vars=q_cols,
        var_name="period",
        value_name="value",
    )
    long = long.rename(columns={region_col: "region", item_col: "item"})
    long["value"] = to_number(long["value"])
    long[["year", "quarter"]] = long["period"].apply(lambda x: pd.Series(parse_period(x)))
    long["item"] = long["item"].astype(str).str.strip()
    long = add_region_fields(long)
    return long


def read_econ_activity(path: Path) -> pd.DataFrame:
    raw = read_csv(path, header=None)
    period_row = raw.iloc[0]
    item_row = raw.iloc[1]
    data = raw.iloc[2:].copy()

    records: list[pd.DataFrame] = []
    for col in range(2, raw.shape[1]):
        period = str(period_row[col]).strip()
        if not re.fullmatch(r"\d{4}\.[1-4]/4", period):
            continue
        item = str(item_row[col]).strip()
        part = pd.DataFrame(
            {
                "region": data.iloc[:, 0].astype(str).str.strip(),
                "sex": data.iloc[:, 1].astype(str).str.strip(),
                "period": period,
                "item": item,
                "value": to_number(data.iloc[:, col]),
            }
        )
        records.append(part)

    out = pd.concat(records, ignore_index=True)
    out[["year", "quarter"]] = out["period"].apply(lambda x: pd.Series(parse_period(x)))
    out = add_region_fields(out)
    return out


def pivot_item(long: pd.DataFrame, value_prefix: str | None = None) -> pd.DataFrame:
    cols = ["region", "metro_area", "year", "quarter", "period"]
    out = long.pivot_table(index=cols, columns="item", values="value", aggfunc="mean").reset_index()
    out.columns.name = None
    if value_prefix:
        renamed = {
            col: f"{value_prefix}_{col}"
            for col in out.columns
            if col not in cols
        }
        out = out.rename(columns=renamed)
    return out


def build_econ_features() -> pd.DataFrame:
    econ = read_econ_activity(RAW_DIR / "employment_econ_activity_sex.csv")
    econ = econ[econ["region"] != "계"].copy()
    econ["metric"] = econ["item"].map(ECON_ITEM_MAP)
    econ = econ.dropna(subset=["metric"])

    idx = ["region", "metro_area", "year", "quarter", "period"]
    total = (
        econ[econ["sex"] == "계"]
        .pivot_table(index=idx, columns="metric", values="value", aggfunc="mean")
        .reset_index()
    )
    total.columns.name = None

    sex_parts = []
    for sex, prefix in [("남자", "male"), ("여자", "female")]:
        part = (
            econ[econ["sex"] == sex]
            .pivot_table(index=idx, columns="metric", values="value", aggfunc="mean")
            .reset_index()
        )
        part.columns.name = None
        part = part.rename(
            columns={
                "labor_force_participation_rate": f"{prefix}_labor_force_participation_rate",
                "unemployment_rate": f"{prefix}_unemployment_rate",
                "employment_rate": f"{prefix}_employment_rate",
                "employment_rate_15_64": f"{prefix}_employment_rate_15_64",
            }
        )
        keep = idx + [
            f"{prefix}_labor_force_participation_rate",
            f"{prefix}_unemployment_rate",
            f"{prefix}_employment_rate",
            f"{prefix}_employment_rate_15_64",
        ]
        sex_parts.append(part[keep])

    out = total
    for part in sex_parts:
        out = out.merge(part, on=idx, how="left")
    out["gender_employment_rate_gap"] = out["male_employment_rate"] - out["female_employment_rate"]
    out["gender_labor_force_participation_gap"] = (
        out["male_labor_force_participation_rate"] - out["female_labor_force_participation_rate"]
    )
    return out


def ratio_from_items(
    long: pd.DataFrame,
    numerator_items: list[str],
    denominator_item: str = "계",
    feature_name: str = "feature",
) -> pd.DataFrame:
    idx = ["region", "metro_area", "year", "quarter", "period"]
    denominator = long[long["item"] == denominator_item][idx + ["value"]].rename(columns={"value": "denominator"})
    numerator = (
        long[long["item"].isin(numerator_items)]
        .groupby(idx, as_index=False)["value"]
        .sum()
        .rename(columns={"value": "numerator"})
    )
    out = denominator.merge(numerator, on=idx, how="left")
    out[feature_name] = np.where(out["denominator"] > 0, out["numerator"] / out["denominator"] * 100, np.nan)
    return out[idx + [feature_name]]


def build_age_features() -> pd.DataFrame:
    long = read_simple_quarterly(RAW_DIR / "employment_region_age.csv", "시도별(1)", "연령계층별(1)")
    long = long[long["region"] != "계"].copy()
    features = [
        ratio_from_items(long, ["15 - 29세"], feature_name="youth_employed_share"),
        ratio_from_items(long, ["60세이상"], feature_name="senior_employed_share"),
        ratio_from_items(long, ["30 - 39세", "40 - 49세"], feature_name="core_30_49_employed_share"),
        ratio_from_items(long, ["15 - 64세"], feature_name="working_age_employed_share"),
    ]
    out = features[0]
    for part in features[1:]:
        out = out.merge(part, on=["region", "metro_area", "year", "quarter", "period"], how="left")
    return out


def build_status_features() -> pd.DataFrame:
    long = read_simple_quarterly(RAW_DIR / "employment_status.csv", "시도별", "종사상지위별")
    long = long[long["region"] != "계"].copy()
    features = [
        ratio_from_items(long, ["임금근로자"], feature_name="wage_worker_share"),
        ratio_from_items(long, ["-상용근로자"], feature_name="regular_worker_share"),
        ratio_from_items(long, ["-임시근로자"], feature_name="temporary_worker_share"),
        ratio_from_items(long, ["-일용근로자"], feature_name="daily_worker_share"),
        ratio_from_items(long, ["*자영업자"], feature_name="self_employed_share"),
    ]
    out = features[0]
    for part in features[1:]:
        out = out.merge(part, on=["region", "metro_area", "year", "quarter", "period"], how="left")
    return out


def build_hours_features() -> pd.DataFrame:
    long = read_simple_quarterly(RAW_DIR / "employment_hours.csv", "시도별", "취업시간별")
    long = long[long["region"] != "계"].copy()
    wide = pivot_item(long)
    idx = ["region", "metro_area", "year", "quarter", "period"]
    total = wide["계"]

    def optional_sum(cols: list[str]) -> pd.Series:
        available = [col for col in cols if col in wide.columns]
        if not available:
            return pd.Series(np.nan, index=wide.index)
        return wide[available].sum(axis=1, min_count=1)

    short_total = wide["*36시간미만"] if "*36시간미만" in wide.columns else optional_sum([" 1-17시간", " 18-35시간"])
    short_total = short_total.fillna(optional_sum(["1~14시간", "15~35시간"]))
    long_total = wide[" 54시간 이상"] if " 54시간 이상" in wide.columns else pd.Series(np.nan, index=wide.index)
    long_total = long_total.fillna(wide["53시간이상"] if "53시간이상" in wide.columns else np.nan)

    out = wide[idx].copy()
    out["short_hours_worker_share"] = np.where(total > 0, short_total / total * 100, np.nan)
    out["long_hours_worker_share"] = np.where(total > 0, long_total / total * 100, np.nan)
    if "주당평균취업시간 (시간)" in wide.columns:
        out["average_weekly_hours"] = wide["주당평균취업시간 (시간)"]
    return out


def build_education_features() -> pd.DataFrame:
    long = read_simple_quarterly(RAW_DIR / "employment_education.csv", "시도별", "교육정도별")
    long = long[long["region"] != "계"].copy()
    return ratio_from_items(long, ["대졸이상"], feature_name="college_employed_share")


def build_quarterly_panel() -> pd.DataFrame:
    parts = [
        build_econ_features(),
        build_age_features(),
        build_status_features(),
        build_hours_features(),
        build_education_features(),
    ]
    keys = ["region", "metro_area", "year", "quarter", "period"]
    panel = parts[0]
    for part in parts[1:]:
        panel = panel.merge(part, on=keys, how="left")
    return panel.sort_values(["year", "quarter", "region"]).reset_index(drop=True)


def build_annual_panel(quarterly: pd.DataFrame) -> pd.DataFrame:
    keys = ["region", "metro_area", "year"]
    numeric_cols = [c for c in quarterly.select_dtypes(include=[np.number]).columns if c not in {"year", "quarter"}]
    annual = quarterly.groupby(keys, as_index=False)[numeric_cols].mean()
    q_counts = quarterly.groupby(keys, as_index=False)["quarter"].nunique().rename(columns={"quarter": "quarter_count"})
    annual = annual.merge(q_counts, on=keys, how="left")
    annual["is_complete_year"] = annual["quarter_count"] == 4
    return annual.sort_values(["year", "region"]).reset_index(drop=True)


def normalize_metric(df: pd.DataFrame, col: str, higher_is_better: bool) -> pd.Series:
    s = df[col].astype(float)
    lo = s.min(skipna=True)
    hi = s.max(skipna=True)
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(50.0, index=df.index)
    score = (s - lo) / (hi - lo) * 100
    if not higher_is_better:
        score = 100 - score
    return score


def add_scores(annual: pd.DataFrame) -> pd.DataFrame:
    out = annual.copy()
    complete = out[(out["year"] >= 2016) & (out["year"] <= 2025) & out["is_complete_year"]].copy()
    directions = {
        "employment_rate": True,
        "employment_rate_15_64": True,
        "labor_force_participation_rate": True,
        "unemployment_rate": False,
        "female_employment_rate": True,
        "female_labor_force_participation_rate": True,
        "gender_employment_rate_gap": False,
        "wage_worker_share": True,
        "regular_worker_share": True,
        "temporary_worker_share": False,
        "daily_worker_share": False,
        "self_employed_share": False,
        "youth_employed_share": True,
        "senior_employed_share": False,
        "short_hours_worker_share": False,
        "long_hours_worker_share": False,
        "college_employed_share": True,
    }

    for col, high in directions.items():
        lo = complete[col].min(skipna=True)
        hi = complete[col].max(skipna=True)
        if pd.isna(lo) or pd.isna(hi) or hi == lo:
            out[f"{col}_score"] = 50.0
            continue
        score = (out[col] - lo) / (hi - lo) * 100
        out[f"{col}_score"] = score if high else 100 - score

    def mean_score(cols: list[str]) -> pd.Series:
        return out[[f"{c}_score" for c in cols]].mean(axis=1)

    out["labor_market_access_score"] = mean_score(
        ["employment_rate", "employment_rate_15_64", "labor_force_participation_rate", "unemployment_rate"]
    )
    out["female_employment_score"] = mean_score(
        ["female_employment_rate", "female_labor_force_participation_rate", "gender_employment_rate_gap"]
    )
    out["stable_wage_job_score"] = mean_score(
        ["wage_worker_share", "regular_worker_share", "temporary_worker_share", "daily_worker_share", "self_employed_share"]
    )
    out["youth_retention_score"] = mean_score(["youth_employed_share", "senior_employed_share"])
    out["working_time_quality_score"] = mean_score(["short_hours_worker_share", "long_hours_worker_share"])
    out["education_job_score"] = mean_score(["college_employed_share"])
    out["employment_inclusion_score"] = out[
        [
            "labor_market_access_score",
            "female_employment_score",
            "stable_wage_job_score",
            "youth_retention_score",
            "working_time_quality_score",
            "education_job_score",
        ]
    ].mean(axis=1)
    return out


def calculate_summaries(scored: pd.DataFrame) -> dict[str, pd.DataFrame]:
    complete = scored[(scored["year"] >= 2016) & (scored["year"] <= 2025) & scored["is_complete_year"]].copy()
    latest_year = int(complete["year"].max())
    latest = complete[complete["year"] == latest_year].copy()

    metric_cols = [
        "employment_rate",
        "employment_rate_15_64",
        "labor_force_participation_rate",
        "unemployment_rate",
        "female_employment_rate",
        "gender_employment_rate_gap",
        "wage_worker_share",
        "regular_worker_share",
        "self_employed_share",
        "temporary_worker_share",
        "daily_worker_share",
        "short_hours_worker_share",
        "long_hours_worker_share",
        "youth_employed_share",
        "senior_employed_share",
        "college_employed_share",
        "employment_inclusion_score",
    ]
    metro_gap = (
        complete.groupby(["year", "metro_area"])[metric_cols]
        .mean()
        .reset_index()
        .pivot(index="year", columns="metro_area", values=metric_cols)
    )
    metro_gap.columns = [f"{metric}_{area}" for metric, area in metro_gap.columns]
    for metric in metric_cols:
        if f"{metric}_수도권" in metro_gap and f"{metric}_비수도권" in metro_gap:
            metro_gap[f"{metric}_gap_metro_minus_nonmetro"] = (
                metro_gap[f"{metric}_수도권"] - metro_gap[f"{metric}_비수도권"]
            )
    metro_gap = metro_gap.reset_index()

    component_gap = []
    for metric in metric_cols:
        row = {"metric": metric}
        for area in ["수도권", "비수도권"]:
            row[area] = latest.loc[latest["metro_area"] == area, metric].mean()
        row["gap_metro_minus_nonmetro"] = row.get("수도권", np.nan) - row.get("비수도권", np.nan)
        component_gap.append(row)
    component_gap = pd.DataFrame(component_gap)

    lever_cols = list(POLICY_LABELS.keys())
    priority_rows = []
    for lever in lever_cols:
        yearly_rows = []
        for year, part in complete.groupby("year"):
            low = part.nsmallest(5, "employment_inclusion_score")[lever].mean()
            high = part.nlargest(5, "employment_inclusion_score")[lever].mean()
            yearly_rows.append({"year": year, "top_bottom_gap": high - low})
        yearly = pd.DataFrame(yearly_rows)
        latest_gap = yearly.loc[yearly["year"] == latest_year, "top_bottom_gap"].iloc[0]
        persistent_gap = yearly["top_bottom_gap"].mean()
        corr = complete[[lever, "employment_inclusion_score"]].corr().iloc[0, 1]
        priority_index = ((latest_gap + persistent_gap) / 2) * max(corr, 0)
        priority_rows.append(
            {
                "policy_lever": lever,
                "policy_label": POLICY_LABELS[lever],
                "latest_year": latest_year,
                "latest_top_bottom_gap": latest_gap,
                "persistent_top_bottom_gap": persistent_gap,
                "corr_with_total_score": corr,
                "priority_index": priority_index,
            }
        )
    priority = pd.DataFrame(priority_rows).sort_values("priority_index", ascending=False).reset_index(drop=True)

    inequality_trend = []
    for year, part in complete.groupby("year"):
        row = {"year": year}
        for metric in [
            "employment_rate_15_64",
            "female_employment_rate",
            "gender_employment_rate_gap",
            "stable_wage_job_score",
            "working_time_quality_score",
            "employment_inclusion_score",
        ]:
            row[f"{metric}_std"] = part[metric].std()
            row[f"{metric}_range"] = part[metric].max() - part[metric].min()
        inequality_trend.append(row)
    inequality_trend = pd.DataFrame(inequality_trend)

    region_recommendations = latest[
        ["region", "metro_area", "employment_inclusion_score", *lever_cols]
    ].copy()
    for lever in lever_cols:
        region_recommendations[f"{lever}_need"] = 100 - region_recommendations[lever]
    need_cols = [f"{lever}_need" for lever in lever_cols]
    region_recommendations["top_policy_need"] = region_recommendations[need_cols].idxmax(axis=1).str.replace("_need", "", regex=False)
    region_recommendations["top_policy_label"] = region_recommendations["top_policy_need"].map(POLICY_LABELS)
    region_recommendations = region_recommendations.sort_values("employment_inclusion_score")

    return {
        "complete": complete,
        "latest": latest,
        "metro_gap": metro_gap,
        "component_gap": component_gap,
        "priority": priority,
        "inequality_trend": inequality_trend,
        "region_recommendations": region_recommendations,
    }


def save_table(df: pd.DataFrame, name: str) -> None:
    out_dir = TABLE_DIR / table_category(name)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / name, index=False, encoding="utf-8-sig")


def save_fig(name: str) -> None:
    plt.tight_layout()
    out_dir = FIGURE_DIR / figure_category(name)
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / name, dpi=180)
    plt.close()


def plot_line_by_metro(df: pd.DataFrame, y: str, title: str, ylabel: str, filename: str) -> None:
    plot_df = df.groupby(["year", "metro_area"], as_index=False)[y].mean()
    plt.figure(figsize=(10, 5.5))
    sns.lineplot(data=plot_df, x="year", y=y, hue="metro_area", marker="o", linewidth=2.4)
    plt.title(title)
    plt.xlabel("연도")
    plt.ylabel(ylabel)
    plt.legend(title="")
    save_fig(filename)


def make_eda_plots(raw_diagnosis: pd.DataFrame, framework: pd.DataFrame) -> None:
    plt.figure(figsize=(11, 5.2))
    plot_df = raw_diagnosis.sort_values("missing_rate_pct", ascending=False)
    sns.barplot(data=plot_df, x="missing_rate_pct", y="dataset", color="#2F6F73")
    plt.title("원본 데이터별 결측률")
    plt.xlabel("결측률(%)")
    plt.ylabel("")
    save_fig("00_eda_raw_missing_rate.png")

    coverage = raw_diagnosis[["dataset", "quarter_count"]].sort_values("quarter_count")
    plt.figure(figsize=(11, 5.2))
    sns.barplot(data=coverage, x="quarter_count", y="dataset", color="#2F6F73")
    plt.axvline(40, color="#555555", linestyle="--", linewidth=1, label="2016~2025 완전연도 기준 40개 분기")
    plt.title("원본 데이터별 분기 컬럼 수")
    plt.xlabel("고유 분기 수")
    plt.ylabel("")
    plt.legend()
    save_fig("00_eda_raw_period_coverage.png")

    regions = raw_diagnosis[["dataset", "region_count_excluding_total"]].sort_values("region_count_excluding_total")
    plt.figure(figsize=(11, 5.2))
    sns.barplot(data=regions, x="region_count_excluding_total", y="dataset", color="#2F6F73")
    plt.axvline(17, color="#555555", linestyle="--", linewidth=1, label="17개 시도")
    plt.title("원본 데이터별 지역 coverage")
    plt.xlabel("전국 합계 제외 지역 수")
    plt.ylabel("")
    plt.legend()
    save_fig("00_eda_raw_region_coverage.png")

    fw = framework.copy()
    fw["feature_count"] = fw["features"].str.count(",") + 1
    plt.figure(figsize=(11, 5.6))
    sns.barplot(data=fw, x="feature_count", y="dimension", color="#C7822D")
    plt.title("자체 분석 기준별 사용 feature 수")
    plt.xlabel("feature 수")
    plt.ylabel("")
    save_fig("00_framework_feature_count.png")


def make_plots(scored: pd.DataFrame, summaries: dict[str, pd.DataFrame]) -> None:
    complete = summaries["complete"]
    latest = summaries["latest"]
    latest_year = int(latest["year"].max())
    priority = summaries["priority"]

    coverage = (
        scored.groupby(["year", "is_complete_year"], as_index=False)["quarter_count"]
        .max()
        .rename(columns={"quarter_count": "분기 수"})
    )
    plt.figure(figsize=(10, 4.8))
    sns.barplot(data=coverage, x="year", y="분기 수", hue="is_complete_year", palette=["#C85C5C", "#2F6F73"])
    plt.axhline(4, color="#555555", linestyle="--", linewidth=1)
    plt.title("연도별 분기 coverage")
    plt.xlabel("연도")
    plt.ylabel("포함 분기 수")
    plt.legend(title="완전 연도")
    save_fig("01_data_coverage_quarters.png")

    feature_cols = [
        "employment_rate",
        "employment_rate_15_64",
        "labor_force_participation_rate",
        "unemployment_rate",
        "female_employment_rate",
        "wage_worker_share",
        "short_hours_worker_share",
        "college_employed_share",
    ]
    missing = complete.groupby("year")[feature_cols].apply(lambda x: x.notna().mean() * 100).reset_index()
    heat = missing.set_index("year").T
    plt.figure(figsize=(11, 4.8))
    sns.heatmap(heat, vmin=0, vmax=100, cmap="YlGnBu", annot=True, fmt=".0f", cbar_kws={"label": "비결측률(%)"})
    plt.title("주요 feature 연도별 비결측률")
    plt.xlabel("연도")
    plt.ylabel("feature")
    save_fig("02_feature_coverage_heatmap.png")

    plot_line_by_metro(
        complete,
        "employment_rate_15_64",
        "15~64세 고용률: 수도권 vs 비수도권",
        "15~64세 고용률(%)",
        "03_employment_15_64_trend_metro.png",
    )
    plot_line_by_metro(
        complete,
        "labor_force_participation_rate",
        "경제활동참가율: 수도권 vs 비수도권",
        "경제활동참가율(%)",
        "04_labor_force_participation_trend_metro.png",
    )
    plot_line_by_metro(
        complete,
        "unemployment_rate",
        "실업률: 수도권 vs 비수도권",
        "실업률(%)",
        "05_unemployment_trend_metro.png",
    )
    plot_line_by_metro(
        complete,
        "gender_employment_rate_gap",
        "남녀 고용률 격차: 수도권 vs 비수도권",
        "남자-여자 고용률 격차(%p)",
        "06_gender_employment_gap_trend_metro.png",
    )

    ranking = latest.sort_values("employment_rate_15_64", ascending=False)
    plt.figure(figsize=(10, 7.5))
    sns.barplot(data=ranking, x="employment_rate_15_64", y="region", hue="metro_area", dodge=False, palette=["#2F6F73", "#C7822D"])
    plt.title(f"{latest_year}년 시도별 15~64세 고용률")
    plt.xlabel("15~64세 고용률(%)")
    plt.ylabel("지역")
    plt.legend(title="")
    save_fig("07_region_employment_15_64_ranking_latest.png")

    ranking = latest.sort_values("employment_inclusion_score", ascending=False)
    plt.figure(figsize=(10, 7.5))
    sns.barplot(data=ranking, x="employment_inclusion_score", y="region", hue="metro_area", dodge=False, palette=["#2F6F73", "#C7822D"])
    plt.title(f"{latest_year}년 시도별 고용 포용성 종합점수")
    plt.xlabel("고용 포용성 종합점수(0~100)")
    plt.ylabel("지역")
    plt.legend(title="")
    save_fig("08_region_employment_inclusion_score_latest.png")

    plt.figure(figsize=(9.5, 5.8))
    sns.barplot(data=priority, x="priority_index", y="policy_label", color="#2F6F73")
    plt.title("지역 고용격차 완화 정책 우선순위")
    plt.xlabel("우선순위 지수")
    plt.ylabel("")
    save_fig("09_policy_priority_ranking.png")

    lever_cols = list(POLICY_LABELS.keys())
    lever_gap_rows = []
    for lever in lever_cols:
        metro = latest.loc[latest["metro_area"] == "수도권", lever].mean()
        nonmetro = latest.loc[latest["metro_area"] == "비수도권", lever].mean()
        lever_gap_rows.append({"policy_label": POLICY_LABELS[lever], "gap_metro_minus_nonmetro": metro - nonmetro})
    lever_gap = pd.DataFrame(lever_gap_rows).sort_values("gap_metro_minus_nonmetro")
    plt.figure(figsize=(9.5, 5.8))
    colors = ["#C85C5C" if v < 0 else "#2F6F73" for v in lever_gap["gap_metro_minus_nonmetro"]]
    plt.barh(lever_gap["policy_label"], lever_gap["gap_metro_minus_nonmetro"], color=colors)
    plt.axvline(0, color="#555555", linewidth=1)
    plt.title(f"{latest_year}년 정책 레버 점수 격차: 수도권 - 비수도권")
    plt.xlabel("점수 격차")
    plt.ylabel("")
    save_fig("10_policy_lever_metro_gap_latest.png")

    display_metrics = {
        "employment_rate_15_64": "15~64세 고용률",
        "female_employment_rate": "여성 고용률",
        "gender_employment_rate_gap": "남녀 고용률 격차",
        "wage_worker_share": "임금근로자 비중",
        "regular_worker_share": "상용근로자 비중",
        "self_employed_share": "자영업자 비중",
        "short_hours_worker_share": "단시간 취업자 비중",
        "youth_employed_share": "청년층 취업자 비중",
        "college_employed_share": "대졸이상 취업자 비중",
    }
    rows = []
    for metric, label in display_metrics.items():
        metro = latest.loc[latest["metro_area"] == "수도권", metric].mean()
        nonmetro = latest.loc[latest["metro_area"] == "비수도권", metric].mean()
        rows.append({"label": label, "gap_metro_minus_nonmetro": metro - nonmetro})
    component = pd.DataFrame(rows).sort_values("gap_metro_minus_nonmetro")
    plt.figure(figsize=(9.8, 6.2))
    colors = ["#C85C5C" if v < 0 else "#2F6F73" for v in component["gap_metro_minus_nonmetro"]]
    plt.barh(component["label"], component["gap_metro_minus_nonmetro"], color=colors)
    plt.axvline(0, color="#555555", linewidth=1)
    plt.title(f"{latest_year}년 주요 고용지표 격차: 수도권 - 비수도권")
    plt.xlabel("격차(%p 또는 점수)")
    plt.ylabel("")
    save_fig("11_component_gap_latest.png")

    heat_cols = [
        "employment_rate_15_64_score",
        "female_employment_rate_score",
        "gender_employment_rate_gap_score",
        "stable_wage_job_score",
        "working_time_quality_score",
        "youth_retention_score",
        "employment_inclusion_score",
    ]
    heat_labels = [
        "15~64 고용률",
        "여성 고용률",
        "성별 격차",
        "안정일자리",
        "근로시간",
        "청년정착",
        "종합",
    ]
    heat_df = latest.sort_values("employment_inclusion_score", ascending=False).set_index("region")[heat_cols]
    heat_df.columns = heat_labels
    plt.figure(figsize=(9.8, 8.2))
    sns.heatmap(heat_df, vmin=0, vmax=100, cmap="RdYlGn", annot=True, fmt=".0f", cbar_kws={"label": "점수"})
    plt.title(f"{latest_year}년 지역별 고용 구조 점수 heatmap")
    plt.xlabel("")
    plt.ylabel("지역")
    save_fig("12_region_metric_heatmap_latest.png")

    plt.figure(figsize=(8.5, 6.2))
    sns.scatterplot(
        data=latest,
        x="female_employment_rate",
        y="employment_rate_15_64",
        hue="metro_area",
        size="employment_inclusion_score",
        sizes=(60, 220),
        palette=["#2F6F73", "#C7822D"],
    )
    for _, row in latest.iterrows():
        plt.text(row["female_employment_rate"] + 0.04, row["employment_rate_15_64"], row["region"], fontsize=8)
    plt.title(f"{latest_year}년 여성 고용률과 15~64세 고용률")
    plt.xlabel("여성 고용률(%)")
    plt.ylabel("15~64세 고용률(%)")
    plt.legend(title="")
    save_fig("13_female_employment_vs_total_latest.png")

    plt.figure(figsize=(8.5, 6.2))
    sns.scatterplot(
        data=latest,
        x="regular_worker_share",
        y="employment_inclusion_score",
        hue="metro_area",
        size="wage_worker_share",
        sizes=(60, 220),
        palette=["#2F6F73", "#C7822D"],
    )
    for _, row in latest.iterrows():
        plt.text(row["regular_worker_share"] + 0.04, row["employment_inclusion_score"], row["region"], fontsize=8)
    plt.title(f"{latest_year}년 상용근로자 비중과 고용 포용성")
    plt.xlabel("상용근로자 비중(%)")
    plt.ylabel("고용 포용성 종합점수")
    plt.legend(title="")
    save_fig("14_regular_jobs_vs_score_latest.png")

    plt.figure(figsize=(8.5, 6.2))
    sns.scatterplot(
        data=latest,
        x="youth_employed_share",
        y="senior_employed_share",
        hue="metro_area",
        size="employment_inclusion_score",
        sizes=(60, 220),
        palette=["#2F6F73", "#C7822D"],
    )
    for _, row in latest.iterrows():
        plt.text(row["youth_employed_share"] + 0.03, row["senior_employed_share"], row["region"], fontsize=8)
    plt.title(f"{latest_year}년 청년층·고령층 취업자 비중")
    plt.xlabel("청년층 취업자 비중(%)")
    plt.ylabel("고령층 취업자 비중(%)")
    plt.legend(title="")
    save_fig("15_youth_senior_scatter_latest.png")

    inequality = summaries["inequality_trend"]
    trend = inequality[
        [
            "year",
            "employment_rate_15_64_range",
            "female_employment_rate_range",
            "gender_employment_rate_gap_range",
            "employment_inclusion_score_range",
        ]
    ].melt("year", var_name="metric", value_name="range")
    trend["metric"] = trend["metric"].map(
        {
            "employment_rate_15_64_range": "15~64 고용률",
            "female_employment_rate_range": "여성 고용률",
            "gender_employment_rate_gap_range": "성별 격차",
            "employment_inclusion_score_range": "종합점수",
        }
    )
    plt.figure(figsize=(10, 5.8))
    sns.lineplot(data=trend, x="year", y="range", hue="metric", marker="o", linewidth=2.2)
    plt.title("지역 간 고용지표 격차 추이: 최고-최저 범위")
    plt.xlabel("연도")
    plt.ylabel("최고-최저 격차")
    plt.legend(title="")
    save_fig("16_regional_inequality_trends.png")

    needs = summaries["region_recommendations"].copy()
    need_cols = [f"{lever}_need" for lever in lever_cols]
    need_heat = needs.set_index("region")[need_cols]
    need_heat.columns = [POLICY_LABELS[c.replace("_need", "")] for c in need_cols]
    plt.figure(figsize=(10, 8.2))
    sns.heatmap(need_heat, cmap="YlOrRd", annot=True, fmt=".0f", cbar_kws={"label": "정책 필요도"})
    plt.title(f"{latest_year}년 지역별 정책 필요도 heatmap")
    plt.xlabel("")
    plt.ylabel("지역")
    save_fig("17_region_policy_needs_heatmap_latest.png")


def write_report(
    scored: pd.DataFrame,
    summaries: dict[str, pd.DataFrame],
    raw_diagnosis: pd.DataFrame,
    dataset_roles: pd.DataFrame,
    framework: pd.DataFrame,
) -> None:
    complete = summaries["complete"]
    latest = summaries["latest"]
    priority = summaries["priority"]
    component_gap = summaries["component_gap"]
    recommendations = summaries["region_recommendations"]
    latest_year = int(latest["year"].max())
    years = f"{int(complete['year'].min())}~{int(complete['year'].max())}"
    top_policy = priority.iloc[0]
    second_policy = priority.iloc[1]
    third_policy = priority.iloc[2]

    metro_summary = latest.groupby("metro_area")[
        [
            "employment_rate_15_64",
            "female_employment_rate",
            "gender_employment_rate_gap",
            "wage_worker_share",
            "regular_worker_share",
            "self_employed_share",
            "short_hours_worker_share",
            "employment_inclusion_score",
        ]
    ].mean()

    def fmt(value: float) -> str:
        return f"{value:.1f}"

    priority_table = [
        "| 순위 | 정책 레버 | 2025년 상하위 격차 | 10년 평균 격차 | 종합점수 상관 | 우선순위 지수 |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for i, row in priority.head(5).iterrows():
        priority_table.append(
            f"| {i + 1} | {row['policy_label']} | {row['latest_top_bottom_gap']:.1f} | "
            f"{row['persistent_top_bottom_gap']:.1f} | {row['corr_with_total_score']:.2f} | {row['priority_index']:.1f} |"
        )

    raw_table = [
        "| 원본 데이터 | 행 | 열 | 결측률 | 중복행 | 기간 | 고유 분기 수 | 지역 수 | 항목 수 |",
        "|---|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    for _, row in raw_diagnosis.iterrows():
        raw_table.append(
            f"| {row['dataset']} | {int(row['rows'])} | {int(row['columns'])} | "
            f"{row['missing_rate_pct']:.2f}% | {int(row['duplicate_rows'])} | "
            f"{row['period_start']}~{row['period_end']} | {int(row['quarter_count'])} | "
            f"{int(row['region_count_excluding_total'])} | {int(row['item_count'])} |"
        )

    role_table = [
        "| 원본 데이터 | 주요 변수 | 분석에서의 역할 | 삶의 질과 연결한 근거 |",
        "|---|---|---|---|",
    ]
    for _, row in dataset_roles.iterrows():
        role_table.append(
            f"| {row['dataset']} | {row['main_columns']} | {row['analysis_role']} | {row['life_quality_link']} |"
        )

    framework_table = [
        "| 자체 분석 기준 | 사용 feature | 방향성 | 삶의 질과 연결한 가정 | 정책 해석 |",
        "|---|---|---|---|---|",
    ]
    for _, row in framework.iterrows():
        framework_table.append(
            f"| {row['dimension']} | {row['features']} | {row['direction']} | "
            f"{row['life_quality_assumption']} | {row['policy_interpretation']} |"
        )

    lines = [
        "# 최종 보고서: 2016~2026 KOSIS 고용 데이터 기반 지역 고용격차 분석",
        "",
        "## 1. 분석 목적",
        "",
        "이 보고서는 KOSIS 고용 raw 데이터를 이용해 지역 간 고용 여건 차이를 정석적인 EDA 파이프라인으로 점검하고, 고용 측면에서 지역 간 삶의 질 격차를 줄이는 데 어떤 정책 레버가 가장 우선적인지 도출한다.",
        "",
        "삶의 만족도 원자료를 직접 결합한 인과분석은 아니므로, 결론은 정책 효과의 확정 추정치가 아니라 고용 구조 데이터가 가리키는 우선 개입 방향으로 해석한다.",
        "",
        "## 2. 원본 데이터 EDA",
        "",
        "- 출처: KOSIS 고용 관련 시도별 분기 통계",
        f"- 완전 연도 분석 기간: `{years}`",
        "- 최신 참고값: `2026년 1분기`는 부분연도이므로 정책 결론 산정에서는 제외",
        "- 분석 단위: `year × region`, 17개 시도",
        "",
        "먼저 원본 데이터가 분석 가능한 상태인지 확인했다. EDA에서는 각 raw CSV의 행·열 수, 결측치, 중복행, 기간 coverage, 지역 coverage, 항목 수를 점검했다.",
        "",
        *raw_table,
        "",
        f"![원본 데이터별 결측률]({fig_ref('00_eda_raw_missing_rate.png')})",
        "",
        "결측률을 먼저 확인한 이유는 특정 지표의 결측이 크면 지역 간 차이가 실제 차이가 아니라 데이터 공백에서 나올 수 있기 때문이다. 현재 핵심 raw 데이터는 결측률이 분석을 막을 수준으로 나타나지 않았다.",
        "",
        f"![원본 데이터별 분기 coverage]({fig_ref('00_eda_raw_period_coverage.png')})",
        "",
        "분기 coverage를 확인한 결과 2016.1/4~2026.1/4 자료가 들어왔고, 2016~2025년은 완전 연도 기준 40개 분기로 구성된다. 2026년은 1분기만 있으므로 최종 정책 결론에서는 제외했다.",
        "",
        f"![원본 데이터별 지역 coverage]({fig_ref('00_eda_raw_region_coverage.png')})",
        "",
        "지역 coverage는 전국 합계를 제외한 17개 시도 기준으로 확인했다. 지역 수가 맞아야 수도권/비수도권 비교와 시도별 순위가 왜곡되지 않는다.",
        "",
        "## 3. 원본 데이터별 사용 근거",
        "",
        "이번 분석은 아무 고용지표나 임의로 묶은 것이 아니라, 원본 데이터가 삶의 질 proxy에서 어떤 의미를 갖는지 먼저 정했다. 아래 기준에 따라 각 raw 파일을 분석에 사용했다.",
        "",
        *role_table,
        "",
        "## 4. 내가 세운 고용-삶의 질 proxy 기준",
        "",
        "삶의 만족도 원자료가 아직 없기 때문에, 이번 분석에서는 `고용이 삶의 질에 영향을 줄 수 있는 경로`를 직접 정의했다. 기준은 여섯 가지다. 단순히 고용률이 높은 지역을 좋은 지역으로 보지 않고, 일자리 접근성, 포용성, 안정성, 청년 정착성, 근로시간, 지역 산업 기반을 함께 봤다.",
        "",
        *framework_table,
        "",
        f"![자체 분석 기준별 feature 수]({fig_ref('00_framework_feature_count.png')})",
        "",
        "이 기준을 세운 이유는 지역 간 삶의 질 격차가 단순한 취업자 수 차이가 아니라, 어떤 사람이 어떤 질의 일자리에 접근할 수 있는지에서 발생한다고 보았기 때문이다.",
        "",
        "## 5. 분석 파이프라인",
        "",
        "```text",
        "KOSIS raw CSV",
        "  -> 원본 데이터별 결측치·중복·기간·지역 coverage 진단",
        "  -> 원본 파일 보관 및 안정 파일명 정리",
        "  -> 분기 컬럼 long 변환",
        "  -> 지역명 17개 시도 기준 정규화",
        "  -> 수도권/비수도권 분류",
        "  -> 분기 패널 생성",
        "  -> 완전 연도 기준 연평균 패널 생성",
        "  -> 고용 접근성, 여성 고용, 안정일자리, 청년정착, 근로시간 점수화",
        "  -> 지역별 격차와 정책 우선순위 산정",
        "```",
        "",
        f"![연도별 분기 coverage]({fig_ref('01_data_coverage_quarters.png')})",
        "",
        "위 그래프는 2016~2025년은 4개 분기가 모두 있는 완전 연도이고, 2026년은 1분기만 있는 부분연도임을 보여준다. 따라서 정책 결론은 2016~2025년 완전 연도 기준으로 냈다.",
        "",
        f"![주요 feature coverage]({fig_ref('02_feature_coverage_heatmap.png')})",
        "",
        "주요 고용 feature는 2016~2025년 대부분의 지역·연도에서 결측 없이 구성되어, 장기 EDA와 지역 비교에 사용할 수 있다.",
        "",
        "## 6. 핵심 EDA 결과",
        "",
        f"![15~64세 고용률 추세]({fig_ref('03_employment_15_64_trend_metro.png')})",
        "",
        "15~64세 고용률은 지역 노동시장의 핵심 결과 지표로 사용했다. 수도권과 비수도권 평균 차이뿐 아니라 연도별 변화를 함께 확인했다.",
        "",
        f"![경제활동참가율 추세]({fig_ref('04_labor_force_participation_trend_metro.png')})",
        "",
        "경제활동참가율은 지역 주민이 실제 노동시장에 진입하는 정도를 보여준다. 고용률이 낮은 지역은 단순히 일자리 수만이 아니라 노동시장 참여 기반도 함께 봐야 한다.",
        "",
        f"![실업률 추세]({fig_ref('05_unemployment_trend_metro.png')})",
        "",
        "실업률은 경기 변동과 지역별 일자리 흡수력을 함께 반영한다. 단, 실업률만 보면 비경제활동인구 증가 문제를 놓칠 수 있어 고용률·참가율과 같이 해석했다.",
        "",
        f"![남녀 고용률 격차 추세]({fig_ref('06_gender_employment_gap_trend_metro.png')})",
        "",
        "성별 고용률 격차는 지역의 돌봄, 산업구조, 일자리 유연성 차이를 반영할 수 있다. 이 지표는 지역 간 삶의 질 격차와 연결될 가능성이 큰 포용성 지표로 사용했다.",
        "",
        f"![{latest_year}년 15~64세 고용률 순위]({fig_ref('07_region_employment_15_64_ranking_latest.png')})",
        "",
        f"![{latest_year}년 고용 포용성 종합점수]({fig_ref('08_region_employment_inclusion_score_latest.png')})",
        "",
        f"{latest_year}년 기준 지역별 고용 여건은 단일 지표가 아니라 고용률, 여성 고용, 안정일자리, 근로시간, 청년·고령 구조가 결합된 결과로 차이가 나타난다.",
        "",
        "## 7. 정책 우선순위 결론",
        "",
        f"![정책 우선순위]({fig_ref('09_policy_priority_ranking.png')})",
        "",
        f"데이터 기준 최우선 정책 레버는 **{top_policy['policy_label']}**이다. 이 레버는 고용 포용성 상위 지역과 하위 지역 사이의 격차가 크고, 종합 고용 여건 점수와의 관련성도 높게 나타났다.",
        "",
        f"두 번째 우선순위는 **{second_policy['policy_label']}**, 세 번째 우선순위는 **{third_policy['policy_label']}**이다. 따라서 정책 설계는 1순위 레버만 단독으로 추진하기보다, `{top_policy['policy_label']} + {second_policy['policy_label']} + {third_policy['policy_label']}` 조합으로 설계하는 것이 타당하다.",
        "",
        "여기서 고학력·지역산업 일자리 기반은 교육정책만을 뜻하지 않는다. 원자료상 `대졸이상 취업자 비중`을 사용한 구조지표이며, 지역 안에 대졸 이상 인력이 머물 수 있는 산업, 직무, 임금근로 일자리가 얼마나 있는지를 보는 proxy다.",
        "",
        "정책 우선순위 산정 기준은 다음과 같다.",
        "",
        "- 2025년 기준 고용 포용성 상위 5개 지역과 하위 5개 지역의 레버 점수 격차",
        "- 2016~2025년 동안 반복적으로 유지된 평균 격차",
        "- 해당 레버 점수와 종합 고용 포용성 점수의 상관",
        "",
        *priority_table,
        "",
        "중요한 점은 단순 고용률만으로는 지역 불평등을 충분히 설명하기 어렵다는 것이다. 2025년 평균 15~64세 고용률은 수도권 70.2%, 비수도권 69.5%로 큰 차이가 아니었다. 반면 고용 포용성 종합점수는 수도권 61.9, 비수도권 52.4로 더 크게 벌어진다. 즉 격차의 핵심은 일자리 수보다 지역 안에 어떤 질의 일자리와 커리어 경로가 있는지에 가깝다.",
        "",
        f"![정책 레버 수도권-비수도권 격차]({fig_ref('10_policy_lever_metro_gap_latest.png')})",
        "",
        "이 그래프는 수도권/비수도권 평균 차이 관점에서 어떤 정책 영역의 격차가 큰지 보여준다. 단, 최종 우선순위는 수도권 여부만이 아니라 17개 시도 전체의 상·하위 지역 격차를 함께 고려했다.",
        "",
        f"![주요 고용지표 격차]({fig_ref('11_component_gap_latest.png')})",
        "",
        "주요 지표를 직접 비교하면 어떤 원자료 지표가 정책 결론을 뒷받침하는지 확인할 수 있다.",
        "",
        "## 8. 지역별 구조 진단",
        "",
        f"![{latest_year}년 지역별 고용 구조 heatmap]({fig_ref('12_region_metric_heatmap_latest.png')})",
        "",
        "지역별 heatmap은 각 지역이 어떤 고용 구조에서 취약한지 보여준다. 같은 비수도권 안에서도 취약한 축이 다르기 때문에, 전국 단일 정책보다 지역 맞춤형 패키지가 필요하다.",
        "",
        f"![여성 고용률과 15~64세 고용률]({fig_ref('13_female_employment_vs_total_latest.png')})",
        "",
        "여성 고용률이 낮은 지역은 전체 핵심연령 고용률도 낮게 나타나는 경향이 있다. 이는 여성 고용 참여 확대가 지역 고용격차 완화의 중요한 축이 될 수 있음을 시사한다.",
        "",
        f"![상용근로자 비중과 고용 포용성]({fig_ref('14_regular_jobs_vs_score_latest.png')})",
        "",
        "상용근로자 비중은 안정적 임금일자리 기반을 보여준다. 고용 포용성 점수가 낮은 지역은 안정적 임금일자리 기반을 같이 보강할 필요가 있다.",
        "",
        f"![청년층·고령층 취업자 비중]({fig_ref('15_youth_senior_scatter_latest.png')})",
        "",
        "청년층과 고령층 취업자 비중은 지역의 인구·산업 구조를 반영한다. 청년층 취업자 비중이 낮고 고령층 비중이 높은 지역은 청년 정착형 일자리와 지역 산업 전환 정책이 필요하다.",
        "",
        f"![지역 간 고용격차 추이]({fig_ref('16_regional_inequality_trends.png')})",
        "",
        "지역 간 격차가 일시적인지, 10년 동안 반복되는 구조인지 확인하기 위해 최고-최저 범위의 추이를 확인했다.",
        "",
        f"![{latest_year}년 지역별 정책 필요도]({fig_ref('17_region_policy_needs_heatmap_latest.png')})",
        "",
        "정책 필요도 heatmap은 지역별로 어떤 정책 패키지가 우선인지 보여준다.",
        "",
        "## 9. 데이터 기반 정책 제안",
        "",
        f"### 1순위: {top_policy['policy_label']}",
        "",
        "이 정책은 지역 간 고용 여건 차이를 줄이기 위한 최우선 축이다. 단순히 대학 진학률을 높이는 정책이 아니라, 비수도권 안에 대졸 이상 인력이 실제로 선택할 수 있는 산업과 직무를 만드는 정책이어야 한다.",
        "",
        "구체적으로는 지역 전략산업, 공공서비스, 보건·돌봄, 디지털 전환, 제조 고도화, 연구개발, 지역 중견기업의 전문직무를 늘리고, 지역 대학과 기업의 채용 경로를 제도화하는 방식이 필요하다.",
        "",
        f"### 2순위: {second_policy['policy_label']}",
        "",
        "청년 정착 일자리는 1순위 정책의 효과를 보완하는 역할을 한다. 청년층 취업자 비중이 낮고 고령층 취업자 비중이 높은 지역은 단기 채용 지원만으로는 구조가 바뀌기 어렵다. 지역에서 첫 직장, 경력 성장, 주거, 생활 인프라가 이어지는 패키지가 필요하다.",
        "",
        f"### 3순위: {third_policy['policy_label']}",
        "",
        "안정적 임금일자리는 고학력·청년 일자리 정책이 지역에 남도록 만드는 기반이다. 새 일자리가 단기·불안정 일자리로 만들어지면 지역 정착 효과가 약하므로, 상용직 전환, 사회보험, 임금·복지 격차 완화가 같이 설계되어야 한다.",
        "",
        "### 지역 맞춤형 실행 방향",
        "",
        "- 고용률과 경제활동참가율이 낮은 지역: 직업훈련, 구직 매칭, 이동·주거 지원을 결합한 노동시장 진입 정책",
        "- 여성 고용률과 성별 격차가 취약한 지역: 돌봄 인프라, 경력단절 복귀, 유연근무, 지역 여성 일자리 질 관리",
        "- 안정일자리 점수가 낮은 지역: 상용직 채용 인센티브, 사회보험 가입 조건부 고용지원, 지역 중소기업 임금·복지 격차 완화",
        "- 청년정착 점수가 낮은 지역: 지역 대학-기업 연계, 청년 주거와 일자리 패키지, 신산업·공공서비스 일자리 확대",
        "- 근로시간 안정성이 낮은 지역: 비자발적 단시간 근로 실태조사, 시간제 근로자의 사회보험 사각지대 축소, 근로시간 선택권 강화",
        "",
        "## 10. 최종 결론",
        "",
        f"2016~2025년 KOSIS 고용 데이터를 기준으로 보면, 지역 간 고용격차는 단순한 고용률 차이라기보다 고학력 인력이 일할 수 있는 지역 산업 기반, 청년 정착 가능성, 안정적 임금일자리 구조가 함께 만든 결과다. 이 중 이번 데이터에서 가장 우선순위가 높게 나온 정책 레버는 **{top_policy['policy_label']}**이며, 다음으로 **{second_policy['policy_label']}**, **{third_policy['policy_label']}**이 중요하다.",
        "",
        "따라서 지역 간 삶의 질 격차를 고용 측면에서 줄이려면 전국 공통의 단순 일자리 수 확대보다, 취약 지역의 핵심 병목을 겨냥한 `고학력·청년정착형 안정일자리 패키지`가 가장 타당하다. 특히 지역 대학-기업 연결, 전문직무 창출, 상용직 기반, 청년 주거·생활 지원을 한 번에 묶는 방향이 필요하다.",
        "",
        "## 11. 주요 수치 요약",
        "",
        f"- {latest_year}년 수도권 15~64세 고용률 평균: {fmt(metro_summary.loc['수도권', 'employment_rate_15_64'])}%",
        f"- {latest_year}년 비수도권 15~64세 고용률 평균: {fmt(metro_summary.loc['비수도권', 'employment_rate_15_64'])}%",
        f"- {latest_year}년 수도권 여성 고용률 평균: {fmt(metro_summary.loc['수도권', 'female_employment_rate'])}%",
        f"- {latest_year}년 비수도권 여성 고용률 평균: {fmt(metro_summary.loc['비수도권', 'female_employment_rate'])}%",
        f"- {latest_year}년 수도권 고용 포용성 종합점수 평균: {fmt(metro_summary.loc['수도권', 'employment_inclusion_score'])}",
        f"- {latest_year}년 비수도권 고용 포용성 종합점수 평균: {fmt(metro_summary.loc['비수도권', 'employment_inclusion_score'])}",
        "",
        "## 12. 한계",
        "",
        "- 이 분석은 KOSIS 고용 구조 데이터 기반 분석이며, 삶의 만족도 원자료를 직접 결합하지 않았다.",
        "- 정책 효과를 실제로 추정한 인과분석은 아니므로, 결과는 정책 우선순위 가설로 해석해야 한다.",
        "- 청년층·고령층 취업자 비중은 고용률이 아니라 취업자 구성비이므로 지역 인구구조의 영향을 받는다.",
        "- 2026년은 1분기만 포함되어 최종 정책 결론에서는 제외했다.",
    ]

    report = "\n".join(lines) + "\n"
    (REPORT_DIR / "employment_inequality_policy_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    cleanup_flat_outputs()
    set_korean_font()
    raw_diagnosis = diagnose_raw_files()
    dataset_roles = build_dataset_role_table(raw_diagnosis)
    framework = build_analysis_framework()
    quarterly = build_quarterly_panel()
    annual = build_annual_panel(quarterly)
    scored = add_scores(annual)
    summaries = calculate_summaries(scored)

    save_table(raw_diagnosis, "raw_eda_diagnosis.csv")
    save_table(dataset_roles, "raw_dataset_roles.csv")
    save_table(framework, "analysis_framework.csv")
    save_table(quarterly, "employment_panel_quarterly_2016_2026.csv")
    save_table(annual, "employment_panel_annual_2016_2026.csv")
    save_table(scored, "employment_panel_annual_scored_2016_2026.csv")
    for name, df in summaries.items():
        if name == "complete" or name == "latest":
            continue
        save_table(df, f"{name}.csv")

    make_eda_plots(raw_diagnosis, framework)
    make_plots(scored, summaries)
    write_report(scored, summaries, raw_diagnosis, dataset_roles, framework)
    print(f"Saved tables to {TABLE_DIR}")
    print(f"Saved figures to {FIGURE_DIR}")
    print(f"Saved report to {REPORT_DIR / 'employment_inequality_policy_report.md'}")


if __name__ == "__main__":
    main()
