"""
주거 데이터 EDA (탐색적 데이터 분석)
출처: KOSIS (국가통계포털)
기준연도: 2024
주제: 거주지역 × 성별 × 연령대별 주택 소유 현황
담당: 다빈
"""

import codecs
import os
import warnings
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")
matplotlib.use("Agg")

# ─── 한글 폰트 설정 ──────────────────────────────────────────────────────────
def set_korean_font():
    candidates = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            prop = fm.FontProperties(fname=path)
            plt.rcParams["font.family"] = prop.get_name()
            plt.rcParams["axes.unicode_minus"] = False
            print(f"폰트 설정: {prop.get_name()}")
            return
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False
    print("경고: 한글 폰트를 찾지 못했습니다. 기본 폰트를 사용합니다.")

set_korean_font()

BASE   = "/Users/imdabin/Desktop/socialInteligence/housing"
VIZ    = os.path.join(BASE, "viz")
os.makedirs(VIZ, exist_ok=True)

# ─── 파일 이름 정리 (rename) ─────────────────────────────────────────────────
RENAME_MAP = {
    "거주지역_가구주의_성_연령대별_주택소유_가구수_20260506154428.csv":   "주택소유_가구수.csv",
    "거주지역_가구주의_성_연령대별_무주택_가구수_20260506154634.csv":    "무주택_가구수.csv",
    "거주지역_가구주의_성_연령대별_아파트소유_가구수_20260506154537.csv": "아파트소유_가구수.csv",
    "거주지역_성_연령대별_주택소유자수_20260506154511.csv":             "주택소유자수.csv",
    "_1인가구_거주지역_가구주의_성_연령대별_주택소유_가구수_20260506154609.csv": "1인가구_주택소유_가구수.csv",
}
for old, new in RENAME_MAP.items():
    src = os.path.join(BASE, old)
    dst = os.path.join(BASE, new)
    if os.path.exists(src) and not os.path.exists(dst):
        os.rename(src, dst)
        print(f"  이름 변경: {old}  →  {new}")

# ─── 파싱 유틸 ───────────────────────────────────────────────────────────────
AGE_GROUPS = ["총계", "30세미만", "30~39세", "40~49세", "50~59세", "60~69세", "70~79세", "80세이상"]
REGIONS_16 = ["서울특별시","부산광역시","대구광역시","인천광역시","광주광역시","대전광역시",
               "울산광역시","세종특별자치시","경기도","강원특별자치도","충청북도","충청남도",
               "전북특별자치도","전라남도","경상북도","경상남도","제주특별자치도"]


def parse_housing_csv(filename: str, has_deceased: bool = False) -> pd.DataFrame:
    """
    3-행 헤더(연도/성별/연령대) + 지역 데이터를 tidy long-format으로 변환.
    has_deceased=True 이면 마지막 연령 컬럼이 '사망자'임.
    """
    path = os.path.join(BASE, filename)
    with codecs.open(path, "r", "euc-kr") as f:
        lines = [l.rstrip("\n\r") for l in f.readlines()]

    age_cols = AGE_GROUPS + (["사망자"] if has_deceased else [])
    n_age    = len(age_cols)                # 8 or 9
    genders  = ["총계", "남자", "여자"]

    rows = []
    for line in lines[3:]:                   # 헤더 3행 건너뜀
        parts = line.split(",")
        region = parts[0].strip('"').strip()
        if not region:
            continue
        vals = [v.strip('"').strip() for v in parts[1:]]

        for gi, gender in enumerate(genders):
            for ai, age in enumerate(age_cols):
                idx = gi * n_age + ai
                if idx < len(vals):
                    raw = vals[idx].replace(",", "")
                    try:
                        value = int(raw)
                    except ValueError:
                        value = np.nan
                    rows.append({
                        "지역":   region,
                        "성별":   gender,
                        "연령대": age,
                        "값":     value,
                    })

    df = pd.DataFrame(rows)
    return df


# ─── 데이터 로드 ─────────────────────────────────────────────────────────────
print("\n[1] 데이터 로드 중...")

