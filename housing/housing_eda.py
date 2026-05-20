"""
주거 데이터 EDA (탐색적 데이터 분석)
출처: KOSIS (국가통계포털) — 2024년 실데이터 기반
더미 생성: 2016~2026 Q1 시계열 시뮬레이션
담당: 다빈
"""

import codecs, os, warnings, random
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")
matplotlib.use("Agg")
random.seed(42)
np.random.seed(42)

# ─── 한글 폰트 ────────────────────────────────────────────────────────────────
def set_korean_font():
    for path in ["/System/Library/Fonts/AppleSDGothicNeo.ttc",
                 "/Library/Fonts/AppleGothic.ttf",
                 "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"]:
        if os.path.exists(path):
            prop = fm.FontProperties(fname=path)
            plt.rcParams["font.family"] = prop.get_name()
            plt.rcParams["axes.unicode_minus"] = False
            return
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False

set_korean_font()

BASE = "/Users/imdabin/Desktop/socialInteligence/housing"
VIZ  = os.path.join(BASE, "viz")
os.makedirs(VIZ, exist_ok=True)

# ─── 상수 ─────────────────────────────────────────────────────────────────────
AGE_GROUPS = ["30세미만", "30~39세", "40~49세", "50~59세", "60~69세", "70~79세", "80세이상"]
GENDERS    = ["남자", "여자"]
REGIONS    = ["서울특별시","부산광역시","대구광역시","인천광역시","광주광역시","대전광역시",
              "울산광역시","세종특별자치시","경기도","강원특별자치도","충청북도","충청남도",
              "전북특별자치도","전라남도","경상북도","경상남도","제주특별자치도"]

# 연도: 2016~2025(연간) + 2026Q1
YEARS = list(range(2016, 2026)) + ["2026Q1"]

