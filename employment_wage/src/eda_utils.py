from __future__ import annotations

import re
import unicodedata
import warnings
from functools import reduce
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


EXPECTED_YEARS = list(range(2016, 2027))

RAW_FILE_SPECS: dict[str, str] = {
    "life_satisfaction": "life_quality/life_satisfaction.csv",
    "employment_region_sex": "employment_wage/employment_region_sex.csv",
    "employment_region_age": "employment_wage/employment_region_age.csv",
    "employment_status": "employment_wage/employment_status.csv",
    "employment_hours": "employment_wage/employment_hours.csv",
}

OPTIONAL_RAW_FILE_SPECS: dict[str, str] = {
    "employment_region_sex_age": "employment_wage/employment_region_sex_age.csv",
}

COLUMN_CANDIDATES: dict[str, list[str]] = {
    "year": ["시점", "연도", "year", "TIME", "time"],
    "region": ["행정구역별", "행정구역(시도)별", "시도", "시도별", "지역", "region"],
    "sex": ["성별", "성", "sex", "gender"],
    "age_group": ["연령별", "연령계층별", "age_group", "age", "연령"],
    "item": ["항목", "계정항목", "variable", "item", "지표"],
    "value": ["데이터", "값", "value", "DATA_VALUE", "data_value"],
    "employment_status": ["종사상지위별", "종사상 지위별"],
    "employment_hours": ["취업시간별", "취업 시간별"],
}