df_own    = parse_housing_csv("주택소유_가구수.csv")
df_no     = parse_housing_csv("무주택_가구수.csv")
df_apt    = parse_housing_csv("아파트소유_가구수.csv")
df_owner  = parse_housing_csv("주택소유자수.csv", has_deceased=True)
df_single = parse_housing_csv("1인가구_주택소유_가구수.csv")

# 레이블 추가
df_own["유형"]    = "주택소유_가구수"
df_no["유형"]     = "무주택_가구수"
df_apt["유형"]    = "아파트소유_가구수"
df_owner["유형"]  = "주택소유자수"
df_single["유형"] = "1인가구_주택소유"

df_all = pd.concat([df_own, df_no, df_apt, df_owner, df_single], ignore_index=True)

# 전국 / 지역 분리
df_national = df_all[df_all["지역"] == "전국"].copy()
df_region   = df_all[df_all["지역"] != "전국"].copy()

# 주요 분석용: 성별·연령대 '총계'만 (지역별 합계)
df_reg_total = df_region[
    (df_region["성별"]   == "총계") &
    (df_region["연령대"] == "총계")
].copy()

print(f"  전체 레코드 수: {len(df_all):,}")
print(f"  데이터 포함 지역: {df_region['지역'].nunique()}개")
print(f"  유형: {df_all['유형'].unique().tolist()}")

# 분석용 피벗 테이블 ─ 지역 × 유형
pivot_region = df_reg_total.pivot_table(
    index="지역", columns="유형", values="값", aggfunc="sum"
).rename_axis(None, axis=1)

pivot_region["주택소유율(%)"] = (
    pivot_region["주택소유_가구수"] /
    (pivot_region["주택소유_가구수"] + pivot_region["무주택_가구수"]) * 100
).round(1)
pivot_region["아파트비율(%)"] = (
    pivot_region["아파트소유_가구수"] / pivot_region["주택소유_가구수"] * 100
).round(1)

print("\n[2] 지역별 주요 지표:")
print(pivot_region[["주택소유_가구수","무주택_가구수","주택소유율(%)","아파트비율(%)"]].to_string())

# ─── 시각화 공통 설정 ────────────────────────────────────────────────────────
PALETTE_GEN  = {"남자": "#4C72B0", "여자": "#DD8452", "총계": "#55A868"}
PALETTE_BLUE = "Blues_r"
FIG_DPI      = 150


