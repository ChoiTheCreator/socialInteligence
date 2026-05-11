# 고용-삶의 질 EDA Evidence Map

이 폴더는 팀원에게 `원본 데이터 -> 전처리 -> 분석용 데이터 -> 관찰된 결론 -> 근거 그래프` 흐름을 설명하기 위한 인덱스다.

현재 데이터에는 실제 삶의 만족도 값이 없으므로, 결론은 `삶의 만족도`가 아니라 `고용 여건 기반 삶의 질 proxy`에 대한 관찰로 제한한다.

## 1. 분석 흐름

```text
KOSIS raw CSV
  -> 컬럼 표준화: year, region, value
  -> 지역 정규화: 17개 시도
  -> 수도권 분류: 서울/경기/인천 = 수도권
  -> year x region 단위 feature 생성
  -> 고용 proxy 점수 생성
  -> 수도권/비수도권 비교
  -> 결론별 표/그래프 연결
```

## 2. 데이터 위치

| 단계 | 파일 |
|---|---|
| 원본 고용 데이터 | `data/raw/employment_wage/*.csv` |
| 삶의 만족도 원자료 자리 | `data/raw/life_quality/.gitkeep` |
| 도메인별 전처리 산출물 | `data/processed/employment_wage/` |
| 최종 분석 패널 | `data/processed/kosis_life_quality_employment_panel.csv` |
| 고용 proxy 분석 패널 | `employment_wage/outputs/tables/10_employment_qol_proxy_panel.csv` |
| 발표용 요약문 | `employment_wage/outputs/employment_qol_proxy_analysis.md` |

## 3. 발표에 가장 먼저 쓸 그래프

| 우선순위 | 그래프 | 용도 |
|---:|---|---|
| 1 | `employment_wage/outputs/figures/10_employment_qol_proxy_score_trend_metro.png` | 수도권/비수도권 proxy 점수 차이 제시 |
| 2 | `employment_wage/outputs/figures/10_employment_qol_proxy_component_gap.png` | 차이를 만든 고용 지표 설명 |
| 3 | `employment_wage/outputs/figures/10_employment_qol_proxy_region_ranking_2026.png` | 2026년 시도별 순위 제시 |
| 4 | `employment_wage/outputs/figures/10_employment_qol_proxy_heatmap_2026.png` | 지역별 분포를 한 화면에서 제시 |

## 4. 결론별 Evidence Map

| ID | 관찰된 결론 또는 추측 | 근거 표 | 근거 그래프 | 발표 문장 |
|---|---|---|---|---|
| E1 | 현재 데이터만으로는 실제 삶의 만족도와 고용의 관계를 검증할 수 없다. | `data/processed/employment_wage/03_target_life_satisfaction_not_created.csv`, `employment_wage/outputs/tables/04_employment_feature_availability.csv` | 없음 | "삶의 만족도 원자료가 아직 없기 때문에 이번 결과는 실제 삶의 만족도 분석이 아니라 고용 여건 proxy 분석이다." |
| E2 | 원본 데이터는 2016~2026 전체가 아니라 2025~2026 중심이며, 2026년은 부분자료로 봐야 한다. | `employment_wage/outputs/tables/01_year_coverage.csv`, `employment_wage/outputs/tables/01_partial_2026_diagnostics.csv` | `employment_wage/outputs/figures/eda_01_year_region_coverage.png`, `employment_wage/outputs/figures/eda_02_partial_2026_periods.png` | "현재 고용 데이터의 시간 범위는 제한적이어서 장기 추세보다 최근 구조 비교로 해석해야 한다." |
| E3 | 고용 proxy 평균 점수는 수도권이 비수도권보다 높게 관찰된다. | `employment_wage/outputs/tables/10_employment_qol_proxy_metro_summary.csv`, `employment_wage/outputs/tables/10_employment_qol_proxy_metro_year.csv` | `employment_wage/outputs/figures/10_employment_qol_proxy_score_trend_metro.png` | "고용 여건 proxy 기준으로는 수도권이 비수도권보다 유리하게 관찰된다." |
| E4 | 수도권 우위는 임금근로자 비중, 청년층 취업자 비중, 자영업자 비율, 단시간 취업자 비율, 남녀 취업자 구성비 격차에서 주로 나온다. | `employment_wage/outputs/tables/10_employment_qol_proxy_component_gap.csv` | `employment_wage/outputs/figures/10_employment_qol_proxy_component_gap.png` | "격차는 단일 지표가 아니라 고용 안정성, 청년 고용, 노동시간 proxy가 함께 만든 결과로 보인다." |
| E5 | 비수도권이 모든 지표에서 불리한 것은 아니다. 임시근로자와 일용근로자 비율은 비수도권이 약간 낮게 관찰된다. | `employment_wage/outputs/tables/10_employment_qol_proxy_component_gap.csv` | `employment_wage/outputs/figures/10_employment_qol_proxy_component_gap.png` | "수도권 우위라고 단순화하기보다, 지표별로 방향이 다르다는 점을 같이 보여줘야 한다." |
| E6 | 2026년 지역별 proxy 점수는 세종, 서울, 대전, 부산, 경기 등이 높고 전남, 경북, 전북 등이 낮게 관찰된다. | `employment_wage/outputs/tables/10_employment_qol_proxy_region_ranking_2026.csv` | `employment_wage/outputs/figures/10_employment_qol_proxy_region_ranking_2026.png`, `employment_wage/outputs/figures/10_employment_qol_proxy_heatmap_2026.png` | "수도권/비수도권 평균 차이 외에도 시도별 편차가 크다." |

## 5. 발표 결론 문장

현재 보유한 고용 원본 데이터만 기준으로 보면, 수도권은 임금근로자 비중과 청년층 취업자 비중이 높고 자영업자 및 단시간 취업자 비율이 낮아 `고용 여건 기반 삶의 질 proxy`가 비수도권보다 높게 관찰된다.

다만 실제 삶의 만족도 원자료가 아직 없으므로, 이 결과는 삶의 만족도 차이를 검증한 결론이 아니라 고용 구조 차이에 기반한 탐색적 추측이다. 후속 분석에서는 삶의 만족도, 주거, 건강, 교육, 문화, 안전, 소득 변수를 결합해야 한다.
