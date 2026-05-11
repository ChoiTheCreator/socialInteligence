# KOSIS 삶의 질-고용 EDA 1~4단계 요약

작성일: 2026-05-11  
분석 범위: 데이터 로드, 기본 진단, 컬럼 표준화, 지역명 정규화, 수도권/비수도권 구분, `year × region` 패널 생성

## 1. 결론 요약

현재 확보된 데이터만으로는 삶의 만족도와 고용 요인의 관계 분석을 진행하기 어렵다. 이유는 `life_satisfaction.csv`가 아직 없고, 고용 데이터도 2016~2026 전체가 아니라 2025~2026 일부 기간만 포함하기 때문이다.

다만 고용 관련 원본 CSV는 정상적으로 읽혔고, 17개 시도 기준으로 지역명이 정규화되었으며, 수도권/비수도권 구분과 `year × region` 단위 고용 feature 패널은 생성되었다.

최종 패널:

- 파일: [`../../data/processed/kosis_life_quality_employment_panel.csv`](../../data/processed/kosis_life_quality_employment_panel.csv)
- 크기: `34 rows × 39 columns`
- 단위: `year × region`
- 기간: `2025~2026`
- 지역: 17개 시도
- target: `life_satisfaction`은 현재 전부 결측

## 2. 데이터 로드 진단

로드된 고용 데이터:

| file_key | 상태 | 비고 |
|---|---|---|
| `employment_region_sex` | 로드됨 | 성별 취업자 수 |
| `employment_region_age` | 로드됨 | 연령별 취업자 수 |
| `employment_status` | 로드됨 | 종사상지위별 취업자 수 |
| `employment_hours` | 로드됨 | 취업시간별 취업자 수 |
| `employment_region_sex_age` | 로드됨 | 성 × 연령별 취업자 수, 참고용 |
| `life_satisfaction` | 없음 | target 생성 불가 |

진단 파일:

- [`tables/01_missing_raw_files.csv`](tables/01_missing_raw_files.csv)
- [`tables/01_file_diagnostics.csv`](tables/01_file_diagnostics.csv)
- [`tables/01_duplicate_rows.csv`](tables/01_duplicate_rows.csv)

### 진단

삶의 만족도 원본은 다음 위치에 아직 없다.

```text
data/raw/life_quality/life_satisfaction.csv
```

따라서 최종 패널의 `life_satisfaction`과 `life_satisfaction_period_count`는 모두 결측이다.

### 가설

현재 상태에서 5단계 이후의 target 분포, 상관관계, 수도권/비수도권 삶의 만족도 차이 분석을 진행하면 분석 대상이 없어 해석이 불가능하다.

### 처방

삶의 만족도 원본 CSV를 `data/raw/life_quality/life_satisfaction.csv`로 추가한 뒤 1~4단계를 다시 실행해야 한다.

## 3. 기간 및 2026년 부분자료 진단

현재 고용 데이터는 2016~2026 전체 기간을 포함하지 않는다.

| file_key | 포함 연도 | 누락 연도 | 2026 포함 여부 |
|---|---:|---|---|
| `employment_region_sex` | 2025, 2026 | 2016~2024 | 포함 |
| `employment_region_age` | 2025, 2026 | 2016~2024 | 포함 |
| `employment_status` | 2025, 2026 | 2016~2024 | 포함 |
| `employment_hours` | 2025, 2026 | 2016~2024 | 포함 |
| `employment_region_sex_age` | 2025, 2026 | 2016~2024 | 포함 |

2026년 부분자료 진단:

| file_key | 2026 기간 수 | 완전 연간 기준 | 2026 부분자료 여부 |
|---|---:|---:|---|
| `employment_region_sex` | 3개월 | 12개월 | 부분자료 |
| `employment_region_age` | 3개월 | 12개월 | 부분자료 |
| `employment_status` | 3개월 | 12개월 | 부분자료 |
| `employment_hours` | 3개월 | 12개월 | 부분자료 |
| `employment_region_sex_age` | 1분기 | 4분기 | 부분자료 |

진단 파일:

- [`tables/01_year_coverage.csv`](tables/01_year_coverage.csv)
- [`tables/01_partial_2026_diagnostics.csv`](tables/01_partial_2026_diagnostics.csv)

### 진단

2026년은 연간 자료가 아니라 `2026.01~2026.03` 또는 `2026.1/4`만 포함한다.

### 가설

2026년 값을 다른 연도와 같은 연평균으로 비교하면 계절성, 경기 변동, 조사 시점 차이 때문에 왜곡될 가능성이 있다.

### 처방

후속 EDA에서는 2026년을 다음 중 하나로 처리하는 것이 적절하다.