def save(fig, name):
    path = os.path.join(VIZ, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  저장: viz/{name}")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. 2024 실데이터 로드
# ═══════════════════════════════════════════════════════════════════════════════
def parse_csv_2024(filename: str, has_deceased: bool = False) -> pd.DataFrame:
    path = os.path.join(BASE, filename)
    with codecs.open(path, "r", "euc-kr") as f:
        lines = [l.rstrip("\n\r") for l in f.readlines()]

    age_cols = AGE_GROUPS + (["사망자"] if has_deceased else [])
    n_age    = len(age_cols)
    rows = []
    for line in lines[3:]:
        parts  = line.split(",")
        region = parts[0].strip('"').strip()
        if not region:
            continue
        vals = [v.strip('"').strip() for v in parts[1:]]
        for gi, gender in enumerate(["총계", "남자", "여자"]):
            for ai, age in enumerate(age_cols):
                idx = gi * n_age + ai
                raw = vals[idx].replace(",", "") if idx < len(vals) else ""
                try:
                    value = int(raw)
                except ValueError:
                    value = np.nan
                rows.append({"지역": region, "성별": gender, "연령대": age, "값": value})
    return pd.DataFrame(rows)

print("[1] 2024 실데이터 로드...")
df_own24   = parse_csv_2024("주택소유_가구수.csv")
df_no24    = parse_csv_2024("무주택_가구수.csv")
df_apt24   = parse_csv_2024("아파트소유_가구수.csv")
df_s24     = parse_csv_2024("1인가구_주택소유_가구수.csv")

# 지역별 성별 연령대별 2024 기준값 추출 (총가구=소유+무주택)
base_own = df_own24[(df_own24["성별"] != "총계") & (~df_own24["연령대"].isin(["총계","사망자"]))].copy()
base_no  = df_no24 [(df_no24 ["성별"] != "총계") & (~df_no24 ["연령대"].isin(["총계","사망자"]))].copy()
base_apt = df_apt24[(df_apt24["성별"] != "총계") & (~df_apt24["연령대"].isin(["총계","사망자"]))].copy()
base_s   = df_s24  [(df_s24  ["성별"] != "총계") & (~df_s24  ["연령대"].isin(["총계","사망자"]))].copy()

base_own = base_own[base_own["지역"] != "전국"]
base_no  = base_no [base_no ["지역"] != "전국"]
base_apt = base_apt[base_apt["지역"] != "전국"]
base_s   = base_s  [base_s  ["지역"] != "전국"]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. 더미 시계열 생성 (2016~2026Q1)
# ═══════════════════════════════════════════════════════════════════════════════
print("[2] 더미 시계열 생성 (2016~2026Q1)...")

# 연도 인덱스 (2024=0 기준)
def year_delta(yr):
    if yr == "2026Q1":
        return 2026.25 - 2024
    return yr - 2024

# 지역별 연간 트렌드 팩터 (현실 반영)
#  - 서울: 소유율 꾸준히 하락 (집값↑), 아파트비율 안정적
#  - 세종: 신도시 성장 → 총가구 빠르게 증가
#  - 비수도권: 소유율 완만 상승 후 유지
REGION_OWN_TREND = {   # 연간 소유율 변화 (pp/year, 2016→2024 기준)
    "서울특별시":  -0.35, "경기도": -0.15, "인천광역시": -0.10,
    "부산광역시":  -0.05, "대구광역시": -0.05,
    "세종특별자치시": 0.40,
    "강원특별자치도": 0.10, "충청북도": 0.10, "충청남도": 0.10,
    "전북특별자치도": 0.05, "전라남도": 0.05,
    "경상북도": 0.05,  "경상남도": 0.05,
    "광주광역시": -0.05, "대전광역시": -0.05,
    "울산광역시":  0.10, "제주특별자치도": -0.10,
}
# 연령대별 청년층 소유율 하락 가속
AGE_OWN_TREND = {
    "30세미만": -0.25, "30~39세": -0.30,
    "40~49세":  -0.05, "50~59세":  0.05,
    "60~69세":   0.10, "70~79세":  0.10, "80세이상": 0.05,
}
# 아파트 비율 매년 소폭 상승
APT_GROWTH = 0.008   # 연 0.8%p 상승

def make_factor(region, age, yr, gender):
    """2024 실데이터 → 연도 yr 시뮬레이션 스케일 팩터"""
    d = year_delta(yr)
    own_shift = (REGION_OWN_TREND.get(region, 0) + AGE_OWN_TREND.get(age, 0)) * d / 100
    noise     = np.random.normal(0, 0.008)   # ±0.8% 노이즈
    return max(0.50, 1 + own_shift + noise)

rows_ts = []

for yr in YEARS:
    if yr == 2024:
        # 실데이터 그대로
        for _, r in base_own.iterrows():
            rows_ts.append({"연도": yr, "지역": r["지역"], "성별": r["성별"],
                            "연령대": r["연령대"], "유형": "주택소유_가구수", "값": r["값"]})
        for _, r in base_no.iterrows():
            rows_ts.append({"연도": yr, "지역": r["지역"], "성별": r["성별"],
                            "연령대": r["연령대"], "유형": "무주택_가구수", "값": r["값"]})
        for _, r in base_apt.iterrows():
            rows_ts.append({"연도": yr, "지역": r["지역"], "성별": r["성별"],
                            "연령대": r["연령대"], "유형": "아파트소유_가구수", "값": r["값"]})
        for _, r in base_s.iterrows():
            rows_ts.append({"연도": yr, "지역": r["지역"], "성별": r["성별"],
                            "연령대": r["연령대"], "유형": "1인가구_주택소유", "값": r["값"]})
        continue

    # 더미: 2024 기준 팩터 적용
    for _, r in base_own.iterrows():
        f = make_factor(r["지역"], r["연령대"], yr, r["성별"])
        # 세종 신도시 성장 반영: 2016년 가구 자체가 적었음
        세종_growth = 1.0
        if r["지역"] == "세종특별자치시":
            세종_growth = max(0.1, 1 - 0.12 * (2024 - (yr if yr != "2026Q1" else 2026.25)))
        val = max(0, int(r["값"] * f * 세종_growth + np.random.normal(0, r["값"] * 0.01)))
        rows_ts.append({"연도": yr, "지역": r["지역"], "성별": r["성별"],
                        "연령대": r["연령대"], "유형": "주택소유_가구수", "값": val})

    for _, r in base_no.iterrows():
        f_inv = 2 - make_factor(r["지역"], r["연령대"], yr, r["성별"])  # 소유↓ → 무주택↑
        f_inv = max(0.7, f_inv)
        val = max(0, int(r["값"] * f_inv + np.random.normal(0, r["값"] * 0.01)))
        rows_ts.append({"연도": yr, "지역": r["지역"], "성별": r["성별"],
                        "연령대": r["연령대"], "유형": "무주택_가구수", "값": val})

    for _, r in base_apt.iterrows():
        d   = year_delta(yr)
        apt_f = 1 + APT_GROWTH * d + np.random.normal(0, 0.005)
        val = max(0, int(r["값"] * max(0.5, apt_f) + np.random.normal(0, r["값"] * 0.01)))
        rows_ts.append({"연도": yr, "지역": r["지역"], "성별": r["성별"],
                        "연령대": r["연령대"], "유형": "아파트소유_가구수", "값": val})

    for _, r in base_s.iterrows():
        f = make_factor(r["지역"], r["연령대"], yr, r["성별"])
        val = max(0, int(r["값"] * f + np.random.normal(0, r["값"] * 0.01)))
        rows_ts.append({"연도": yr, "지역": r["지역"], "성별": r["성별"],
                        "연령대": r["연령대"], "유형": "1인가구_주택소유", "값": val})

df_ts = pd.DataFrame(rows_ts)
# 연도를 표시용 레이블로 변환
df_ts["연도_label"] = df_ts["연도"].apply(lambda y: str(y) if y != "2026Q1" else "2026Q1")

print(f"  시계열 레코드 수: {len(df_ts):,}  (연도 수: {df_ts['연도'].nunique()})")

# 편의 집계
def agg(df, 유형, 성별="총계", 연령대=None, 지역=None):
    sub = df[df["유형"] == 유형].copy()
    if 성별 != "ALL":
        sub = sub[sub["성별"] == 성별]
    if 연령대:
        sub = sub[sub["연령대"] == 연령대]
    if 지역:
        sub = sub[sub["지역"].isin(지역 if isinstance(지역, list) else [지역])]
    return sub.groupby("연도")["값"].sum().reset_index()

YEAR_LABELS = [str(y) if y != "2026Q1" else "2026Q1" for y in YEARS]
YEAR_INTS   = [y if y != "2026Q1" else 2026.25 for y in YEARS]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. 시각화
# ═══════════════════════════════════════════════════════════════════════════════
print("[3] 시각화 생성 중...")

# ── 그림 01: 전국 연도별 주택소유 vs 무주택 가구 수 ─────────────────────────
own_nat  = agg(df_ts, "주택소유_가구수", 성별="ALL")
no_nat   = agg(df_ts, "무주택_가구수",   성별="ALL")
merged   = own_nat.merge(no_nat, on="연도", suffixes=("_own","_no"))
merged["소유율(%)"] = (merged["값_own"] / (merged["값_own"] + merged["값_no"]) * 100).round(1)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
labels = [str(y) for y in merged["연도"]]
x      = range(len(labels))
ax1.bar(x, merged["값_own"] / 1e6, label="주택소유", color="#457B9D", alpha=0.85)
ax1.bar(x, merged["값_no"]  / 1e6, bottom=merged["값_own"] / 1e6,
        label="무주택", color="#E07B54", alpha=0.85)
ax1.set_ylabel("가구 수 (백만)")
ax1.set_title("2016~2026Q1 전국 주택소유 vs 무주택 가구 수 추이", pad=10)
ax1.legend()
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}M"))
ax2.plot(x, merged["소유율(%)"], marker="o", color="#2A9D8F", linewidth=2)
ax2.set_ylabel("주택소유율 (%)")
ax2.set_xlabel("연도")
ax2.set_xticks(list(x))
ax2.set_xticklabels(labels, rotation=30, ha="right")
ax2.legend()
ax2.grid(axis="y", alpha=0.3)
fig.tight_layout()
save(fig, "01_전국_연도별_소유vs무주택.png")

