# 팀 공유용 발표 흐름

## 1. 원본 데이터 확인

보여줄 파일:

- `data/raw/employment_wage/employment_region_age.csv`
- `data/raw/employment_wage/employment_region_sex.csv`
- `data/raw/employment_wage/employment_status.csv`
- `data/raw/employment_wage/employment_hours.csv`

말할 내용:

> KOSIS에서 받은 고용 원본 CSV를 지역, 연도, 성별, 연령, 종사상지위, 취업시간 기준으로 정리했다.

## 2. 데이터 진단

보여줄 표/그래프:

- `employment_wage/outputs/tables/01_year_coverage.csv`
- `employment_wage/outputs/tables/01_partial_2026_diagnostics.csv`
- `employment_wage/outputs/figures/eda_01_year_region_coverage.png`
- `employment_wage/outputs/figures/eda_02_partial_2026_periods.png`

말할 내용:

> 현재 데이터는 2016~2026 전체 장기 패널이 아니라 2025~2026 중심이며, 2026년은 부분자료로 해석해야 한다.

## 3. 전처리와 feature 생성

보여줄 표:

- `employment_wage/outputs/tables/04_employment_feature_availability.csv`
- `employment_wage/outputs/tables/10_employment_qol_proxy_metric_assumptions.csv`

말할 내용:

> 고용률, 실업률 같은 실제 rate 변수는 현재 원본에 없어 생성하지 않았고, 대신 취업자 구성비와 종사상지위/취업시간 비율로 고용 여건 proxy를 만들었다.

## 4. 분석용 데이터셋

보여줄 표:

- `data/processed/kosis_life_quality_employment_panel.csv`
- `employment_wage/outputs/tables/10_employment_qol_proxy_panel.csv`

말할 내용:

> 모든 feature는 year x region 단위로 맞췄고, 서울/경기/인천은 수도권, 나머지는 비수도권으로 분류했다.

## 5. 메인 결론

보여줄 그래프:

- `employment_wage/outputs/figures/10_employment_qol_proxy_score_trend_metro.png`

말할 내용:

> 고용 여건 proxy 기준으로 수도권 평균 점수가 비수도권보다 높게 관찰된다.

## 6. 결론의 근거 분해

보여줄 그래프:

- `employment_wage/outputs/figures/10_employment_qol_proxy_component_gap.png`

말할 내용:

> 수도권의 proxy 우위는 임금근로자 비중, 청년층 취업자 비중, 자영업자 비율, 단시간 취업자 비율, 남녀 취업자 구성비 격차에서 주로 나온다.

## 7. 지역별 차이

보여줄 그래프:

- `employment_wage/outputs/figures/10_employment_qol_proxy_region_ranking_2026.png`
- `employment_wage/outputs/figures/10_employment_qol_proxy_heatmap_2026.png`

말할 내용:

> 수도권/비수도권 평균 차이뿐 아니라 시도별 편차도 크다. 다만 2026년은 부분자료라 확정 순위로 말하지 않는다.

## 8. 한계와 다음 단계

말할 내용:

> 이 분석은 실제 삶의 만족도 분석이 아니라 고용 구조 기반 proxy 분석이다. 다음 단계에서는 삶의 만족도 원자료와 주거, 건강, 교육, 문화, 안전, 소득 변수를 결합해야 한다.