def save(fig, name):
    path = os.path.join(VIZ, name)
    fig.savefig(path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  저장: viz/{name}")


# ═══════════════════════════════════════════════════════════════════════════════
# 그림 1 ─ 지역별 주택소유율 수평 막대 (전국 강조)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[3] 시각화 생성 중...")

fig, ax = plt.subplots(figsize=(10, 7))
data_sorted = pivot_region["주택소유율(%)"].sort_values()
colors = ["#E63946" if r == "전국" else "#457B9D" for r in data_sorted.index]
bars = ax.barh(data_sorted.index, data_sorted.values, color=colors)
ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=8)
ax.set_xlabel("주택소유율 (%)")
ax.set_title("2024년 거주지역별 주택소유율\n(소유가구 / (소유+무주택) 가구)", pad=12)
ax.axvline(data_sorted.get("전국", 0), color="#E63946", linestyle="--", linewidth=1, alpha=0.6, label="전국")
ax.legend()
ax.set_xlim(0, 80)
fig.tight_layout()
save(fig, "01_지역별_주택소유율.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 그림 2 ─ 지역별 아파트 비율 (소유 주택 중 아파트 비중)
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 7))
data_apt = pivot_region["아파트비율(%)"].sort_values()
bars = ax.barh(data_apt.index, data_apt.values, color="#2A9D8F")
ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=8)
ax.set_xlabel("아파트 비율 (%)")
ax.set_title("2024년 거주지역별 아파트 소유 비율\n(아파트 소유 가구 / 주택 소유 가구)", pad=12)
ax.set_xlim(0, 90)
fig.tight_layout()
save(fig, "02_지역별_아파트소유비율.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 그림 3 ─ 연령대별 주택소유 vs 무주택 (전국·총계)
# ═══════════════════════════════════════════════════════════════════════════════
df_nat_age = df_national[
    (df_national["성별"]   == "총계") &
    (df_national["연령대"] != "총계") &
    (df_national["연령대"] != "사망자") &
    (df_national["유형"].isin(["주택소유_가구수","무주택_가구수"]))
].copy()

age_order = ["30세미만","30~39세","40~49세","50~59세","60~69세","70~79세","80세이상"]
df_nat_age["연령대"] = pd.Categorical(df_nat_age["연령대"], categories=age_order, ordered=True)
df_nat_age = df_nat_age.sort_values("연령대")

fig, ax = plt.subplots(figsize=(10, 6))
pivot_age = df_nat_age.pivot_table(index="연령대", columns="유형", values="값")
pivot_age.plot(kind="bar", ax=ax, color=["#E07B54","#4A90D9"], width=0.65)
ax.set_xlabel("연령대")
ax.set_ylabel("가구 수 (만 가구)")
ax.set_title("2024년 연령대별 주택소유 vs 무주택 가구 수 (전국)", pad=12)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/10000:.0f}만"))
ax.legend(["무주택_가구수","주택소유_가구수"], title="구분")
ax.tick_params(axis="x", rotation=30)
fig.tight_layout()
save(fig, "03_연령대별_주택소유vs무주택.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 그림 4 ─ 성별 × 연령대별 주택소유 가구수 (전국)
# ═══════════════════════════════════════════════════════════════════════════════
df_nat_gen = df_national[
    (df_national["성별"]   != "총계") &
    (df_national["연령대"] != "총계") &
    (df_national["연령대"] != "사망자") &
    (df_national["유형"] == "주택소유_가구수")
].copy()
df_nat_gen["연령대"] = pd.Categorical(df_nat_gen["연령대"], categories=age_order, ordered=True)
df_nat_gen = df_nat_gen.sort_values("연령대")

fig, ax = plt.subplots(figsize=(10, 6))
for gender, grp in df_nat_gen.groupby("성별"):
    ax.plot(grp["연령대"].astype(str), grp["값"] / 10000,
            marker="o", linewidth=2, label=gender, color=PALETTE_GEN[gender])
ax.set_xlabel("연령대")
ax.set_ylabel("가구 수 (만 가구)")
ax.set_title("2024년 성별 × 연령대별 주택소유 가구수 (전국)", pad=12)
ax.legend(title="성별")
ax.tick_params(axis="x", rotation=30)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
save(fig, "04_성별_연령대별_주택소유.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 그림 5 ─ 성별 주택소유율 (남/여 비교, 연령대별) — 전국
# ═══════════════════════════════════════════════════════════════════════════════
df_gen_own = df_national[
    (df_national["성별"]   != "총계") &
    (df_national["연령대"] != "총계") &
    (df_national["연령대"] != "사망자") &
    (df_national["유형"].isin(["주택소유_가구수","무주택_가구수"]))
].pivot_table(index=["성별","연령대"], columns="유형", values="값").reset_index()
df_gen_own["연령대"] = pd.Categorical(df_gen_own["연령대"], categories=age_order, ordered=True)
df_gen_own["소유율(%)"] = (df_gen_own["주택소유_가구수"] /
                           (df_gen_own["주택소유_가구수"] + df_gen_own["무주택_가구수"]) * 100).round(1)
df_gen_own = df_gen_own.sort_values("연령대")

fig, ax = plt.subplots(figsize=(10, 6))
for gender, grp in df_gen_own.groupby("성별"):
    ax.plot(grp["연령대"].astype(str), grp["소유율(%)"],
            marker="o", linewidth=2.5, label=gender, color=PALETTE_GEN[gender])
ax.set_xlabel("연령대")
ax.set_ylabel("주택소유율 (%)")
ax.set_title("2024년 성별 × 연령대별 주택소유율 (전국)", pad=12)
ax.legend(title="성별")
ax.tick_params(axis="x", rotation=30)
ax.grid(axis="y", alpha=0.3)
ax.set_ylim(0, 80)
fig.tight_layout()
save(fig, "05_성별_연령대별_주택소유율.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 그림 6 ─ 지역별 × 성별 주택소유 가구수 히트맵
# ═══════════════════════════════════════════════════════════════════════════════
df_hm = df_region[
    (df_region["유형"]   == "주택소유_가구수") &
    (df_region["성별"]   != "총계") &
    (df_region["연령대"] == "총계")
].pivot_table(index="지역", columns="성별", values="값")

fig, ax = plt.subplots(figsize=(8, 9))
sns.heatmap(df_hm / 10000, annot=True, fmt=".0f", cmap="YlOrRd",
            ax=ax, cbar_kws={"label": "만 가구"}, linewidths=0.5)
ax.set_title("2024년 지역 × 성별 주택소유 가구수 (만 가구)", pad=12)
ax.set_xlabel("성별")
ax.set_ylabel("")
fig.tight_layout()
save(fig, "06_지역별_성별_주택소유_히트맵.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 그림 7 ─ 지역별 × 연령대별 주택소유 가구수 히트맵
# ═══════════════════════════════════════════════════════════════════════════════
df_hm2 = df_region[
    (df_region["유형"]   == "주택소유_가구수") &
    (df_region["성별"]   == "총계") &
    (df_region["연령대"] != "총계")
].copy()
df_hm2["연령대"] = pd.Categorical(df_hm2["연령대"], categories=age_order, ordered=True)
df_hm2 = df_hm2.pivot_table(index="지역", columns="연령대", values="값")
df_hm2 = df_hm2.reindex(columns=age_order)

fig, ax = plt.subplots(figsize=(12, 9))
sns.heatmap(df_hm2 / 10000, annot=True, fmt=".0f", cmap="Blues",
            ax=ax, cbar_kws={"label": "만 가구"}, linewidths=0.5)
ax.set_title("2024년 지역 × 연령대별 주택소유 가구수 (만 가구)", pad=12)
ax.set_xlabel("연령대")
ax.set_ylabel("")
ax.tick_params(axis="x", rotation=30)
fig.tight_layout()
save(fig, "07_지역별_연령대별_주택소유_히트맵.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 그림 8 ─ 1인가구 주택소유 vs 전체 주택소유 (지역별)
# ═══════════════════════════════════════════════════════════════════════════════
df_sing_reg = df_region[
    (df_region["유형"]   == "1인가구_주택소유") &
    (df_region["성별"]   == "총계") &
    (df_region["연령대"] == "총계")
].set_index("지역")["값"].rename("1인가구_소유")

df_all_reg = df_region[
    (df_region["유형"]   == "주택소유_가구수") &
    (df_region["성별"]   == "총계") &
    (df_region["연령대"] == "총계")
].set_index("지역")["값"].rename("전체_소유")

df_sing_cmp = pd.concat([df_sing_reg, df_all_reg], axis=1).dropna()
df_sing_cmp["1인가구비율(%)"] = (df_sing_cmp["1인가구_소유"] / df_sing_cmp["전체_소유"] * 100).round(1)
df_sing_cmp = df_sing_cmp.sort_values("1인가구비율(%)")

fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.barh(df_sing_cmp.index, df_sing_cmp["1인가구비율(%)"], color="#6A4C93")
ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=8)
ax.set_xlabel("1인가구 소유 비율 (%)")
ax.set_title("2024년 지역별 1인가구 주택소유 비율\n(1인가구 소유 / 전체 소유 가구)", pad=12)
ax.set_xlim(0, 30)
fig.tight_layout()
save(fig, "08_지역별_1인가구_소유비율.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 그림 9 ─ 상관관계: 지역별 주요 지표 산점도 + 회귀선
# ═══════════════════════════════════════════════════════════════════════════════
df_corr = pivot_region.copy()
df_corr["1인가구비율(%)"] = df_sing_cmp["1인가구비율(%)"]
df_corr = df_corr.dropna()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# 주택소유율 vs 아파트비율
ax = axes[0]
r, p = stats.pearsonr(df_corr["주택소유율(%)"], df_corr["아파트비율(%)"])
sns.regplot(data=df_corr, x="주택소유율(%)", y="아파트비율(%)",
            ax=ax, scatter_kws={"s": 60, "color": "#457B9D"},
            line_kws={"color": "#E63946"})
for region, row in df_corr.iterrows():
    ax.annotate(region, (row["주택소유율(%)"], row["아파트비율(%)"]),
                fontsize=6.5, ha="center", va="bottom")
ax.set_title(f"주택소유율 vs 아파트비율\n(r={r:.2f}, p={p:.3f})", pad=8)

# 주택소유율 vs 1인가구비율
ax = axes[1]
r2, p2 = stats.pearsonr(df_corr["주택소유율(%)"], df_corr["1인가구비율(%)"])
sns.regplot(data=df_corr, x="주택소유율(%)", y="1인가구비율(%)",
            ax=ax, scatter_kws={"s": 60, "color": "#2A9D8F"},
            line_kws={"color": "#E63946"})
for region, row in df_corr.iterrows():
    ax.annotate(region, (row["주택소유율(%)"], row["1인가구비율(%)"]),
                fontsize=6.5, ha="center", va="bottom")
ax.set_title(f"주택소유율 vs 1인가구비율\n(r={r2:.2f}, p={p2:.3f})", pad=8)

fig.suptitle("2024년 지역별 주요 지표 상관관계", fontsize=13, y=1.02)
fig.tight_layout()
save(fig, "09_지역별_지표_상관관계.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 그림 10 ─ 지역별 주요 지표 종합 대시보드
# ═══════════════════════════════════════════════════════════════════════════════
df_dash = df_region[
    (df_region["성별"]   == "총계") &
    (df_region["연령대"] == "총계") &
    (df_region["유형"].isin(["주택소유_가구수","무주택_가구수","아파트소유_가구수"]))
].pivot_table(index="지역", columns="유형", values="값").reset_index()

df_dash["소유율(%)"] = (df_dash["주택소유_가구수"] /
                        (df_dash["주택소유_가구수"] + df_dash["무주택_가구수"]) * 100).round(1)
df_dash["아파트비율(%)"] = (df_dash["아파트소유_가구수"] / df_dash["주택소유_가구수"] * 100).round(1)
df_dash = df_dash.sort_values("소유율(%)", ascending=False)

fig, axes = plt.subplots(1, 3, figsize=(16, 7))

# 주택소유 가구수
ax = axes[0]
ax.barh(df_dash["지역"], df_dash["주택소유_가구수"] / 10000, color="#457B9D")
ax.set_xlabel("만 가구")
ax.set_title("주택소유 가구수")

# 주택소유율
ax = axes[1]
bars = ax.barh(df_dash["지역"], df_dash["소유율(%)"], color="#2A9D8F")
ax.bar_label(bars, fmt="%.1f%%", padding=2, fontsize=7.5)
ax.set_xlabel("%")
ax.set_title("주택소유율")
ax.set_xlim(0, 75)

# 아파트비율
ax = axes[2]
bars = ax.barh(df_dash["지역"], df_dash["아파트비율(%)"], color="#E9C46A")
ax.bar_label(bars, fmt="%.1f%%", padding=2, fontsize=7.5)
ax.set_xlabel("%")
ax.set_title("아파트소유 비율")
ax.set_xlim(0, 80)

for ax in axes[1:]:
    ax.set_yticklabels([])

fig.suptitle("2024년 거주지역별 주거 지표 종합 대시보드", fontsize=14, fontweight="bold", y=1.01)
fig.tight_layout()
save(fig, "10_지역별_종합_대시보드.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 그림 11 ─ 성별 × 연령대 소유율 히트맵 (전국)
# ═══════════════════════════════════════════════════════════════════════════════
df_pivot_gen_age_own = df_national[
    (df_national["성별"]   != "총계") &
    (df_national["연령대"] != "총계") &
    (df_national["연령대"] != "사망자") &
    (df_national["유형"].isin(["주택소유_가구수","무주택_가구수"]))
].pivot_table(index="성별", columns="연령대", values="값", aggfunc="sum")

df_pivot_gen_age_own_rate = pd.DataFrame()
for age in age_order:
    if age in df_pivot_gen_age_own.columns:
        df_pivot_gen_age_own_rate[age] = df_pivot_gen_age_own.get(age, 0)

# 소유율 계산 (유형별로 분리)
own_by_gen_age = df_national[
    (df_national["성별"]   != "총계") &
    (df_national["연령대"] != "총계") &
    (df_national["연령대"] != "사망자") &
    (df_national["유형"].isin(["주택소유_가구수","무주택_가구수"]))
].pivot_table(index=["성별","연령대"], columns="유형", values="값").reset_index()
own_by_gen_age["연령대"] = pd.Categorical(own_by_gen_age["연령대"], categories=age_order, ordered=True)
own_by_gen_age["소유율"] = (own_by_gen_age["주택소유_가구수"] /
                             (own_by_gen_age["주택소유_가구수"] + own_by_gen_age["무주택_가구수"]) * 100).round(1)
hm_rate = own_by_gen_age.pivot_table(index="성별", columns="연령대", values="소유율")
hm_rate = hm_rate.reindex(columns=age_order)

fig, ax = plt.subplots(figsize=(10, 3.5))
sns.heatmap(hm_rate, annot=True, fmt=".1f", cmap="RdYlGn",
            ax=ax, cbar_kws={"label": "소유율 (%)"}, linewidths=0.8,
            vmin=10, vmax=70)
ax.set_title("2024년 성별 × 연령대별 주택소유율 (%) — 전국", pad=10)
ax.set_xlabel("연령대")
ax.set_ylabel("성별")
ax.tick_params(axis="x", rotation=30)
fig.tight_layout()
save(fig, "11_성별_연령대_소유율_히트맵.png")

# ═══════════════════════════════════════════════════════════════════════════════
# 그림 12 ─ 지역 × 연령대 × 성별 소유율 — 수도권 vs 비수도권 비교
# ═══════════════════════════════════════════════════════════════════════════════
METRO     = ["서울특별시","경기도","인천광역시"]
NON_METRO = [r for r in REGIONS_16 if r not in METRO]

def region_group_rate(regions, label):
    sub = df_region[
        (df_region["지역"].isin(regions)) &
        (df_region["성별"]   != "총계") &
        (df_region["연령대"] != "총계") &
        (df_region["유형"].isin(["주택소유_가구수","무주택_가구수"]))
    ].groupby(["성별","연령대","유형"])["값"].sum().reset_index()
    sub2 = sub.pivot_table(index=["성별","연령대"], columns="유형", values="값").reset_index()
    sub2.columns.name = None
    sub2["소유율"] = (sub2["주택소유_가구수"] /
                      (sub2["주택소유_가구수"] + sub2["무주택_가구수"]) * 100).round(1)
    sub2["권역"] = label
    return sub2

df_m   = region_group_rate(METRO,     "수도권")
df_nm  = region_group_rate(NON_METRO, "비수도권")
df_cmp = pd.concat([df_m, df_nm])
df_cmp["연령대"] = pd.Categorical(df_cmp["연령대"], categories=age_order, ordered=True)
df_cmp = df_cmp.sort_values("연령대")

fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
for ax, gender in zip(axes, ["남자","여자"]):
    sub = df_cmp[df_cmp["성별"] == gender]
    for 권역, grp in sub.groupby("권역"):
        color = "#E63946" if 권역 == "수도권" else "#457B9D"
        ax.plot(grp["연령대"].astype(str), grp["소유율"],
                marker="o", linewidth=2, label=권역, color=color)
    ax.set_title(f"{gender} — 수도권 vs 비수도권 주택소유율")
    ax.set_xlabel("연령대")
    ax.set_ylabel("주택소유율 (%)")
    ax.tick_params(axis="x", rotation=30)
    ax.legend(title="권역")
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, 75)

fig.suptitle("2024년 수도권 vs 비수도권 성별·연령대별 주택소유율 비교", fontsize=13, y=1.02)
fig.tight_layout()
save(fig, "12_수도권vs비수도권_성별_연령대_소유율.png")

# ─── 상관관계 수치 요약 ────────────────────────────────────────────────────────
print("\n[4] 상관관계 분석 요약")
print("=" * 55)
corr_vars = ["주택소유율(%)","아파트비율(%)"]
if "1인가구비율(%)" in df_corr.columns:
    corr_vars.append("1인가구비율(%)")
print(df_corr[corr_vars].corr().round(3).to_string())

print("\n[5] 지역별 주요 통계")
print("=" * 55)
summary = df_corr[corr_vars].describe().round(1)
print(summary.to_string())

print(f"\n✅  완료! 시각화 {len(os.listdir(VIZ))}개가 housing/viz/ 에 저장되었습니다.")