# ── 그림 02: 지역별 연도별 주택소유율 히트맵 ────────────────────────────────
rows_rate = []
for yr in YEARS:
    sub = df_ts[df_ts["연도"] == yr]
    for reg in REGIONS:
        own_v = sub[(sub["유형"] == "주택소유_가구수") & (sub["지역"] == reg)]["값"].sum()
        no_v  = sub[(sub["유형"] == "무주택_가구수")   & (sub["지역"] == reg)]["값"].sum()
        tot   = own_v + no_v
        rows_rate.append({"연도": str(yr), "지역": reg,
                          "소유율": round(own_v / tot * 100, 1) if tot > 0 else np.nan})

df_rate = pd.DataFrame(rows_rate)
hm = df_rate.pivot_table(index="지역", columns="연도", values="소유율")
hm = hm.reindex(columns=[str(y) for y in YEARS])

fig, ax = plt.subplots(figsize=(16, 8))
sns.heatmap(hm, annot=True, fmt=".1f", cmap="RdYlGn", ax=ax,
            cbar_kws={"label": "소유율 (%)"}, linewidths=0.3,
            vmin=40, vmax=70)
ax.set_title("2016~2026Q1 지역별 주택소유율 히트맵 (%)", pad=12)
ax.set_xlabel("연도")
ax.set_ylabel("")
ax.tick_params(axis="x", rotation=30)
fig.tight_layout()
save(fig, "02_지역별_연도별_소유율_히트맵.png")