- 2026년 제외 후 2025년만 임시 점검
- 2026년을 `partial_year=True`로 flag 처리
- 2026년 전체 월/분기 자료를 확보한 뒤 비교

## 4. 컬럼 표준화 및 지역명 정규화 결과

KOSIS wide 형식의 시점 컬럼을 long 형식으로 변환했고, 다음 표준 컬럼을 생성했다.

- `year`
- `source_period`
- `period_type`
- `month`
- `quarter`
- `region`
- `metro_area`
- `value`

지역명은 17개 시도 기준으로 정규화했다.

수도권 기준:

- 수도권: 서울, 경기, 인천
- 비수도권: 그 외 14개 시도

진단 파일:

- [`tables/02_column_mapping_summary.csv`](tables/02_column_mapping_summary.csv)
- [`tables/02_column_mapping_errors.csv`](tables/02_column_mapping_errors.csv)
- [`tables/02_region_mapping_issues.csv`](tables/02_region_mapping_issues.csv)
- [`tables/02_preprocessing_missing_summary.csv`](tables/02_preprocessing_missing_summary.csv)

### 진단

현재 컬럼 매핑 오류는 없었다. 지역 coverage도 2025년과 2026년 모두 17개 시도로 맞춰졌다.

### 가설

지역명 표준화와 수도권/비수도권 구분은 후속 분석에서 집단 비교와 panel merge의 기본 키로 사용할 수 있다.

### 처방

추가 KOSIS 파일을 넣을 때도 동일한 표준화 함수로 처리하고, `02_column_mapping_errors.csv`가 비어 있는지 먼저 확인한다.

## 5. Feature 생성 결과

현재 원본은 고용률, 실업률, 경제활동참가율이 아니라 취업자 수 중심이다. 취업자 수는 지역 인구 규모의 영향을 크게 받기 때문에, 가능한 feature는 전체 대비 비율로 변환했다.

생성된 주요 feature:

| 영역 | feature | 의미 |
|---|---|---|
| 성별 | `female_employed_share` | 전체 취업자 중 여성 취업자 비중 |
| 성별 | `male_female_employed_share_gap` | 남녀 취업자 구성비 격차 |
| 연령 | `youth_employed_share` | 전체 취업자 중 청년층 비중 |
| 연령 | `middle_age_employed_share` | 전체 취업자 중 중장년층 비중 |
| 연령 | `senior_employed_share` | 전체 취업자 중 고령층 비중 |
| 종사상지위 | `wage_worker_share` | 임금근로자 비중 |
| 종사상지위 | `self_employed_share` | 자영업자 비중 |
| 종사상지위 | `temporary_worker_share` | 임시근로자 비중 |
| 종사상지위 | `daily_worker_share` | 일용근로자 비중 |
| 취업시간 | `short_hours_worker_share` | 단시간 취업자 비중 |
| 취업시간 | `long_hours_worker_share` | 장시간 취업자 비중 |

진단 파일:

- [`tables/03_feature_build_log.csv`](tables/03_feature_build_log.csv)
- [`tables/03_year_region_unit_check.csv`](tables/03_year_region_unit_check.csv)

### 진단

각 feature frame은 모두 `year × region` 단위로 정리되었고, 중복 key는 발생하지 않았다.

### 가설

취업자 수 자체보다 구성비 feature가 지역 간 고용 구조 차이를 비교하는 데 더 적절하다.

### 처방

고용률, 실업률, 경제활동참가율 원본이 추가되면 현재 count 기반 feature보다 rate 기반 feature를 우선 사용한다.

## 6. 최종 패널 생성 결과

최종 패널은 2025년과 2026년 각각 17개 시도를 포함한다.

| year | region_count |
|---:|---:|
| 2025 | 17 |
| 2026 | 17 |

수도권/비수도권 구성:

| year | 수도권 | 비수도권 |
|---:|---:|---:|
| 2025 | 3 | 14 |
| 2026 | 3 | 14 |

진단 파일:

- [`tables/04_merge_summary.csv`](tables/04_merge_summary.csv)
- [`tables/04_panel_missing_summary.csv`](tables/04_panel_missing_summary.csv)
- [`tables/04_panel_year_region_coverage.csv`](tables/04_panel_year_region_coverage.csv)
- [`tables/04_unmatched_target_year_region.csv`](tables/04_unmatched_target_year_region.csv)
- [`tables/04_unmatched_employment_year_region.csv`](tables/04_unmatched_employment_year_region.csv)

### 진단

고용 feature는 결측 없이 병합되었다. 다만 삶의 만족도 target은 원본 부재로 인해 34개 row 모두 결측이다.

### 가설