VALID_REGIONS = [
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

METRO_REGIONS = {"서울", "경기", "인천"}

REGION_NAME_MAP = {
    "서울특별시": "서울",
    "서울": "서울",
    "부산광역시": "부산",
    "부산": "부산",
    "대구광역시": "대구",
    "대구": "대구",
    "인천광역시": "인천",
    "인천": "인천",
    "광주광역시": "광주",
    "광주": "광주",
    "대전광역시": "대전",
    "대전": "대전",
    "울산광역시": "울산",
    "울산": "울산",
    "세종특별자치시": "세종",
    "세종": "세종",
    "경기도": "경기",
    "경기": "경기",
    "강원도": "강원",
    "강원특별자치도": "강원",
    "강원": "강원",
    "충청북도": "충북",
    "충북": "충북",
    "충청남도": "충남",
    "충남": "충남",
    "전라북도": "전북",
    "전북특별자치도": "전북",
    "전북": "전북",
    "전라남도": "전남",
    "전남": "전남",
    "경상북도": "경북",
    "경북": "경북",
    "경상남도": "경남",
    "경남": "경남",
    "제주특별자치도": "제주",
    "제주도": "제주",
    "제주": "제주",
}

MISSING_VALUE_TOKENS = {"", "-", "--", "---", "...", "…", "NA", "N/A", "nan", "NaN", "NULL", "null", "x", "X"}

REQUIRED_EMPLOYMENT_FEATURES = [
    "employment_rate",
    "unemployment_rate",
    "labor_force_participation_rate",
    "youth_employment_rate",
    "youth_unemployment_rate",
    "male_employment_rate",
    "female_employment_rate",
    "gender_employment_gap",
    "temporary_worker_ratio",
    "daily_worker_ratio",
    "self_employed_ratio",
    "short_hours_worker_ratio",
    "long_hours_worker_ratio",
]

RATIO_ALIAS_MAP = {
    "temporary_worker_ratio": "temporary_worker_share",
    "daily_worker_ratio": "daily_worker_share",
    "self_employed_ratio": "self_employed_share",
    "short_hours_worker_ratio": "short_hours_worker_share",
    "long_hours_worker_ratio": "long_hours_worker_share",
}

FIGURE_LABELS = {
    "life_satisfaction": "삶의 만족도",
    "employment_rate": "고용률",
    "unemployment_rate": "실업률",
    "labor_force_participation_rate": "경제활동참가율",
    "youth_employment_rate": "청년층 고용률",
    "youth_unemployment_rate": "청년층 실업률",
    "male_employment_rate": "남성 고용률",
    "female_employment_rate": "여성 고용률",
    "gender_employment_gap": "성별 고용률 격차",
    "temporary_worker_ratio": "임시근로자 비율",
    "daily_worker_ratio": "일용근로자 비율",
    "self_employed_ratio": "자영업자 비율",
    "short_hours_worker_ratio": "단시간 취업자 비율",
    "long_hours_worker_ratio": "장시간 취업자 비율",
}


class ColumnMappingError(ValueError):
    """Raised when required KOSIS columns cannot be mapped safely."""


def setup_environment(repo_root: str | Path | None = None, domain: str = "employment_wage") -> dict[str, Path]:
    """Create shared data folders and domain-specific analysis output folders."""
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    domain_root = root / domain
    dirs = {
        "root": root,
        "domain_root": domain_root,
        "raw": root / "data" / "raw",
        "processed": root / "data" / "processed",
        "domain_processed": root / "data" / "processed" / domain,
        "tables": domain_root / "outputs" / "tables",
        "figures": domain_root / "outputs" / "figures",
        "notebooks": domain_root / "notebooks",
        "src": domain_root / "src",
    }
    for path in dirs.values():
        if path != root:
            path.mkdir(parents=True, exist_ok=True)
    set_korean_font()
    return dirs


def set_korean_font() -> str:
    """Set a Korean font if one is installed; otherwise keep matplotlib's default."""
    installed = {font.name for font in fm.fontManager.ttflist}
    candidates = [
        "AppleGothic",
        "Apple SD Gothic Neo",
        "Arial Unicode MS",
        "Malgun Gothic",
        "Nanum Gothic",
        "NanumGothic",
        "Noto Sans CJK KR",
        "Noto Sans KR",
        "DejaVu Sans",
    ]
    selected = matplotlib.rcParams.get("font.family", ["sans-serif"])
    for name in candidates:
        if name in installed:
            matplotlib.rcParams["font.family"] = name
            selected = name
            break
    matplotlib.rcParams["axes.unicode_minus"] = False
    warnings.filterwarnings("ignore", message="Glyph .* missing from current font")
    return str(selected)


def nfc(value: Any) -> str:
    return unicodedata.normalize("NFC", str(value))


def normalize_label(value: Any) -> str:
    text = nfc(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def column_match_key(value: Any) -> str:
    text = normalize_label(value).lower()
    text = re.sub(r"\(\d+\)$", "", text)
    text = re.sub(r"[\s_]", "", text)
    return text


def safe_slug(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
    return text or "table"


def read_csv_flexible(path: str | Path) -> pd.DataFrame:
    """Read KOSIS CSV files with common Korean encodings."""
    path = Path(path)
    errors: list[str] = []
    for encoding in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")
    raise UnicodeDecodeError("csv", b"", 0, 1, f"Failed to decode {path}. Tried: {errors}")


def load_raw_data(
    raw_dir: str | Path,
    file_specs: dict[str, str] | None = None,
    include_optional: bool = True,
    discover_extra: bool = True,
    tables_dir: str | Path | None = None,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Load expected raw CSVs and write a missing-file diagnostic table."""
    raw_dir = Path(raw_dir)
    specs = dict(file_specs or RAW_FILE_SPECS)
    if include_optional:
        specs.update(OPTIONAL_RAW_FILE_SPECS)
    spec_paths = {str((raw_dir / path).resolve()) for path in specs.values()}
    if discover_extra and raw_dir.exists():
        for path in sorted(raw_dir.rglob("*.csv")):
            if "source_downloads" in path.parts:
                continue
            resolved = str(path.resolve())
            if resolved in spec_paths:
                continue
            relative = path.relative_to(raw_dir).with_suffix("")
            key = safe_slug("_".join(relative.parts))
            specs[key] = str(path.relative_to(raw_dir))
            spec_paths.add(resolved)

    datasets: dict[str, pd.DataFrame] = {}
    missing_records: list[dict[str, Any]] = []
    for key, filename in specs.items():
        path = raw_dir / filename
        if not path.exists():
            missing_records.append(
                {
                    "file_key": key,
                    "expected_path": str(path),
                    "status": "missing",
                    "meaning_for_next_step": "이 파일에서 생성할 target 또는 feature는 패널 병합에서 결측 처리된다.",
                }
            )
            continue
        df = read_csv_flexible(path)
        datasets[key] = df
        missing_records.append(
            {
                "file_key": key,
                "expected_path": str(path),
                "status": "loaded",
                "meaning_for_next_step": "1단계 진단 및 2단계 표준화 대상으로 사용한다.",
            }
        )

    missing_df = pd.DataFrame(missing_records)
    if tables_dir is not None:
        Path(tables_dir).mkdir(parents=True, exist_ok=True)
        missing_df.to_csv(Path(tables_dir) / "01_missing_raw_files.csv", index=False, encoding="utf-8-sig")
    return datasets, missing_df


def parse_period_label(label: Any) -> dict[str, Any] | None:
    """Parse KOSIS period columns such as 2026, 2026.01, and 2025.2/4."""
    text = normalize_label(label).replace('"', "")

    match = re.fullmatch(r"(\d{4})", text)
    if match:
        year = int(match.group(1))
        return {"year": year, "period": str(year), "period_type": "year", "month": np.nan, "quarter": np.nan}

    match = re.fullmatch(r"(\d{4})년", text)
    if match:
        year = int(match.group(1))
        return {"year": year, "period": str(year), "period_type": "year", "month": np.nan, "quarter": np.nan}

    match = re.fullmatch(r"(\d{4})\.(\d{1,2})/4", text)
    if match:
        year = int(match.group(1))
        quarter = int(match.group(2))
        if 1 <= quarter <= 4:
            return {
                "year": year,
                "period": f"{year}.{quarter}/4",
                "period_type": "quarter",
                "month": np.nan,
                "quarter": quarter,
            }

    match = re.fullmatch(r"(\d{4})\.(\d{1,2})", text)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        if 1 <= month <= 12:
            return {
                "year": year,
                "period": f"{year}.{month:02d}",
                "period_type": "month",
                "month": month,
                "quarter": np.nan,
            }

    match = re.fullmatch(r"(\d{4})년\s*(\d{1,2})월", text)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        if 1 <= month <= 12:
            return {
                "year": year,
                "period": f"{year}.{month:02d}",
                "period_type": "month",
                "month": month,
                "quarter": np.nan,
            }

    return None


def find_time_columns(columns: list[Any] | pd.Index) -> list[str]:
    parsed = []
    for column in columns:
        meta = parse_period_label(column)
        if meta is not None:
            parsed.append((str(column), meta))
    parsed.sort(key=lambda item: (item[1]["year"], item[1]["month"] if pd.notna(item[1]["month"]) else 0, item[1]["quarter"] if pd.notna(item[1]["quarter"]) else 0))
    return [column for column, _ in parsed]


def resolve_column(
    df: pd.DataFrame,
    logical_name: str,
    required: bool = True,
    extra_candidates: list[str] | None = None,
) -> str | None:
    """Resolve a logical column name from flexible KOSIS column candidates."""
    candidates = list(COLUMN_CANDIDATES.get(logical_name, []))
    if extra_candidates:
        candidates.extend(extra_candidates)

    columns = [normalize_label(col) for col in df.columns]
    exact_lookup = {col: original for col, original in zip(columns, df.columns)}
    for candidate in candidates:
        if candidate in exact_lookup:
            return exact_lookup[candidate]

    key_lookup = {column_match_key(col): original for col, original in zip(columns, df.columns)}
    for candidate in candidates:
        key = column_match_key(candidate)
        if key in key_lookup:
            return key_lookup[key]

    if logical_name == "region":
        for original in df.columns:
            key = column_match_key(original)
            if "시도" in key or "행정구역" in key:
                return original

    if logical_name == "age_group":
        for original in df.columns:
            key = column_match_key(original)
            if "연령" in key:
                return original

    if not required:
        return None

    message = (
        f"필수 컬럼 매핑 실패: logical_name={logical_name}\n"
        f"현재 컬럼 목록: {list(df.columns)}\n"
        f"후보 컬럼명: {candidates}\n"
        "COLUMN_CANDIDATES 또는 파일별 매핑을 추가해야 한다."
    )
    raise ColumnMappingError(message)


def clean_numeric(series: pd.Series) -> pd.Series:
    """Convert KOSIS values to numeric while treating symbols as missing."""
    text = series.astype("string").map(lambda x: normalize_label(x) if pd.notna(x) else x)
    text = text.replace(list(MISSING_VALUE_TOKENS), pd.NA)
    text = text.str.replace(",", "", regex=False)
    text = text.str.replace("%", "", regex=False)
    text = text.str.replace(" ", "", regex=False)
    return pd.to_numeric(text, errors="coerce")


def normalize_region(value: Any) -> str | float:
    if pd.isna(value):
        return np.nan
    text = normalize_label(value)
    text = re.sub(r"\s+", "", text)
    if text in {"계", "전국", "전국계", "합계"}:
        return "계"
    return REGION_NAME_MAP.get(text, text)


def metro_area(region: Any) -> str | float:
    if pd.isna(region) or region == "계":
        return np.nan
    return "수도권" if region in METRO_REGIONS else "비수도권"


def summarize_columns(df: pd.DataFrame, file_key: str) -> pd.DataFrame:
    records = []
    duplicate_rows = int(df.duplicated().sum())
    for column in df.columns:
        non_null = df[column].dropna()
        samples = non_null.astype(str).head(5).tolist()
        records.append(
            {
                "file_key": file_key,
                "row_count": len(df),
                "column_count": df.shape[1],
                "duplicate_rows_in_file": duplicate_rows,
                "column": column,
                "dtype": str(df[column].dtype),
                "missing_count": int(df[column].isna().sum()),
                "missing_rate": float(df[column].isna().mean()),
                "unique_count": int(df[column].nunique(dropna=True)),
                "sample_values": " | ".join(samples),
                "meaning_for_next_step": "결측률, dtype, 고유값 수를 보고 표준화·숫자 변환·feature 생성 가능성을 판단한다.",
            }
        )
    return pd.DataFrame(records)


def extract_years_from_raw(df: pd.DataFrame) -> list[int]:
    time_cols = find_time_columns(df.columns)
    years = {parse_period_label(col)["year"] for col in time_cols if parse_period_label(col) is not None}
    if years:
        return sorted(years)

    year_col = resolve_column(df, "year", required=False)
    if year_col is None:
        return []
    parsed = pd.to_numeric(df[year_col].astype(str).str.extract(r"(\d{4})", expand=False), errors="coerce")
    return sorted(parsed.dropna().astype(int).unique().tolist())


def period_coverage_from_raw(df: pd.DataFrame, file_key: str) -> pd.DataFrame:
    records = []
    time_cols = find_time_columns(df.columns)
    if time_cols:
        for column in time_cols:
            meta = parse_period_label(column)
            if meta is None:
                continue
            records.append(
                {
                    "file_key": file_key,
                    "year": meta["year"],
                    "period": meta["period"],
                    "period_type": meta["period_type"],
                }
            )
    else:
        year_col = resolve_column(df, "year", required=False)
        if year_col is not None:
            years = pd.to_numeric(df[year_col].astype(str).str.extract(r"(\d{4})", expand=False), errors="coerce")
            for year in sorted(years.dropna().astype(int).unique()):
                records.append({"file_key": file_key, "year": year, "period": str(year), "period_type": "year"})
    return pd.DataFrame(records)


def diagnose_raw_files(
    datasets: dict[str, pd.DataFrame],
    tables_dir: str | Path,
    expected_years: list[int] | None = None,
) -> dict[str, pd.DataFrame]:
    """Write 1단계 diagnostics for loaded raw datasets."""
    tables_dir = Path(tables_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    expected_years = expected_years or EXPECTED_YEARS

    file_records: list[dict[str, Any]] = []
    duplicate_records: list[dict[str, Any]] = []
    coverage_frames: list[pd.DataFrame] = []

    for file_key, df in datasets.items():
        overview = summarize_columns(df, file_key)
        overview.to_csv(tables_dir / f"01_column_overview_{file_key}.csv", index=False, encoding="utf-8-sig")

        years = extract_years_from_raw(df)
        missing_years = sorted(set(expected_years) - set(years))
        duplicate_count = int(df.duplicated().sum())
        time_cols = find_time_columns(df.columns)
        file_records.append(
            {
                "file_key": file_key,
                "rows": len(df),
                "columns": df.shape[1],
                "duplicate_rows": duplicate_count,
                "years_present": ", ".join(map(str, years)),
                "min_year": min(years) if years else np.nan,
                "max_year": max(years) if years else np.nan,
                "covers_2016_2026": set(expected_years).issubset(set(years)),
                "missing_expected_years": ", ".join(map(str, missing_years)),
                "has_2026": 2026 in years,
                "time_column_count": len(time_cols),
                "meaning_for_next_step": "연도 누락과 2026 부분자료 여부는 패널 병합 및 이후 모델링 시 제외·flag 처리 기준이 된다.",
            }
        )
        duplicate_records.append(
            {
                "file_key": file_key,
                "duplicate_rows": duplicate_count,
                "duplicate_rate": duplicate_count / len(df) if len(df) else np.nan,
                "meaning_for_next_step": "중복 row가 있으면 표준화 전 원자료 중복 제거 또는 원인 확인이 필요하다.",
            }
        )
        coverage = period_coverage_from_raw(df, file_key)
        if not coverage.empty:
            coverage_frames.append(coverage)

    file_diagnostics = pd.DataFrame(file_records)
    duplicate_diagnostics = pd.DataFrame(duplicate_records)
    period_coverage = pd.concat(coverage_frames, ignore_index=True) if coverage_frames else pd.DataFrame()

    if not period_coverage.empty:
        year_coverage = (
            period_coverage.groupby(["file_key", "year"], as_index=False)
            .agg(period_count=("period", "nunique"), periods=("period", lambda x: ", ".join(sorted(map(str, set(x))))))
            .sort_values(["file_key", "year"])
        )
        partial_2026 = []
        for file_key, group in year_coverage.groupby("file_key"):
            count_2026 = group.loc[group["year"] == 2026, "period_count"]
            other_counts = group.loc[group["year"] != 2026, "period_count"]
            max_other = int(other_counts.max()) if not other_counts.empty else np.nan
            has_2026 = not count_2026.empty
            count_value = int(count_2026.iloc[0]) if has_2026 else 0
            periods_2026 = group.loc[group["year"] == 2026, "periods"].iloc[0] if has_2026 else ""
            period_types_2026 = period_coverage.loc[
                (period_coverage["file_key"] == file_key) & (period_coverage["year"] == 2026),
                "period_type",
            ].dropna()
            if not period_types_2026.empty and (period_types_2026 == "month").any():
                expected_full_year_period_count = 12
            elif not period_types_2026.empty and (period_types_2026 == "quarter").any():
                expected_full_year_period_count = 4
            elif not period_types_2026.empty and (period_types_2026 == "year").any():
                expected_full_year_period_count = 1
            else:
                expected_full_year_period_count = np.nan
            is_partial_vs_calendar = bool(
                has_2026
                and pd.notna(expected_full_year_period_count)
                and count_value < expected_full_year_period_count
            )
            is_partial_vs_other_years = bool(has_2026 and pd.notna(max_other) and count_value < max_other)
            partial_2026.append(
                {
                    "file_key": file_key,
                    "has_2026": has_2026,
                    "period_count_2026": count_value,
                    "expected_full_year_period_count": expected_full_year_period_count,
                    "max_period_count_other_years": max_other,
                    "periods_2026": periods_2026,
                    "is_2026_likely_partial": is_partial_vs_calendar or is_partial_vs_other_years,
                    "meaning_for_next_step": "2026년이 일부 월·분기만 있으면 연평균 feature 해석에 주의하고 후속 EDA에서 별도 flag 또는 제외를 검토한다.",
                }
            )
        partial_2026_diagnostics = pd.DataFrame(partial_2026)
    else:
        year_coverage = pd.DataFrame()
        partial_2026_diagnostics = pd.DataFrame()

    file_diagnostics.to_csv(tables_dir / "01_file_diagnostics.csv", index=False, encoding="utf-8-sig")
    duplicate_diagnostics.to_csv(tables_dir / "01_duplicate_rows.csv", index=False, encoding="utf-8-sig")
    year_coverage.to_csv(tables_dir / "01_year_coverage.csv", index=False, encoding="utf-8-sig")
    partial_2026_diagnostics.to_csv(tables_dir / "01_partial_2026_diagnostics.csv", index=False, encoding="utf-8-sig")

    return {
        "file_diagnostics": file_diagnostics,
        "duplicate_diagnostics": duplicate_diagnostics,
        "year_coverage": year_coverage,
        "partial_2026_diagnostics": partial_2026_diagnostics,
    }


def standardize_kosis_frame(df: pd.DataFrame, file_key: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Standardize KOSIS data to long rows with year, region, value, and dimensions."""
    original_columns = list(df.columns)
    df = df.copy()
    df.columns = [normalize_label(col) for col in df.columns]

    time_cols = find_time_columns(df.columns)
    region_col = resolve_column(df, "region", required=True)
    year_col = resolve_column(df, "year", required=False)
    value_col = resolve_column(df, "value", required=False)
    sex_col = resolve_column(df, "sex", required=False)
    age_col = resolve_column(df, "age_group", required=False)
    item_col = resolve_column(df, "item", required=False)
    status_col = resolve_column(df, "employment_status", required=False)
    hours_col = resolve_column(df, "employment_hours", required=False)

    mapping = {
        "file_key": file_key,
        "original_columns": " | ".join(map(str, original_columns)),
        "region_col": region_col,
        "year_col": year_col,
        "value_col": value_col,
        "sex_col": sex_col,
        "age_group_col": age_col,
        "item_col": item_col,
        "employment_status_col": status_col,
        "employment_hours_col": hours_col,
        "time_column_count": len(time_cols),
    }

    if time_cols:
        id_vars = [col for col in df.columns if col not in time_cols]
        long = df.melt(id_vars=id_vars, value_vars=time_cols, var_name="source_period", value_name="value")
        period_meta = pd.DataFrame([parse_period_label(period) for period in long["source_period"]])
        long = pd.concat([long.reset_index(drop=True), period_meta.reset_index(drop=True)], axis=1)
    else:
        if year_col is None or value_col is None:
            message = (
                f"{file_key}: wide 시점 컬럼도 없고 year/value 컬럼도 매핑되지 않았다.\n"
                f"현재 컬럼 목록: {list(df.columns)}\n"
                "연도 후보: COLUMN_CANDIDATES['year'], 값 후보: COLUMN_CANDIDATES['value']를 확인해야 한다."
            )
            raise ColumnMappingError(message)
        long = df.copy()
        long["source_period"] = long[year_col]
        parsed_year = pd.to_numeric(long[year_col].astype(str).str.extract(r"(\d{4})", expand=False), errors="coerce")
        long["year"] = parsed_year
        long["period"] = parsed_year.astype("Int64").astype(str)
        long["period_type"] = "year"
        long["month"] = np.nan
        long["quarter"] = np.nan
        long["value"] = long[value_col]

    long["source_file_key"] = file_key
    long["region_raw"] = long[region_col].map(normalize_label)
    long["region"] = long["region_raw"].map(normalize_region)
    long["is_valid_region"] = long["region"].isin(VALID_REGIONS)
    long["metro_area"] = long["region"].map(metro_area)
    long["value_raw"] = long["value"]
    long["value"] = clean_numeric(long["value"])
    long["year"] = pd.to_numeric(long["year"], errors="coerce").astype("Int64")

    if sex_col is not None:
        long["sex"] = long[sex_col].map(normalize_label)
    if age_col is not None:
        long["age_group"] = long[age_col].map(normalize_label)
    if item_col is not None:
        long["variable"] = long[item_col].map(normalize_label)
    if status_col is not None:
        long["employment_status"] = long[status_col].map(normalize_label)
    if hours_col is not None:
        long["employment_hours"] = long[hours_col].map(normalize_label)

    keep_columns = [
        "source_file_key",
        "year",
        "source_period",
        "period",
        "period_type",
        "month",
        "quarter",
        "region_raw",
        "region",
        "metro_area",
        "is_valid_region",
        "value_raw",
        "value",
    ]
    for optional in ["sex", "age_group", "variable", "employment_status", "employment_hours"]:
        if optional in long.columns:
            keep_columns.append(optional)
    long = long[keep_columns].copy()
    return long, mapping


def standardize_all(
    datasets: dict[str, pd.DataFrame],
    processed_dir: str | Path,
    tables_dir: str | Path,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    """Run 2단계 standardization for every loaded dataset."""
    processed_dir = Path(processed_dir)
    tables_dir = Path(tables_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    standardized: dict[str, pd.DataFrame] = {}
    mappings: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    region_issue_frames: list[pd.DataFrame] = []
    missing_frames: list[pd.DataFrame] = []

    for file_key, df in datasets.items():
        try:
            long, mapping = standardize_kosis_frame(df, file_key)
        except ColumnMappingError as exc:
            print(str(exc))
            errors.append({"file_key": file_key, "error": str(exc), "meaning_for_next_step": "컬럼 매핑 후보를 보강해야 이 파일을 feature 생성에 사용할 수 있다."})
            continue

        standardized[file_key] = long
        mappings.append(mapping)
        long.to_csv(processed_dir / f"02_standardized_{file_key}_long.csv", index=False, encoding="utf-8-sig")

        missing_summary = summarize_columns(long, file_key)
        missing_summary.to_csv(tables_dir / f"02_column_overview_standardized_{file_key}.csv", index=False, encoding="utf-8-sig")
        missing_frames.append(missing_summary)

        region_issues = (
            long.loc[~long["is_valid_region"] & long["region"].notna(), ["source_file_key", "region_raw", "region"]]
            .drop_duplicates()
            .sort_values(["source_file_key", "region_raw"])
        )
        if not region_issues.empty:
            region_issues["meaning_for_next_step"] = "17개 시도 외 지역은 패널 feature 생성에서 제외한다. '계'는 전국 합계라 지역 비교에 사용하지 않는다."
            region_issue_frames.append(region_issues)

    mapping_df = pd.DataFrame(mappings)
    error_df = pd.DataFrame(errors)
    region_issues_df = pd.concat(region_issue_frames, ignore_index=True) if region_issue_frames else pd.DataFrame()
    missing_df = pd.concat(missing_frames, ignore_index=True) if missing_frames else pd.DataFrame()

    mapping_df.to_csv(tables_dir / "02_column_mapping_summary.csv", index=False, encoding="utf-8-sig")
    error_df.to_csv(tables_dir / "02_column_mapping_errors.csv", index=False, encoding="utf-8-sig")
    region_issues_df.to_csv(tables_dir / "02_region_mapping_issues.csv", index=False, encoding="utf-8-sig")
    missing_df.to_csv(tables_dir / "02_preprocessing_missing_summary.csv", index=False, encoding="utf-8-sig")
    return standardized, mapping_df, error_df


def valid_panel_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df["is_valid_region"] & df["year"].notna() & df["value"].notna()].copy()


def normalize_category(value: Any) -> str:
    text = normalize_label(value)
    text = text.replace("*", "")
    text = re.sub(r"^-+", "", text)
    text = re.sub(r"\s+", "", text)
    return text


def annual_dimension_mean(df: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    work = valid_panel_rows(df)
    group_cols = ["year", "region", "metro_area"] + dimensions
    annual = (
        work.groupby(group_cols, dropna=False, as_index=False)
        .agg(value=("value", "mean"), source_period_count=("period", "nunique"))
        .sort_values(group_cols)
    )
    annual["year"] = annual["year"].astype(int)
    return annual


def add_period_count_feature(base: pd.DataFrame, source: pd.DataFrame, file_key: str) -> pd.DataFrame:
    periods = (
        valid_panel_rows(source)
        .groupby(["year", "region"], as_index=False)
        .agg(**{f"period_count_{file_key}": ("period", "nunique")})
    )
    periods["year"] = periods["year"].astype(int)
    return base.merge(periods, on=["year", "region"], how="left")


def find_columns_by_labels(pivot: pd.DataFrame, labels: list[str]) -> list[str]:
    normalized_lookup = {normalize_category(col): col for col in pivot.columns}
    found = []
    for label in labels:
        key = normalize_category(label)
        if key in normalized_lookup:
            found.append(normalized_lookup[key])
    return found


def divide_percent(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return np.where(denominator.replace(0, np.nan).notna(), numerator / denominator.replace(0, np.nan) * 100, np.nan)


def build_life_target(df: pd.DataFrame | None) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    logs: list[dict[str, Any]] = []
    if df is None or df.empty:
        logs.append(
            {
                "source": "life_satisfaction",
                "feature": "life_satisfaction",
                "status": "not_created",
                "meaning_for_next_step": "life_satisfaction.csv가 없으면 최종 패널은 고용 feature 중심으로 생성되고 target은 결측이다.",
            }
        )
        return pd.DataFrame(), logs

    work = valid_panel_rows(df)
    if "variable" in work.columns and work["variable"].nunique(dropna=True) > 1:
        mask = work["variable"].astype(str).str.contains("삶|만족|질|생활", regex=True, na=False)
        if mask.any():
            work = work.loc[mask].copy()
            selection_note = "삶/만족/질 키워드가 포함된 항목을 target 후보로 선택했다."
        else:
            selection_note = "삶/만족/질 키워드를 찾지 못해 전체 value 평균을 target으로 사용했다. 항목 매핑 확인이 필요하다."
    else:
        selection_note = "단일 지표 파일로 판단해 value를 삶의 만족도 target으로 사용했다."

    target = (
        work.groupby(["year", "region", "metro_area"], as_index=False)
        .agg(life_satisfaction=("value", "mean"), life_satisfaction_period_count=("period", "nunique"))
        .sort_values(["year", "region"])
    )
    target["year"] = target["year"].astype(int)
    logs.append(
        {
            "source": "life_satisfaction",
            "feature": "life_satisfaction",
            "status": "created",
            "meaning_for_next_step": selection_note,
        }
    )
    return target, logs


def build_sex_features(df: pd.DataFrame | None) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    logs: list[dict[str, Any]] = []
    if df is None or df.empty or "sex" not in df.columns:
        logs.append({"source": "employment_region_sex", "feature": "sex_features", "status": "not_created", "meaning_for_next_step": "성별 컬럼이 없어 성별 고용 격차 feature를 만들 수 없다."})
        return pd.DataFrame(), logs

    annual = annual_dimension_mean(df, ["sex"])
    pivot = annual.pivot_table(index=["year", "region", "metro_area"], columns="sex", values="value", aggfunc="mean").reset_index()
    total_col = find_columns_by_labels(pivot, ["계"])
    male_col = find_columns_by_labels(pivot, ["남자", "남성"])
    female_col = find_columns_by_labels(pivot, ["여자", "여성"])

    out = pivot[["year", "region", "metro_area"]].copy()
    male = pivot[male_col[0]] if male_col else pd.Series(np.nan, index=pivot.index)
    female = pivot[female_col[0]] if female_col else pd.Series(np.nan, index=pivot.index)
    total = pivot[total_col[0]] if total_col else male.add(female, fill_value=np.nan)

    out["employed_count_total_sex_file"] = total
    out["male_employed_count"] = male
    out["female_employed_count"] = female
    out["female_employed_share"] = divide_percent(female, total)
    out["male_female_employed_count_gap"] = male - female
    out["male_female_employed_share_gap"] = divide_percent(male - female, total)
    out = add_period_count_feature(out, df, "employment_region_sex")

    logs.extend(
        [
            {"source": "employment_region_sex", "feature": "female_employed_share", "status": "created", "meaning_for_next_step": "취업자 수 원자료의 지역 규모 영향을 줄이기 위해 여성 취업자 비중을 feature로 사용한다."},
            {"source": "employment_region_sex", "feature": "male_female_employed_share_gap", "status": "created", "meaning_for_next_step": "고용률 격차가 아닌 취업자 구성비 격차다. 고용률 파일이 추가되면 rate 기반 feature로 대체하는 것이 적절하다."},
        ]
    )
    return out, logs


def parse_age_range(label: Any) -> tuple[int | None, int | None]:
    text = normalize_label(label).replace(" ", "")
    match = re.search(r"(\d+)[-~](\d+)세", text)
    if match:
        return int(match.group(1)), int(match.group(2))
    match = re.search(r"(\d+)세이상", text)
    if match:
        return int(match.group(1)), None
    return None, None


def sum_age_columns(pivot: pd.DataFrame, predicate: Any) -> pd.Series:
    columns = []
    for column in pivot.columns:
        if column in {"year", "region", "metro_area"}:
            continue
        start, end = parse_age_range(column)
        if predicate(column, start, end):
            columns.append(column)
    if not columns:
        return pd.Series(np.nan, index=pivot.index)
    return pivot[columns].sum(axis=1, min_count=1)


def build_age_features(df: pd.DataFrame | None) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    logs: list[dict[str, Any]] = []
    if df is None or df.empty or "age_group" not in df.columns:
        logs.append({"source": "employment_region_age", "feature": "age_features", "status": "not_created", "meaning_for_next_step": "연령 컬럼이 없어 청년·중장년·고령층 feature를 만들 수 없다."})
        return pd.DataFrame(), logs

    annual = annual_dimension_mean(df, ["age_group"])
    pivot = annual.pivot_table(index=["year", "region", "metro_area"], columns="age_group", values="value", aggfunc="mean").reset_index()
    out = pivot[["year", "region", "metro_area"]].copy()
    total_col = find_columns_by_labels(pivot, ["계"])
    total = pivot[total_col[0]] if total_col else sum_age_columns(pivot, lambda _c, start, end: start is not None and (end is not None or start >= 60))

    youth_exact = find_columns_by_labels(pivot, ["15 - 29세", "15-29세", "15~29세"])
    if youth_exact:
        youth = pivot[youth_exact[0]]
    else:
        youth = sum_age_columns(pivot, lambda _c, start, end: start is not None and end is not None and start >= 15 and end <= 29)

    middle = sum_age_columns(pivot, lambda _c, start, end: start is not None and end is not None and start >= 30 and end <= 59)
    senior = sum_age_columns(pivot, lambda _c, start, _end: start is not None and start >= 60)
    working_age_exact = find_columns_by_labels(pivot, ["15 - 64세", "15-64세", "15~64세"])
    working_age = pivot[working_age_exact[0]] if working_age_exact else pd.Series(np.nan, index=pivot.index)

    out["employed_count_total_age_file"] = total
    out["youth_employed_count"] = youth
    out["youth_employed_share"] = divide_percent(youth, total)
    out["middle_age_employed_count"] = middle
    out["middle_age_employed_share"] = divide_percent(middle, total)
    out["senior_employed_count"] = senior
    out["senior_employed_share"] = divide_percent(senior, total)
    out["working_age_employed_count"] = working_age
    out = add_period_count_feature(out, df, "employment_region_age")

    logs.extend(
        [
            {"source": "employment_region_age", "feature": "youth_employed_share", "status": "created", "meaning_for_next_step": "청년층 취업자 수 자체보다 지역 내 취업자 구성비를 사용해 규모 효과를 줄인다."},
            {"source": "employment_region_age", "feature": "senior_employed_share", "status": "created", "meaning_for_next_step": "고령층 고용 구조 차이가 삶의 만족도와 관련되는지 후속 상관·시각화에서 검토할 수 있다."},
        ]
    )
    return out, logs


def pick_category_series(pivot: pd.DataFrame, labels: list[str]) -> pd.Series:
    columns = find_columns_by_labels(pivot, labels)
    if columns:
        return pivot[columns[0]]
    return pd.Series(np.nan, index=pivot.index)


def build_status_features(df: pd.DataFrame | None) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    logs: list[dict[str, Any]] = []
    if df is None or df.empty or "employment_status" not in df.columns:
        logs.append({"source": "employment_status", "feature": "status_features", "status": "not_created", "meaning_for_next_step": "종사상지위별 컬럼이 없어 지위별 취업자 비율 feature를 만들 수 없다."})
        return pd.DataFrame(), logs

    work = df.copy()
    work["employment_status"] = work["employment_status"].map(normalize_category)
    annual = annual_dimension_mean(work, ["employment_status"])
    pivot = annual.pivot_table(index=["year", "region", "metro_area"], columns="employment_status", values="value", aggfunc="mean").reset_index()
    out = pivot[["year", "region", "metro_area"]].copy()
    total = pick_category_series(pivot, ["계"])
    out["employed_count_total_status_file"] = total

    categories = {
        "non_wage_worker_share": ["비임금근로자"],
        "self_employed_share": ["자영업자"],
        "employer_self_employed_share": ["고용원이있는자영업자"],
        "own_account_self_employed_share": ["고용원이없는자영업자"],
        "unpaid_family_worker_share": ["무급가족종사자"],
        "wage_worker_share": ["임금근로자"],
        "regular_worker_share": ["상용근로자"],
        "temporary_worker_share": ["임시근로자"],
        "daily_worker_share": ["일용근로자"],
    }
    for feature, labels in categories.items():
        out[feature] = divide_percent(pick_category_series(pivot, labels), total)
    out = add_period_count_feature(out, work, "employment_status")

    logs.append({"source": "employment_status", "feature": "status_share_features", "status": "created", "meaning_for_next_step": "종사상지위별 취업자 수를 전체 취업자 대비 비율로 바꿔 지역 인구 규모 효과를 줄였다."})
    return out, logs


def build_hours_features(df: pd.DataFrame | None) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    logs: list[dict[str, Any]] = []
    if df is None or df.empty or "employment_hours" not in df.columns:
        logs.append({"source": "employment_hours", "feature": "hours_features", "status": "not_created", "meaning_for_next_step": "취업시간별 컬럼이 없어 단시간·장시간 feature를 만들 수 없다."})
        return pd.DataFrame(), logs

    work = df.copy()
    work["employment_hours"] = work["employment_hours"].map(normalize_category)
    annual = annual_dimension_mean(work, ["employment_hours"])
    pivot = annual.pivot_table(index=["year", "region", "metro_area"], columns="employment_hours", values="value", aggfunc="mean").reset_index()
    out = pivot[["year", "region", "metro_area"]].copy()
    total = pick_category_series(pivot, ["계"])
    out["employed_count_total_hours_file"] = total

    very_short = pick_category_series(pivot, ["1-17시간"])
    short_18_35 = pick_category_series(pivot, ["18-35시간"])
    standard_36_44 = pick_category_series(pivot, ["36-44시간"])
    extended_45_53 = pick_category_series(pivot, ["45-53시간"])
    long_54_plus = pick_category_series(pivot, ["54시간이상", "54시간 이상"])

    out["very_short_hours_worker_share"] = divide_percent(very_short, total)
    out["short_hours_worker_share"] = divide_percent(very_short.add(short_18_35, fill_value=0), total)
    out["standard_hours_worker_share"] = divide_percent(standard_36_44, total)
    out["extended_hours_worker_share"] = divide_percent(extended_45_53.add(long_54_plus, fill_value=0), total)
    out["long_hours_worker_share"] = divide_percent(long_54_plus, total)
    out = add_period_count_feature(out, work, "employment_hours")

    logs.append({"source": "employment_hours", "feature": "hours_share_features", "status": "created", "meaning_for_next_step": "취업시간별 취업자 수를 전체 취업자 대비 비율로 바꿔 단시간·장시간 고용 구조를 비교한다."})
    return out, logs


def is_youth_label(label: Any) -> bool:
    text = normalize_category(label)
    return any(token in text for token in ["청년", "15-29", "15~29", "15 - 29", "15세-29세"])


def indicator_feature_name(row: pd.Series) -> str | None:
    """Map rate-style KOSIS rows to canonical feature names without fabricating missing data."""
    variable = normalize_category(row.get("variable", ""))
    sex = normalize_category(row.get("sex", ""))
    age = normalize_category(row.get("age_group", ""))

    is_total_sex = sex in {"", "계", "전체"}
    is_total_age = age in {"", "계", "전체"}

    if "경제활동참가율" in variable or "경제활동참가" in variable:
        if is_total_sex and is_total_age:
            return "labor_force_participation_rate"
        return None

    if "실업률" in variable:
        if is_youth_label(age):
            return "youth_unemployment_rate"
        if is_total_sex and is_total_age:
            return "unemployment_rate"
        return None

    if "고용률" in variable:
        if is_youth_label(age):
            return "youth_employment_rate"
        if sex in {"남자", "남성"} and is_total_age:
            return "male_employment_rate"
        if sex in {"여자", "여성"} and is_total_age:
            return "female_employment_rate"
        if is_total_sex and is_total_age:
            return "employment_rate"
        return None

    return None


def build_indicator_features(standardized: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Create canonical employment-rate features from any raw file that has an item/variable column."""
    frames = []
    logs: list[dict[str, Any]] = []
    for file_key, df in standardized.items():
        if df.empty or "variable" not in df.columns:
            continue
        work = valid_panel_rows(df)
        if work.empty:
            continue
        work = work.copy()
        work["canonical_feature"] = work.apply(indicator_feature_name, axis=1)
        matched = work[work["canonical_feature"].notna()].copy()
        if matched.empty:
            continue
        matched["source_file_key"] = file_key
        frames.append(matched[["year", "region", "metro_area", "canonical_feature", "value", "source_file_key"]])

    if not frames:
        logs.append(
            {
                "source": "all_standardized_files",
                "feature": "employment_rate_unemployment_rate_labor_force_rate",
                "status": "not_created",
                "meaning_for_next_step": "고용률·실업률·경제활동참가율처럼 항목명이 있는 rate 원자료가 없어 생성하지 않았다.",
            }
        )
        return pd.DataFrame(), logs

    matched_all = pd.concat(frames, ignore_index=True)
    annual = (
        matched_all.groupby(["year", "region", "metro_area", "canonical_feature"], as_index=False)
        .agg(value=("value", "mean"), source_files=("source_file_key", lambda x: ", ".join(sorted(set(map(str, x))))))
    )
    pivot = annual.pivot_table(index=["year", "region", "metro_area"], columns="canonical_feature", values="value", aggfunc="mean").reset_index()
    pivot.columns.name = None
    if {"male_employment_rate", "female_employment_rate"}.issubset(pivot.columns):
        pivot["gender_employment_gap"] = pivot["male_employment_rate"] - pivot["female_employment_rate"]

    created = [feature for feature in REQUIRED_EMPLOYMENT_FEATURES if feature in pivot.columns and pivot[feature].notna().any()]
    for feature in created:
        logs.append(
            {
                "source": "rate_indicator_files",
                "feature": feature,
                "status": "created",
                "meaning_for_next_step": "항목명이 있는 rate 원자료에서 직접 생성했다. 핵심 분석에 우선 사용한다.",
            }
        )
    return pivot, logs


def build_feature_frames(
    standardized: dict[str, pd.DataFrame],
    processed_dir: str | Path,
    tables_dir: str | Path,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Create 3단계 year-region target and employment features."""
    processed_dir = Path(processed_dir)
    tables_dir = Path(tables_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    builders = {
        "target_life_satisfaction": lambda: build_life_target(standardized.get("life_satisfaction")),
        "features_employment_indicators": lambda: build_indicator_features(standardized),
        "features_employment_region_sex": lambda: build_sex_features(standardized.get("employment_region_sex")),
        "features_employment_region_age": lambda: build_age_features(standardized.get("employment_region_age")),
        "features_employment_status": lambda: build_status_features(standardized.get("employment_status")),
        "features_employment_hours": lambda: build_hours_features(standardized.get("employment_hours")),
    }

    feature_frames: dict[str, pd.DataFrame] = {}
    logs: list[dict[str, Any]] = []
    unit_records: list[dict[str, Any]] = []

    for name, builder in builders.items():
        frame, frame_logs = builder()
        feature_frames[name] = frame
        logs.extend(frame_logs)
        if not frame.empty:
            frame.to_csv(processed_dir / f"03_{name}.csv", index=False, encoding="utf-8-sig")
            duplicate_keys = int(frame.duplicated(["year", "region"]).sum())
            unit_records.append(
                {
                    "frame": name,
                    "rows": len(frame),
                    "unique_year_region": frame[["year", "region"]].drop_duplicates().shape[0],
                    "duplicate_year_region_rows": duplicate_keys,
                    "meaning_for_next_step": "duplicate_year_region_rows가 0이어야 최종 패널 병합 단위가 안정적이다.",
                }
            )
        else:
            pd.DataFrame(frame_logs).to_csv(processed_dir / f"03_{name}_not_created.csv", index=False, encoding="utf-8-sig")

    log_df = pd.DataFrame(logs)
    unit_df = pd.DataFrame(unit_records)
    log_df.to_csv(tables_dir / "03_feature_build_log.csv", index=False, encoding="utf-8-sig")
    unit_df.to_csv(tables_dir / "03_year_region_unit_check.csv", index=False, encoding="utf-8-sig")
    return feature_frames, log_df


def apply_required_feature_aliases(panel: pd.DataFrame, tables_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Add canonical feature names for requested ratio variables and log unavailable features."""
    panel = panel.copy()
    records = []
    for feature, source in RATIO_ALIAS_MAP.items():
        if feature not in panel.columns and source in panel.columns:
            panel[feature] = panel[source]
            records.append(
                {
                    "feature": feature,
                    "status": "created",
                    "source_column": source,
                    "note": "취업자 수 원자료에서 전체 취업자 대비 비율로 계산된 기존 share 변수를 표준 ratio 이름으로 복사했다.",
                }
            )

    if "gender_employment_gap" not in panel.columns and {"male_employment_rate", "female_employment_rate"}.issubset(panel.columns):
        panel["gender_employment_gap"] = panel["male_employment_rate"] - panel["female_employment_rate"]
        records.append(
            {
                "feature": "gender_employment_gap",
                "status": "created",
                "source_column": "male_employment_rate - female_employment_rate",
                "note": "남성 고용률에서 여성 고용률을 뺀 값이다.",
            }
        )

    for feature in REQUIRED_EMPLOYMENT_FEATURES:
        if feature in panel.columns and panel[feature].notna().any():
            if not any(record["feature"] == feature for record in records):
                records.append(
                    {
                        "feature": feature,
                        "status": "created",
                        "source_column": feature,
                        "note": "원자료 또는 이전 feature 생성 단계에서 생성되었다.",
                    }
                )
        else:
            records.append(
                {
                    "feature": feature,
                    "status": "not_created",
                    "source_column": "",
                    "note": "현재 raw 데이터에서 이 변수를 만들 수 있는 항목/분자/분모가 확인되지 않았다. 값을 추정하거나 대체하지 않았다.",
                }
            )

    availability = pd.DataFrame(records).drop_duplicates("feature", keep="first")
    Path(tables_dir).mkdir(parents=True, exist_ok=True)
    availability.to_csv(Path(tables_dir) / "04_employment_feature_availability.csv", index=False, encoding="utf-8-sig")
    return panel, availability


def merge_feature_frames(
    feature_frames: dict[str, pd.DataFrame],
    processed_dir: str | Path,
    tables_dir: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create 4단계 final year-region panel and write merge diagnostics."""
    processed_dir = Path(processed_dir)
    tables_dir = Path(tables_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    target = feature_frames.get("target_life_satisfaction", pd.DataFrame())
    employment_frames = [
        frame
        for key, frame in feature_frames.items()
        if key != "target_life_satisfaction" and isinstance(frame, pd.DataFrame) and not frame.empty
    ]

    merge_keys = ["year", "region", "metro_area"]
    employment_panel = reduce(lambda left, right: left.merge(right, on=merge_keys, how="outer"), employment_frames) if employment_frames else pd.DataFrame(columns=merge_keys)

    if isinstance(target, pd.DataFrame) and not target.empty:
        panel = target.merge(employment_panel, on=merge_keys, how="outer")
    else:
        panel = employment_panel.copy()
        panel["life_satisfaction"] = np.nan
        panel["life_satisfaction_period_count"] = np.nan

    if not panel.empty:
        panel = panel.sort_values(["year", "region"]).reset_index(drop=True)
    panel, feature_availability = apply_required_feature_aliases(panel, tables_dir)

    target_keys = target[["year", "region"]].drop_duplicates() if isinstance(target, pd.DataFrame) and not target.empty else pd.DataFrame(columns=["year", "region"])
    employment_keys = employment_panel[["year", "region"]].drop_duplicates() if not employment_panel.empty else pd.DataFrame(columns=["year", "region"])
    unmatched_target = target_keys.merge(employment_keys, on=["year", "region"], how="left", indicator=True).query("_merge == 'left_only'").drop(columns="_merge")
    unmatched_employment = employment_keys.merge(target_keys, on=["year", "region"], how="left", indicator=True).query("_merge == 'left_only'").drop(columns="_merge")
    merge_failed = pd.concat(
        [
            unmatched_target.assign(failed_side="target_without_employment_features"),
            unmatched_employment.assign(failed_side="employment_features_without_target"),
        ],
        ignore_index=True,
    )

    merge_summary_records = [
        {
            "frame": key,
            "rows": len(frame) if isinstance(frame, pd.DataFrame) else 0,
            "unique_year_region": frame[["year", "region"]].drop_duplicates().shape[0] if isinstance(frame, pd.DataFrame) and not frame.empty else 0,
            "meaning_for_next_step": "병합 전 source별 패널 단위 row 수다. target과 feature의 year-region coverage 차이를 확인한다.",
        }
        for key, frame in feature_frames.items()
    ]
    merge_summary_records.append(
        {
            "frame": "final_panel",
            "rows": len(panel),
            "unique_year_region": panel[["year", "region"]].drop_duplicates().shape[0] if not panel.empty else 0,
            "meaning_for_next_step": "최종 EDA 5단계 이후 사용할 year-region 패널 row 수다.",
        }
    )
    merge_summary = pd.DataFrame(merge_summary_records)

    missing_summary = []
    for column in panel.columns:
        missing_summary.append(
            {
                "column": column,
                "missing_count": int(panel[column].isna().sum()),
                "missing_rate": float(panel[column].isna().mean()) if len(panel) else np.nan,
                "meaning_for_next_step": "결측률이 높은 feature는 후속 EDA·모델링에서 제외 또는 별도 처리 후보가 된다.",
            }
        )
    missing_summary_df = pd.DataFrame(missing_summary)

    panel.to_csv(processed_dir / "kosis_life_quality_employment_panel.csv", index=False, encoding="utf-8-sig")
    merge_summary.to_csv(tables_dir / "04_merge_summary.csv", index=False, encoding="utf-8-sig")
    unmatched_target.to_csv(tables_dir / "04_unmatched_target_year_region.csv", index=False, encoding="utf-8-sig")
    unmatched_employment.to_csv(tables_dir / "04_unmatched_employment_year_region.csv", index=False, encoding="utf-8-sig")
    merge_failed.to_csv(tables_dir / "05_merge_failed_rows.csv", index=False, encoding="utf-8-sig")
    missing_summary_df.to_csv(tables_dir / "04_panel_missing_summary.csv", index=False, encoding="utf-8-sig")

    if not panel.empty:
        coverage = (
            panel.groupby("year", as_index=False)
            .agg(region_count=("region", "nunique"), regions=("region", lambda x: ", ".join(sorted(map(str, set(x))))))
            .sort_values("year")
        )
    else:
        coverage = pd.DataFrame(columns=["year", "region_count", "regions"])
    coverage["meaning_for_next_step"] = "연도별 지역 coverage가 17개인지 확인하고, 2026 부분자료는 후속 분석에서 별도 해석한다."
    coverage.to_csv(tables_dir / "04_panel_year_region_coverage.csv", index=False, encoding="utf-8-sig")
    return panel, merge_summary


def write_data_diagnosis(
    datasets: dict[str, pd.DataFrame],
    missing_raw: pd.DataFrame,
    diagnostics: dict[str, pd.DataFrame],
    tables_dir: str | Path,
) -> pd.DataFrame:
    """Write the requested one-file raw data diagnosis table."""
    tables_dir = Path(tables_dir)
    records: list[dict[str, Any]] = []
    file_diag = diagnostics.get("file_diagnostics", pd.DataFrame())
    partial_diag = diagnostics.get("partial_2026_diagnostics", pd.DataFrame())

    for _, row in missing_raw.iterrows():
        file_key = row["file_key"]
        df = datasets.get(file_key)
        diag_row = file_diag[file_diag["file_key"] == file_key]
        partial_row = partial_diag[partial_diag["file_key"] == file_key]
        if df is None:
            records.append(
                {
                    "file_key": file_key,
                    "status": "missing",
                    "rows": 0,
                    "columns": 0,
                    "column_names": "",
                    "dtypes": "",
                    "total_missing_count": np.nan,
                    "overall_missing_rate": np.nan,
                    "duplicate_rows": np.nan,
                    "years_present": "",
                    "covers_2016_2026": False,
                    "has_2026": False,
                    "is_2026_likely_partial": np.nan,
                    "region_check": "not_available",
                    "note": "raw 파일이 없어 진단할 수 없다.",
                }
            )
            continue

        region_col = resolve_column(df, "region", required=False)
        if region_col is not None:
            normalized_regions = df[region_col].map(normalize_region)
            valid_region_count = int(normalized_regions[normalized_regions.isin(VALID_REGIONS)].nunique())
            region_check = "valid_17_regions" if valid_region_count == 17 else f"valid_region_count={valid_region_count}"
        else:
            region_check = "region_column_not_mapped"

        records.append(
            {
                "file_key": file_key,
                "status": row["status"],
                "rows": len(df),
                "columns": df.shape[1],
                "column_names": " | ".join(map(str, df.columns)),
                "dtypes": " | ".join(f"{col}:{dtype}" for col, dtype in df.dtypes.items()),
                "total_missing_count": int(df.isna().sum().sum()),
                "overall_missing_rate": float(df.isna().sum().sum() / (df.shape[0] * df.shape[1])) if df.shape[0] and df.shape[1] else np.nan,
                "duplicate_rows": int(df.duplicated().sum()),
                "years_present": diag_row["years_present"].iloc[0] if not diag_row.empty else "",
                "covers_2016_2026": bool(diag_row["covers_2016_2026"].iloc[0]) if not diag_row.empty else False,
                "has_2026": bool(diag_row["has_2026"].iloc[0]) if not diag_row.empty else False,
                "is_2026_likely_partial": bool(partial_row["is_2026_likely_partial"].iloc[0]) if not partial_row.empty else np.nan,
                "region_check": region_check,
                "note": "컬럼·기간·지역·중복 진단 결과다. 2016~2026 전체 coverage와 2026 부분자료 여부를 우선 확인한다.",
            }
        )
    out = pd.DataFrame(records)
    out.to_csv(tables_dir / "01_data_diagnosis.csv", index=False, encoding="utf-8-sig")
    return out


def write_life_satisfaction_summary(panel: pd.DataFrame, tables_dir: str | Path) -> pd.DataFrame:
    tables_dir = Path(tables_dir)
    if "life_satisfaction" not in panel.columns or panel["life_satisfaction"].notna().sum() == 0:
        out = pd.DataFrame(
            [
                {
                    "summary_type": "not_available",
                    "year": np.nan,
                    "region": "",
                    "metro_area": "",
                    "mean": np.nan,
                    "std": np.nan,
                    "count": 0,
                    "note": "life_satisfaction 원자료가 없어 삶의 만족도 요약을 계산하지 않았다.",
                }
            ]
        )
        out.to_csv(tables_dir / "03_life_satisfaction_summary.csv", index=False, encoding="utf-8-sig")
        return out

    frames = []
    for summary_type, group_cols in [
        ("year", ["year"]),
        ("region", ["region"]),
        ("metro_area", ["metro_area"]),
        ("year_metro_area", ["year", "metro_area"]),
    ]:
        summary = (
            panel.groupby(group_cols, dropna=False)["life_satisfaction"]
            .agg(mean="mean", std="std", count="count")
            .reset_index()
        )
        summary["summary_type"] = summary_type
        for col in ["year", "region", "metro_area"]:
            if col not in summary.columns:
                summary[col] = np.nan if col == "year" else ""
        frames.append(summary[["summary_type", "year", "region", "metro_area", "mean", "std", "count"]])
    out = pd.concat(frames, ignore_index=True)
    out["note"] = "삶의 만족도 target의 연도·지역·권역별 평균과 표준편차다."
    out.to_csv(tables_dir / "03_life_satisfaction_summary.csv", index=False, encoding="utf-8-sig")
    return out


def available_analysis_features(panel: pd.DataFrame) -> list[str]:
    return [feature for feature in REQUIRED_EMPLOYMENT_FEATURES if feature in panel.columns and panel[feature].notna().any()]


def can_plot(panel: pd.DataFrame, required_columns: list[str]) -> tuple[bool, str]:
    missing = [column for column in required_columns if column not in panel.columns]
    if missing:
        return False, f"필수 컬럼 없음: {', '.join(missing)}"
    non_null = panel[required_columns].dropna()
    if non_null.empty:
        return False, "필수 컬럼 조합에 유효한 row가 없음"
    return True, "created"


def save_plot(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def plot_line_metro(panel: pd.DataFrame, y: str, title: str, ylabel: str, path: Path) -> tuple[str, str]:
    ok, reason = can_plot(panel, ["year", "metro_area", y])
    if not ok:
        return "skipped", reason
    plot_df = panel.groupby(["year", "metro_area"], as_index=False)[y].mean()
    plt.figure(figsize=(9, 5))
    sns.lineplot(data=plot_df, x="year", y=y, hue="metro_area", marker="o")
    plt.title(title)
    plt.xlabel("연도")
    plt.ylabel(ylabel)
    plt.legend(title="권역")
    save_plot(path)
    return "created", ""


def plot_scatter(panel: pd.DataFrame, x: str, y: str, title: str, xlabel: str, ylabel: str, path: Path) -> tuple[str, str]:
    ok, reason = can_plot(panel, [x, y, "metro_area"])
    if not ok:
        return "skipped", reason
    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=panel.dropna(subset=[x, y]), x=x, y=y, hue="metro_area", s=70)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(title="권역")
    save_plot(path)
    return "created", ""


def generate_core_visualizations(panel: pd.DataFrame, tables_dir: str | Path, figures_dir: str | Path) -> pd.DataFrame:
    tables_dir = Path(tables_dir)
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    set_korean_font()
    sns.set_theme(style="whitegrid")
    set_korean_font()

    records: list[dict[str, Any]] = []

    specs = [
        ("06_life_satisfaction_trend_metro.png", "line", "life_satisfaction", "수도권 vs 비수도권 삶의 만족도 추이", "삶의 만족도"),
        ("06_employment_rate_trend_metro.png", "line", "employment_rate", "수도권 vs 비수도권 고용률 추이", "고용률(%)"),
        ("06_unemployment_rate_trend_metro.png", "line", "unemployment_rate", "수도권 vs 비수도권 실업률 추이", "실업률(%)"),
    ]
    for filename, _, y, title, ylabel in specs:
        status, reason = plot_line_metro(panel, y, title, ylabel, figures_dir / filename)
        records.append({"figure": filename, "status": status, "reason": reason})

    ok, reason = can_plot(panel, ["region", "year", "life_satisfaction"])
    if ok:
        heatmap_df = panel.pivot_table(index="region", columns="year", values="life_satisfaction", aggfunc="mean")
        plt.figure(figsize=(11, 7))
        sns.heatmap(heatmap_df, annot=True, fmt=".2f", cmap="YlGnBu", linewidths=0.4)
        plt.title("시도별 삶의 만족도 heatmap")
        plt.xlabel("연도")
        plt.ylabel("시도")
        save_plot(figures_dir / "06_life_satisfaction_heatmap_region_year.png")
        records.append({"figure": "06_life_satisfaction_heatmap_region_year.png", "status": "created", "reason": ""})
    else:
        records.append({"figure": "06_life_satisfaction_heatmap_region_year.png", "status": "skipped", "reason": reason})

    scatter_specs = [
        ("06_scatter_life_satisfaction_employment_rate.png", "employment_rate", "life_satisfaction", "삶의 만족도 vs 고용률", "고용률(%)", "삶의 만족도"),
        ("06_scatter_life_satisfaction_unemployment_rate.png", "unemployment_rate", "life_satisfaction", "삶의 만족도 vs 실업률", "실업률(%)", "삶의 만족도"),
        ("06_scatter_life_satisfaction_gender_gap.png", "gender_employment_gap", "life_satisfaction", "삶의 만족도 vs 성별 고용률 격차", "성별 고용률 격차(%p)", "삶의 만족도"),
    ]
    for filename, x, y, title, xlabel, ylabel in scatter_specs:
        status, reason = plot_scatter(panel, x, y, title, xlabel, ylabel, figures_dir / filename)
        records.append({"figure": filename, "status": status, "reason": reason})

    youth_x = "youth_employment_rate" if "youth_employment_rate" in panel.columns and panel["youth_employment_rate"].notna().any() else "youth_unemployment_rate"
    status, reason = plot_scatter(
        panel,
        youth_x,
        "life_satisfaction",
        "삶의 만족도 vs 청년층 고용 지표",
        FIGURE_LABELS.get(youth_x, youth_x),
        "삶의 만족도",
        figures_dir / "06_scatter_life_satisfaction_youth_employment.png",
    )
    records.append({"figure": "06_scatter_life_satisfaction_youth_employment.png", "status": status, "reason": reason})

    corr_features = ["life_satisfaction"] + available_analysis_features(panel)
    ok, reason = can_plot(panel, corr_features)
    if ok and len(corr_features) >= 3:
        corr = panel[corr_features].corr(method="pearson")
        plt.figure(figsize=(10, 7))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, linewidths=0.4)
        plt.title("삶의 만족도와 고용 변수 상관관계(Pearson)")
        save_plot(figures_dir / "06_correlation_heatmap.png")
        records.append({"figure": "06_correlation_heatmap.png", "status": "created", "reason": ""})
    else:
        records.append({"figure": "06_correlation_heatmap.png", "status": "skipped", "reason": reason if not ok else "상관계산 가능한 feature 수 부족"})

    out = pd.DataFrame(records)
    out.to_csv(tables_dir / "06_visualization_log.csv", index=False, encoding="utf-8-sig")
    return out


def metro_gap_analysis(panel: pd.DataFrame, tables_dir: str | Path, figures_dir: str | Path) -> pd.DataFrame:
    tables_dir = Path(tables_dir)
    figures_dir = Path(figures_dir)
    variables = [
        "life_satisfaction",
        "employment_rate",
        "unemployment_rate",
        "labor_force_participation_rate",
        "youth_employment_rate",
        "youth_unemployment_rate",
        "gender_employment_gap",
    ]
    records = []
    for variable in variables:
        if variable not in panel.columns or panel[variable].notna().sum() == 0:
            records.append({"year": np.nan, "variable": variable, "metro_mean": np.nan, "nonmetro_mean": np.nan, "gap_metro_minus_nonmetro": np.nan, "status": "not_available"})
            continue
        means = panel.groupby(["year", "metro_area"], as_index=False)[variable].mean()
        pivot = means.pivot(index="year", columns="metro_area", values=variable).reset_index()
        for _, row in pivot.iterrows():
            metro_mean = row.get("수도권", np.nan)
            nonmetro_mean = row.get("비수도권", np.nan)
            records.append(
                {
                    "year": int(row["year"]),
                    "variable": variable,
                    "metro_mean": metro_mean,
                    "nonmetro_mean": nonmetro_mean,
                    "gap_metro_minus_nonmetro": metro_mean - nonmetro_mean if pd.notna(metro_mean) and pd.notna(nonmetro_mean) else np.nan,
                    "status": "calculated",
                }
            )
    out = pd.DataFrame(records)
    out.to_csv(tables_dir / "07_metro_nonmetro_gap_summary.csv", index=False, encoding="utf-8-sig")

    for variable, filename, title in [
        ("life_satisfaction", "07_gap_trend_life_satisfaction.png", "수도권-비수도권 삶의 만족도 격차 추이"),
    ]:
        plot_df = out[(out["variable"] == variable) & (out["status"] == "calculated")].dropna(subset=["gap_metro_minus_nonmetro"])
        if not plot_df.empty:
            plt.figure(figsize=(8, 5))
            sns.lineplot(data=plot_df, x="year", y="gap_metro_minus_nonmetro", marker="o")
            plt.axhline(0, color="#444444", linestyle="--", linewidth=1)
            plt.title(title)
            plt.xlabel("연도")
            plt.ylabel("격차(수도권 평균 - 비수도권 평균)")
            save_plot(figures_dir / filename)

    employment_gap = out[(out["variable"] != "life_satisfaction") & (out["status"] == "calculated")].dropna(subset=["gap_metro_minus_nonmetro"])
    if not employment_gap.empty:
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=employment_gap, x="year", y="gap_metro_minus_nonmetro", hue="variable", marker="o")
        plt.axhline(0, color="#444444", linestyle="--", linewidth=1)
        plt.title("수도권-비수도권 고용 변수 격차 추이")
        plt.xlabel("연도")
        plt.ylabel("격차(수도권 평균 - 비수도권 평균)")
        plt.legend(title="변수")
        save_plot(figures_dir / "07_gap_trend_employment_variables.png")
    return out


def correlation_analysis(panel: pd.DataFrame, tables_dir: str | Path) -> pd.DataFrame:
    from scipy import stats

    records = []
    features = available_analysis_features(panel)
    groups = [("전체", panel), ("수도권", panel[panel["metro_area"] == "수도권"]), ("비수도권", panel[panel["metro_area"] == "비수도권"])]
    for group_name, group_df in groups:
        for feature in features:
            if "life_satisfaction" not in group_df.columns:
                valid = pd.DataFrame()
            else:
                valid = group_df[["life_satisfaction", feature]].dropna()
            if len(valid) < 3 or valid["life_satisfaction"].nunique() < 2 or valid[feature].nunique() < 2:
                records.append(
                    {
                        "group": group_name,
                        "feature": feature,
                        "n": len(valid),
                        "pearson_r": np.nan,
                        "pearson_p": np.nan,
                        "spearman_r": np.nan,
                        "spearman_p": np.nan,
                        "abs_max_correlation": np.nan,
                        "status": "not_calculated",
                        "note": "표본 수가 3 미만이거나 변수 변동이 없어 상관계수를 계산하지 않았다.",
                    }
                )
                continue
            pearson = stats.pearsonr(valid[feature], valid["life_satisfaction"])
            spearman = stats.spearmanr(valid[feature], valid["life_satisfaction"])
            records.append(
                {
                    "group": group_name,
                    "feature": feature,
                    "n": len(valid),
                    "pearson_r": pearson.statistic,
                    "pearson_p": pearson.pvalue,
                    "spearman_r": spearman.statistic,
                    "spearman_p": spearman.pvalue,
                    "abs_max_correlation": max(abs(pearson.statistic), abs(spearman.statistic)),
                    "status": "calculated",
                    "note": "p-value는 표본 수가 작을 수 있으므로 탐색적으로만 해석한다.",
                }
            )
    if not records:
        records.append({"group": "전체", "feature": "", "n": 0, "pearson_r": np.nan, "pearson_p": np.nan, "spearman_r": np.nan, "spearman_p": np.nan, "abs_max_correlation": np.nan, "status": "not_calculated", "note": "사용 가능한 고용 feature가 없다."})
    out = pd.DataFrame(records).sort_values(["status", "abs_max_correlation"], ascending=[True, False])
    out.to_csv(Path(tables_dir) / "08_correlation_summary.csv", index=False, encoding="utf-8-sig")
    return out


def permutation_importance_analysis(panel: pd.DataFrame, tables_dir: str | Path, figures_dir: str | Path) -> pd.DataFrame:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.inspection import permutation_importance

    features = available_analysis_features(panel)
    model_df = panel[["life_satisfaction"] + features].dropna() if "life_satisfaction" in panel.columns else pd.DataFrame()
    if len(model_df) < 10 or len(features) < 2 or model_df["life_satisfaction"].nunique() < 2:
        out = pd.DataFrame(
            [
                {
                    "feature": "",
                    "importance_mean": np.nan,
                    "importance_std": np.nan,
                    "status": "not_run",
                    "note": "모델링에 필요한 target/feature/표본 수가 부족해 permutation importance를 계산하지 않았다.",
                }
            ]
        )
        out.to_csv(Path(tables_dir) / "09_permutation_importance.csv", index=False, encoding="utf-8-sig")
        return out

    x = model_df[features]
    y = model_df["life_satisfaction"]
    model = RandomForestRegressor(n_estimators=300, random_state=42, min_samples_leaf=2)
    model.fit(x, y)
    result = permutation_importance(model, x, y, n_repeats=30, random_state=42)
    out = pd.DataFrame(
        {
            "feature": features,
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std,
            "status": "calculated",
            "note": "EDA 보조용 변수 중요도다. 인과관계나 예측 성능으로 과장하지 않는다.",
        }
    ).sort_values("importance_mean", ascending=False)
    out.to_csv(Path(tables_dir) / "09_permutation_importance.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(9, 5))
    sns.barplot(data=out, x="importance_mean", y="feature", color="#2F6F73")
    plt.title("Permutation importance")
    plt.xlabel("중요도 평균")
    plt.ylabel("고용 변수")
    save_plot(Path(figures_dir) / "09_permutation_importance.png")
    return out


def choose_conclusion(correlation_summary: pd.DataFrame, importance: pd.DataFrame, panel: pd.DataFrame) -> tuple[str, str]:
    if "life_satisfaction" not in panel.columns or panel["life_satisfaction"].notna().sum() < 10:
        return "C", "삶의 만족도 target 또는 표본 수가 부족해 고용 지표와의 관계를 충분히 검증할 수 없다."
    calculated = correlation_summary[correlation_summary["status"] == "calculated"] if "status" in correlation_summary.columns else pd.DataFrame()
    strong_count = int((calculated["abs_max_correlation"] >= 0.5).sum()) if not calculated.empty else 0
    moderate_count = int((calculated["abs_max_correlation"] >= 0.3).sum()) if not calculated.empty else 0
    if strong_count >= 3:
        return "A", "여러 고용 지표에서 비교적 큰 상관관계가 관찰된다. 다만 인과관계로 해석하지 않는다."
    if moderate_count >= 1:
        return "B", "일부 고용 지표에서 삶의 만족도와 관련이 있을 가능성이 관찰된다."
    return "C", "고용 지표만으로 삶의 만족도 차이를 충분히 설명한다고 보기 어렵다."


def write_report_summary(
    panel: pd.DataFrame,
    missing_raw: pd.DataFrame,
    diagnostics: dict[str, pd.DataFrame],
    feature_log: pd.DataFrame,
    gap_summary: pd.DataFrame,
    correlation_summary: pd.DataFrame,
    importance: pd.DataFrame,
    output_dir: str | Path,
) -> Path:
    output_dir = Path(output_dir)
    conclusion_code, conclusion_text = choose_conclusion(correlation_summary, importance, panel)
    years = sorted(panel["year"].dropna().astype(int).unique().tolist()) if "year" in panel.columns and not panel.empty else []
    feature_availability = feature_log[["feature", "status"]].drop_duplicates() if not feature_log.empty and {"feature", "status"}.issubset(feature_log.columns) else pd.DataFrame()
    available_required = [feature for feature in REQUIRED_EMPLOYMENT_FEATURES if feature in panel.columns and panel[feature].notna().any()]
    partial = diagnostics.get("partial_2026_diagnostics", pd.DataFrame())
    partial_note = "2026년 부분자료 진단 결과 없음" if partial.empty else f"2026년 부분자료 파일 수: {int(partial['is_2026_likely_partial'].sum())}"
    corr_top = correlation_summary[correlation_summary["status"] == "calculated"].head(5) if "status" in correlation_summary.columns else pd.DataFrame()
    imp_top = importance[importance["status"] == "calculated"].head(5) if "status" in importance.columns else pd.DataFrame()

    report = [
        "# KOSIS 삶의 만족도-고용 EDA 요약",
        "",
        "## 1. 분석 목적",
        "본 분석은 KOSIS의 삶의 만족도 자료와 고용 관련 지역 통계를 결합하여, 수도권과 비수도권 간 삶의 만족도 차이가 고용 여건과 어떤 관련을 갖는지 탐색하는 것을 목적으로 한다.",
        "",
        "## 2. 데이터 진단 결과",
        f"- 분석 기간: {min(years) if years else '계산 불가'}~{max(years) if years else '계산 불가'}",
        "- 사용한 지역 단위: 17개 시도, 수도권은 서울·경기·인천으로 정의",
        f"- 사용 가능한 필수 고용 변수: {', '.join(available_required) if available_required else '없음'}",
        f"- 결측 및 2026년 부분자료 여부: {partial_note}",
        f"- 병합 과정에서 제외/불일치된 데이터: `outputs/tables/05_merge_failed_rows.csv` 참고",
        "",
        "## 3. 삶의 만족도 차이",
        "- `life_satisfaction` target이 충분히 존재할 때만 수도권/비수도권 차이와 추세를 해석한다.",
        "- 현재 target이 없거나 부족하면 차이 존재 여부를 판단하지 않는다.",
        "",
        "## 4. 고용 지표의 차이",
        f"- 생성 가능한 고용 변수는 `{', '.join(available_required) if available_required else '없음'}`이다.",
        "- 고용률·실업률·경제활동참가율 원자료가 없으면 해당 변수는 생성 불가로 기록하며, 값을 추정하지 않는다.",
        "- 취업자 수 기반 변수는 전체 취업자 대비 비율로 바꾼 경우에만 구조 비교용으로 사용한다.",
        "",
        "## 5. 삶의 만족도와 고용 변수의 관계",
    ]
    if corr_top.empty:
        report.append("- 계산 가능한 상관관계가 없다. target 또는 고용 변수 표본이 부족하다.")
    else:
        for _, row in corr_top.iterrows():
            report.append(f"- {row['group']} / {row['feature']}: Pearson={row['pearson_r']:.3f}, Spearman={row['spearman_r']:.3f}, n={int(row['n'])}")
        report.append("- p-value는 표본 수가 작을 수 있으므로 탐색적으로만 해석한다.")
    report.extend(
        [
            "",
            "## 6. 보조 모델링 결과",
        ]
    )
    if imp_top.empty:
        report.append("- permutation importance를 계산하지 않았다. target/feature/표본 수가 부족하다.")
    else:
        for _, row in imp_top.iterrows():
            report.append(f"- {row['feature']}: importance_mean={row['importance_mean']:.4f}")
        report.append("- 이 결과는 인과관계가 아니라 탐색적 변수 중요도다.")
    report.extend(
        [
            "",
            "## 7. 결론",
            f"선택 결론: {conclusion_code}. {conclusion_text}",
            "",
            "이 결론은 현재 데이터에 근거한 자동 요약이다. 상관관계를 인과관계로 해석하지 않으며, 삶의 만족도 target 또는 핵심 고용률 지표가 부족한 경우 추가 데이터 확보가 필요하다.",
        ]
    )
    path = output_dir / "report_summary.md"
    path.write_text("\n".join(report), encoding="utf-8")
    return path


def run_full_eda_pipeline(repo_root: str | Path) -> dict[str, Any]:
    """Run steps 1-10 end to end and return key objects for notebook display."""
    dirs = setup_environment(repo_root)
    raw_datasets, missing_raw = load_raw_data(dirs["raw"], include_optional=True, discover_extra=True, tables_dir=dirs["tables"])
    diagnostics = diagnose_raw_files(raw_datasets, dirs["tables"], EXPECTED_YEARS)
    data_diagnosis = write_data_diagnosis(raw_datasets, missing_raw, diagnostics, dirs["tables"])
    standardized, column_mapping, mapping_errors = standardize_all(raw_datasets, dirs["domain_processed"], dirs["tables"])
    feature_frames, feature_log = build_feature_frames(standardized, dirs["domain_processed"], dirs["tables"])
    panel, merge_summary = merge_feature_frames(feature_frames, dirs["processed"], dirs["tables"])
    life_summary = write_life_satisfaction_summary(panel, dirs["tables"])
    viz_log = generate_core_visualizations(panel, dirs["tables"], dirs["figures"])
    gap_summary = metro_gap_analysis(panel, dirs["tables"], dirs["figures"])
    corr_summary = correlation_analysis(panel, dirs["tables"])
    importance = permutation_importance_analysis(panel, dirs["tables"], dirs["figures"])
    report_path = write_report_summary(panel, missing_raw, diagnostics, feature_log, gap_summary, corr_summary, importance, dirs["domain_root"] / "outputs")
    return {
        "dirs": dirs,
        "raw_datasets": raw_datasets,
        "missing_raw": missing_raw,
        "diagnostics": diagnostics,
        "data_diagnosis": data_diagnosis,
        "standardized": standardized,
        "column_mapping": column_mapping,
        "mapping_errors": mapping_errors,
        "feature_frames": feature_frames,
        "feature_log": feature_log,
        "panel": panel,
        "merge_summary": merge_summary,
        "life_summary": life_summary,
        "viz_log": viz_log,
        "gap_summary": gap_summary,
        "correlation_summary": corr_summary,
        "importance": importance,
        "report_path": report_path,
    }