# ── 그림 03: 주요 지역 연도별 소유율 추세선 ─────────────────────────────────
HIGHLIGHT = ["서울특별시","경기도","부산광역시","울산광역시","세종특별자치시","전라남도"]
COLORS    = ["#E63946","#457B9D","#2A9D8F","#E9C46A","#6A4C93","#F4A261"]

fig, ax = plt.subplots(figsize=(12, 6))
for reg, col in zip(HIGHLIGHT, COLORS):
    sub = df_rate[df_rate["지역"] == reg].sort_values("연도")
    ax.plot(sub["연도"], sub["소유율"], marker="o", linewidth=2, label=reg, color=col)
ax.set_xlabel("연도")
ax.set_ylabel("주택소유율 (%)")
ax.set_title("주요 지역 주택소유율 연도별 추이 (2016~2026Q1)", pad=10)
ax.legend(loc="upper right", fontsize=8)
ax.tick_params(axis="x", rotation=30)
ax.grid(axis="y", alpha=0.3)
ax.set_ylim(30, 75)
fig.tight_layout()
save(fig, "03_주요지역_소유율_추이.png")

# ── 그림 04: 연령대별 연도별 주택소유율 추이 (전국) ─────────────────────────
rows_age = []
for yr in YEARS:
    sub = df_ts[df_ts["연도"] == yr]
    for age in AGE_GROUPS:
        own_v = sub[(sub["유형"] == "주택소유_가구수") & (sub["연령대"] == age)]["값"].sum()
        no_v  = sub[(sub["유형"] == "무주택_가구수")   & (sub["연령대"] == age)]["값"].sum()
        tot   = own_v + no_v
        rows_age.append({"연도": str(yr), "연령대": age,
                         "소유율": round(own_v / tot * 100, 1) if tot > 0 else np.nan})
df_age_ts = pd.DataFrame(rows_age)