현재 패널은 고용 구조 점검용으로는 사용할 수 있지만, 삶의 질-고용 관계 분석용 최종 데이터셋으로는 아직 불완전하다.

### 처방

삶의 만족도 데이터와 2016~2024 고용 데이터가 추가된 뒤 패널을 재생성해야 한다.

## 7. 현재 고용 구조의 기초 관찰

현재 패널 34개 `year-region` 기준 주요 feature 요약:

| feature | 평균 | 최소 | 최대 |
|---|---:|---:|---:|
| 여성 취업자 비중 | 44.17 | 38.14 | 48.32 |
| 남녀 취업자 구성비 격차 | 11.67 | 3.45 | 23.78 |
| 청년층 취업자 비중 | 11.34 | 8.96 | 14.95 |
| 고령층 취업자 비중 | 25.26 | 14.94 | 35.50 |
| 임금근로자 비중 | 75.54 | 62.89 | 84.28 |
| 임시근로자 비중 | 16.37 | 11.16 | 19.52 |
| 일용근로자 비중 | 2.79 | 0.95 | 3.95 |
| 단시간 취업자 비중 | 24.22 | 19.16 | 30.69 |
| 장시간 취업자 비중 | 9.36 | 6.78 | 11.63 |

수도권/비수도권 평균 비교:

| feature | 수도권 | 비수도권 | 관찰 |
|---|---:|---:|---|
| 여성 취업자 비중 | 44.91 | 44.02 | 수도권이 약간 높음 |
| 남녀 취업자 구성비 격차 | 10.18 | 11.99 | 비수도권이 더 큼 |
| 청년층 취업자 비중 | 12.94 | 11.00 | 수도권이 더 높음 |
| 고령층 취업자 비중 | 20.63 | 26.25 | 비수도권이 더 높음 |
| 임금근로자 비중 | 81.89 | 74.18 | 수도권이 더 높음 |
| 단시간 취업자 비중 | 21.21 | 24.86 | 비수도권이 더 높음 |
| 장시간 취업자 비중 | 8.99 | 9.44 | 비수도권이 약간 높음 |

### 해석 주의

위 결과는 2025~2026 일부 자료만 사용한 기초 관찰이다. 삶의 만족도 target도 없으므로, 현재 단계에서는 고용 구조 차이가 관찰된다고만 말할 수 있다. 삶의 질 차이에 영향을 준다고 해석하려면 target 데이터와 전체 기간 데이터가 필요하다.

## 8. 다음 작업

우선순위:

1. `data/raw/life_quality/life_satisfaction.csv` 추가
2. 2016~2024 고용 데이터 추가
3. 고용률, 실업률, 경제활동참가율 원본 추가
4. 1~4단계 재실행
5. 5단계부터 삶의 만족도 target EDA 진행

현재 상태에서 5단계를 진행하면 target이 전부 결측이므로 분석 결과가 비어 있게 된다.

## 9. 시각화 산출물

현재 단계에서는 삶의 만족도 target이 없으므로, 시각화는 데이터 coverage, 2026년 부분자료 여부, 고용 구조 차이를 중심으로 생성했다.

시각화 index:

- [`tables/05_visualization_index.csv`](tables/05_visualization_index.csv)

생성된 그림:

| 그림 | 목적 |
|---|---|
| [`figures/eda_01_year_region_coverage.png`](figures/eda_01_year_region_coverage.png) | 2025년과 2026년에 17개 시도가 모두 포함되는지 확인 |
| [`figures/eda_02_partial_2026_periods.png`](figures/eda_02_partial_2026_periods.png) | 2026년이 완전 연간 자료가 아닌 부분자료임을 확인 |
| [`figures/eda_03_metro_employment_structure.png`](figures/eda_03_metro_employment_structure.png) | 수도권/비수도권의 주요 고용 구조 평균 비교 |
| [`figures/eda_04_youth_senior_scatter_2026.png`](figures/eda_04_youth_senior_scatter_2026.png) | 시도별 청년층-고령층 취업자 비중 분포 확인 |
| [`figures/eda_05_region_employment_heatmap_2026.png`](figures/eda_05_region_employment_heatmap_2026.png) | 시도별 고용 구조 변수를 heatmap으로 비교 |
| [`figures/eda_06_gender_gap_by_region_2026.png`](figures/eda_06_gender_gap_by_region_2026.png) | 시도별 남녀 취업자 구성비 격차 확인 |
| [`figures/eda_07_key_feature_trends.png`](figures/eda_07_key_feature_trends.png) | 2025년과 2026년 일부자료의 권역별 평균 변화 확인 |

주의: 2026년 그림은 모두 부분자료 기준이므로, 연간 비교나 정책적 해석에는 사용하지 않는 것이 적절하다.
