# Employment & Wage (고용·임금)

- 담당자: 원빈

## 연구 질문

2016~2026년 KOSIS 고용 데이터를 기준으로 볼 때, 지역 간 고용 여건 격차는 어떤 구조에서 발생하며 고용 측면에서 지역 간 삶의 질 격차를 줄이려면 어떤 정책 레버가 우선인가?

## 데이터셋

- 출처: KOSIS
- 기간: 2016.1/4~2026.1/4
- 최종 정책 결론 기준 기간: 2016~2025년 완전 연도
- 2026년 처리: 1분기만 포함되어 최신 참고값으로만 사용
- 지역: 17개 시도
- 분석 단위: `year × region`

사용한 안정 파일명:

- `data_raw/employment_wage/employment_econ_activity_sex.csv`
- `data_raw/employment_wage/employment_region_age.csv`
- `data_raw/employment_wage/employment_region_sex_age.csv`
- `data_raw/employment_wage/employment_status.csv`
- `data_raw/employment_wage/employment_hours.csv`
- `data_raw/employment_wage/employment_education.csv`

KOSIS에서 받은 원본 파일명 보존본은 `data_raw/employment_wage/source_downloads/`에 있다.

## 분석 파이프라인

```text
KOSIS raw CSV
  -> 원본 파일 보관 및 안정 파일명 정리
  -> 분기 컬럼 long 변환
  -> 지역명 17개 시도 기준 정규화
  -> 수도권/비수도권 분류
  -> 분기 패널 생성
  -> 완전 연도 기준 연평균 패널 생성
  -> 고용 접근성, 여성 고용, 안정일자리, 청년정착, 근로시간 점수화
  -> 지역별 격차와 정책 우선순위 산정
```

## 산출물

- 최종 보고서: [`report/employment_inequality_policy_report.md`](report/employment_inequality_policy_report.md)
- 분석 스크립트: [`src/analyze_employment_inequality_2016_2026.py`](src/analyze_employment_inequality_2016_2026.py)
- 원본 데이터 EDA 진단: [`outputs/tables/eda/raw_eda_diagnosis.csv`](outputs/tables/eda/raw_eda_diagnosis.csv)
- 고용-삶의 질 proxy 기준표: [`outputs/tables/eda/analysis_framework.csv`](outputs/tables/eda/analysis_framework.csv)
- 원본 데이터별 사용 근거: [`outputs/tables/eda/raw_dataset_roles.csv`](outputs/tables/eda/raw_dataset_roles.csv)
- 최종 연간 패널: [`outputs/tables/panels/employment_panel_annual_scored_2016_2026.csv`](outputs/tables/panels/employment_panel_annual_scored_2016_2026.csv)
- 정책 우선순위 표: [`outputs/tables/results/priority.csv`](outputs/tables/results/priority.csv)
- EDA 시각화: [`outputs/figures/eda/`](outputs/figures/eda/)
- 추세 시각화: [`outputs/figures/trends/`](outputs/figures/trends/)
- 정책 시각화: [`outputs/figures/policy/`](outputs/figures/policy/)
- 지역 진단 시각화: [`outputs/figures/regional/`](outputs/figures/regional/)

## 재현 방법

```bash
python employment_wage/src/analyze_employment_inequality_2016_2026.py
```

## 핵심 결론

2016~2025년 완전 연도 기준으로 보면 지역 간 고용격차는 단순한 고용률 차이라기보다 고학력 인력이 일할 수 있는 지역 산업 기반, 청년 정착 가능성, 안정적 임금일자리 구조에서 크게 나타난다.

데이터 기준 정책 우선순위는 다음 순서다.

1. 고학력·지역산업 일자리 기반
2. 청년 정착 일자리
3. 안정적 임금일자리

따라서 고용 측면에서 지역 간 삶의 질 격차를 줄이려면 단순 일자리 수 확대보다 `고학력·청년정착형 안정일자리 패키지`가 더 타당하다. 지역 대학-기업 연결, 전문직무 창출, 상용직 기반, 청년 주거·생활 지원을 같이 설계하는 방향이 필요하다.

## 해석 한계

- 삶의 만족도 원자료를 직접 결합한 인과분석은 아니다.
- 정책 효과를 추정한 것이 아니라, 고용 구조 데이터가 가리키는 정책 우선순위 가설이다.
- 청년층·고령층 취업자 비중은 고용률이 아니라 취업자 구성비라서 지역 인구구조의 영향을 받는다.
- 2026년은 1분기만 포함되어 최종 결론에는 사용하지 않았다.

## 참고

기존 `notebooks/employment_by_age_latest.ipynb`와 `viz/employment_by_age_latest.png`는 초기 연령별 취업자 분포 확인용 산출물이다. 최종 정책 분석은 위의 2016~2026 분석 스크립트와 보고서를 기준으로 한다.