fig, ax = plt.subplots(figsize=(12, 6))
palette = sns.color_palette("tab10", len(AGE_GROUPS))
for age, col in zip(AGE_GROUPS, palette):
    sub = df_age_ts[df_age_ts["연령대"] == age].sort_values("연도")
    ax.plot(sub["연도"], sub["소유율"], marker="o", linewidth=2, label=age, color=col)
ax.set_xlabel("연도")
ax.set_ylabel("주택소유율 (%)")
ax.set_title("연령대별 주택소유율 연도별 추이 (2016~2026Q1)", pad=10)
ax.legend(title="연령대", fontsize=8, loc="center right")
ax.tick_params(axis="x", rotation=30)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
save(fig, "04_연령대별_소유율_추이.png")

# ── 그림 05: 성별 연도별 소유율 추이 (전국) ──────────────────────────────────
rows_gen = []
for yr in YEARS:
    sub = df_ts[df_ts["연도"] == yr]
    for gender in GENDERS:
        own_v = sub[(sub["유형"] == "주택소유_가구수") & (sub["성별"] == gender)]["값"].sum()
        no_v  = sub[(sub["유형"] == "무주택_가구수")   & (sub["성별"] == gender)]["값"].sum()
        tot   = own_v + no_v
        rows_gen.append({"연도": str(yr), "성별": gender,
                         "소유율": round(own_v / tot * 100, 1) if tot > 0 else np.nan})
df_gen_ts = pd.DataFrame(rows_gen)

fig, ax = plt.subplots(figsize=(12, 5))
PALETTE_GEN = {"남자": "#4C72B0", "여자": "#DD8452"}
for gender in GENDERS:
    sub = df_gen_ts[df_gen_ts["성별"] == gender].sort_values("연도")
    ax.plot(sub["연도"], sub["소유율"], marker="o", linewidth=2.5,
            label=gender, color=PALETTE_GEN[gender])
ax.fill_between(
    df_gen_ts[df_gen_ts["성별"] == "남자"].sort_values("연도")["연도"],
    df_gen_ts[df_gen_ts["성별"] == "남자"].sort_values("연도")["소유율"],
    df_gen_ts[df_gen_ts["성별"] == "여자"].sort_values("연도")["소유율"],
    alpha=0.1, color="purple", label="성별 격차"
)
ax.set_xlabel("연도")
ax.set_ylabel("주택소유율 (%)")
ax.set_title("성별 주택소유율 연도별 추이 (2016~2026Q1)", pad=10)
ax.legend()
ax.tick_params(axis="x", rotation=30)
ax.grid(axis="y", alpha=0.3)
ax.set_ylim(45, 80)
fig.tight_layout()
save(fig, "05_성별_소유율_추이.png")

# ── 그림 06: 아파트 비율 연도별 추이 (지역별) ──────────────────────────────
rows_apt = []
for yr in YEARS:
    sub = df_ts[df_ts["연도"] == yr]
    for reg in REGIONS:
        own_v = sub[(sub["유형"] == "주택소유_가구수")  & (sub["지역"] == reg)]["값"].sum()
        apt_v = sub[(sub["유형"] == "아파트소유_가구수") & (sub["지역"] == reg)]["값"].sum()
        rows_apt.append({"연도": str(yr), "지역": reg,
                         "아파트비율": round(apt_v / own_v * 100, 1) if own_v > 0 else np.nan})
df_apt_ts = pd.DataFrame(rows_apt)

hm_apt = df_apt_ts.pivot_table(index="지역", columns="연도", values="아파트비율")
hm_apt = hm_apt.reindex(columns=[str(y) for y in YEARS])

fig, ax = plt.subplots(figsize=(16, 8))
sns.heatmap(hm_apt, annot=True, fmt=".1f", cmap="Blues", ax=ax,
            cbar_kws={"label": "아파트 비율 (%)"}, linewidths=0.3)
ax.set_title("2016~2026Q1 지역별 아파트소유 비율 히트맵 (%)\n(소유 가구 중 아파트 비중)", pad=12)
ax.tick_params(axis="x", rotation=30)
fig.tight_layout()
save(fig, "06_지역별_아파트비율_히트맵.png")

# ── 그림 07: 청년층(30세미만+30대) 소유율 vs 중장년층(50대+) 소유율 추이 ──
YOUNG  = ["30세미만","30~39세"]
MIDDLE = ["50~59세","60~69세"]

rows_ym = []
for yr in YEARS:
    sub = df_ts[df_ts["연도"] == yr]
    for group, ages in [("청년층(30대 이하)", YOUNG), ("중장년층(50~60대)", MIDDLE)]:
        own_v = sub[(sub["유형"] == "주택소유_가구수") & (sub["연령대"].isin(ages))]["값"].sum()
        no_v  = sub[(sub["유형"] == "무주택_가구수")   & (sub["연령대"].isin(ages))]["값"].sum()
        tot   = own_v + no_v
        rows_ym.append({"연도": str(yr), "그룹": group,
                        "소유율": round(own_v / tot * 100, 1) if tot > 0 else np.nan})
df_ym = pd.DataFrame(rows_ym)

fig, ax = plt.subplots(figsize=(12, 5))
for grp, col in zip(["청년층(30대 이하)","중장년층(50~60대)"], ["#E63946","#457B9D"]):
    sub = df_ym[df_ym["그룹"] == grp].sort_values("연도")
    ax.plot(sub["연도"], sub["소유율"], marker="o", linewidth=2.5, label=grp, color=col)
ax.set_xlabel("연도")
ax.set_ylabel("주택소유율 (%)")
ax.set_title("청년층 vs 중장년층 주택소유율 격차 추이 (2016~2026Q1)", pad=10)
ax.legend()
ax.tick_params(axis="x", rotation=30)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
save(fig, "07_청년vs중장년_소유율_격차.png")

# ── 그림 08: 수도권 vs 비수도권 소유율 추이 ─────────────────────────────────
METRO     = ["서울특별시","경기도","인천광역시"]
NON_METRO = [r for r in REGIONS if r not in METRO]

rows_mv = []
for yr in YEARS:
    sub = df_ts[df_ts["연도"] == yr]
    for label, regs in [("수도권", METRO), ("비수도권", NON_METRO)]:
        own_v = sub[(sub["유형"] == "주택소유_가구수") & (sub["지역"].isin(regs))]["값"].sum()
        no_v  = sub[(sub["유형"] == "무주택_가구수")   & (sub["지역"].isin(regs))]["값"].sum()
        tot   = own_v + no_v
        rows_mv.append({"연도": str(yr), "권역": label,
                        "소유율": round(own_v / tot * 100, 1) if tot > 0 else np.nan})
df_mv = pd.DataFrame(rows_mv)

fig, ax = plt.subplots(figsize=(12, 5))
for area, col in [("수도권","#E63946"), ("비수도권","#457B9D")]:
    sub = df_mv[df_mv["권역"] == area].sort_values("연도")
    ax.plot(sub["연도"], sub["소유율"], marker="o", linewidth=2.5, label=area, color=col)
ax.fill_between(
    df_mv[df_mv["권역"] == "비수도권"].sort_values("연도")["연도"],
    df_mv[df_mv["권역"] == "수도권"].sort_values("연도")["소유율"],
    df_mv[df_mv["권역"] == "비수도권"].sort_values("연도")["소유율"],
    alpha=0.1, color="gray", label="격차"
)
ax.set_xlabel("연도")
ax.set_ylabel("주택소유율 (%)")
ax.set_title("수도권 vs 비수도권 주택소유율 추이 (2016~2026Q1)", pad=10)
ax.legend()
ax.tick_params(axis="x", rotation=30)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
save(fig, "08_수도권vs비수도권_추이.png")

# ── 그림 09: 지역 × 성별 소유율 — 연도별 남녀 격차 히트맵 ──────────────────
# 남자 소유율 - 여자 소유율 (격차) 를 연도 × 지역으로 시각화
SELECT_YEARS = [2016, 2018, 2020, 2022, 2024, "2026Q1"]

rows_gap_yr = []
for yr in SELECT_YEARS:
    sub = df_ts[df_ts["연도"] == yr]
    for reg in REGIONS:
        for gender in GENDERS:
            own_v = sub[(sub["유형"] == "주택소유_가구수") &
                        (sub["지역"] == reg) & (sub["성별"] == gender)]["값"].sum()
            no_v  = sub[(sub["유형"] == "무주택_가구수") &
                        (sub["지역"] == reg) & (sub["성별"] == gender)]["값"].sum()
            tot   = own_v + no_v
            rows_gap_yr.append({"연도": str(yr), "지역": reg, "성별": gender,
                                 "소유율": round(own_v / tot * 100, 1) if tot > 0 else np.nan})

df_gap_yr = pd.DataFrame(rows_gap_yr)
df_gap_piv = df_gap_yr.pivot_table(index=["지역","연도"], columns="성별", values="소유율").reset_index()
df_gap_piv["남녀격차"] = df_gap_piv["남자"] - df_gap_piv["여자"]
hm_gap = df_gap_piv.pivot_table(index="지역", columns="연도", values="남녀격차")
hm_gap = hm_gap.reindex(columns=[str(y) for y in SELECT_YEARS])

fig, ax = plt.subplots(figsize=(11, 9))
sns.heatmap(hm_gap, annot=True, fmt=".1f", cmap="PuOr_r", ax=ax,
            cbar_kws={"label": "남자 - 여자 소유율 격차 (pp)"},
            linewidths=0.5, center=0)
ax.set_title("지역 × 연도별 성별 주택소유율 격차 (남자 − 여자, pp)\n(2016~2026Q1 주요 연도)", pad=12)
ax.set_xlabel("연도")
ax.set_ylabel("")
fig.tight_layout()
save(fig, "09_지역_연도별_성별격차_히트맵.png")

# ── 그림 10: 주요 지표 상관관계 — 연도별 패널 (4개 연도) ────────────────────
PANEL_YEARS = [2016, 2019, 2022, 2024]
PALETTE_10  = ["#A8DADC", "#457B9D", "#1D3557", "#E63946"]

fig, axes = plt.subplots(2, 2, figsize=(14, 11))
axes = axes.flatten()

for ax, yr, col in zip(axes, PANEL_YEARS, PALETTE_10):
    sub_yr = df_ts[df_ts["연도"] == yr]
    rows_c = []
    for reg in REGIONS:
        s = sub_yr[sub_yr["지역"] == reg]
        own_v = s[s["유형"] == "주택소유_가구수"]["값"].sum()
        no_v  = s[s["유형"] == "무주택_가구수"]["값"].sum()
        apt_v = s[s["유형"] == "아파트소유_가구수"]["값"].sum()
        s_v   = s[s["유형"] == "1인가구_주택소유"]["값"].sum()
        tot   = own_v + no_v
        rows_c.append({
            "지역":          reg,
            "주택소유율(%)":  round(own_v / tot * 100, 1) if tot > 0 else np.nan,
            "아파트비율(%)":  round(apt_v / own_v * 100, 1) if own_v > 0 else np.nan,
            "1인가구비율(%)": round(s_v / own_v * 100, 1) if own_v > 0 else np.nan,
        })
    df_c = pd.DataFrame(rows_c).dropna()
    r, p = stats.pearsonr(df_c["주택소유율(%)"], df_c["아파트비율(%)"])
    sns.regplot(data=df_c, x="주택소유율(%)", y="아파트비율(%)", ax=ax,
                scatter_kws={"s": 55, "color": col, "alpha": 0.85},
                line_kws={"color": "gray", "linewidth": 1.2})
    for _, row in df_c.iterrows():
        ax.annotate(row["지역"], (row["주택소유율(%)"], row["아파트비율(%)"]),
                    fontsize=6, ha="center", va="bottom", color="#333333")
    ax.set_title(f"{yr}년  (r = {r:.2f}, p = {p:.3f})", fontsize=11)
    ax.set_xlabel("주택소유율 (%)")
    ax.set_ylabel("아파트비율 (%)")
    ax.set_xlim(40, 72)
    ax.set_ylim(35, 95)
    ax.grid(alpha=0.2)

fig.suptitle("연도별 지역 주택소유율 vs 아파트비율 상관관계 (2016·2019·2022·2024)",
             fontsize=13, fontweight="bold", y=1.01)
fig.tight_layout()
save(fig, "10_연도별_지표_상관관계_패널.png")

# ── 그림 11: 연도별 성별 격차 변화 (남-여 소유율 차이) ──────────────────────
df_gap = df_gen_ts.pivot_table(index="연도", columns="성별", values="소유율").reset_index()
df_gap["격차(남-여)"] = df_gap["남자"] - df_gap["여자"]

fig, ax = plt.subplots(figsize=(12, 4))
bars = ax.bar(df_gap["연도"], df_gap["격차(남-여)"], color="#6A4C93", alpha=0.8)
ax.set_xlabel("연도")
ax.set_ylabel("남녀 소유율 격차 (pp)")
ax.set_title("연도별 남녀 주택소유율 격차 추이 (2016~2026Q1)", pad=10)
ax.tick_params(axis="x", rotation=30)
ax.grid(axis="y", alpha=0.3)
ax.legend()
fig.tight_layout()
save(fig, "11_연도별_성별격차.png")

# ── 그림 12: 연령대 × 연도 소유율 히트맵 (전국) ──────────────────────────────
hm_age = df_age_ts.pivot_table(index="연령대", columns="연도", values="소유율")
age_order = ["30세미만","30~39세","40~49세","50~59세","60~69세","70~79세","80세이상"]
hm_age = hm_age.reindex(index=age_order, columns=[str(y) for y in YEARS])

fig, ax = plt.subplots(figsize=(14, 5))
sns.heatmap(hm_age, annot=True, fmt=".1f", cmap="RdYlGn", ax=ax,
            cbar_kws={"label": "소유율 (%)"}, linewidths=0.4, vmin=5, vmax=75)
ax.set_title("연령대 × 연도별 주택소유율 히트맵 (%) — 전국", pad=12)
ax.tick_params(axis="x", rotation=30)
fig.tight_layout()
save(fig, "12_연령대_연도_소유율_히트맵.png")

# ─── 상관관계 요약 출력 ───────────────────────────────────────────────────────
print("\n[4] 연도별 지표 상관관계 (주택소유율 vs 아파트비율)")
print("=" * 45)
for yr in PANEL_YEARS:
    sub_yr = df_ts[df_ts["연도"] == yr]
    rows_c = []
    for reg in REGIONS:
        s = sub_yr[sub_yr["지역"] == reg]
        own_v = s[s["유형"] == "주택소유_가구수"]["값"].sum()
        no_v  = s[s["유형"] == "무주택_가구수"]["값"].sum()
        apt_v = s[s["유형"] == "아파트소유_가구수"]["값"].sum()
        tot   = own_v + no_v
        rows_c.append({"주택소유율": round(own_v/tot*100,1) if tot>0 else np.nan,
                        "아파트비율": round(apt_v/own_v*100,1) if own_v>0 else np.nan})
    df_c = pd.DataFrame(rows_c).dropna()
    r, p = stats.pearsonr(df_c["주택소유율"], df_c["아파트비율"])
    print(f"  {yr}년: r = {r:.3f}, p = {p:.3f}")

print("\n[5] 연도별 전국 주택소유율 요약")
print("=" * 45)
for _, row in merged.iterrows():
    print(f"  {row['연도']}: {row['소유율(%)']:.1f}%")

print(f"\n✅ 완료! 시각화 {len(os.listdir(VIZ))}개 → housing/viz/")
