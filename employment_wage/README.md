# Employment & Wage (고용·임금)

- 담당자: 원빈

## 연구 질문
- 연령계층별 취업자 수는 최신 시점에 어떻게 분포하는가?

## 데이터셋
- 출처: KOSIS
- 지표명: 행정구역(시도)별 연령별 취업자
- 기간: 2025.10 ~ 2026.03
- 지역: 전국(계)
- 단위: 원본 파일 기준
- 원본 보존 위치: `../data/raw/employment_wage/source_downloads/`
- 분석용 안정 파일명 위치: `../data/raw/employment_wage/`

## 삶의 질-고용 EDA

- 노트북: [`notebooks/01_eda_kosis_employment_life_quality.ipynb`](notebooks/01_eda_kosis_employment_life_quality.ipynb)
- 유틸리티: [`src/eda_utils.py`](src/eda_utils.py)
- 진단 테이블: [`outputs/tables/`](outputs/tables/)
- 중간 정제 데이터: `../data/processed/employment_wage/`
- 최종 공통 패널: `../data/processed/kosis_life_quality_employment_panel.csv`
- 팀 공유용 Evidence Map: [`evidence_map/README.md`](evidence_map/README.md)

## 산출물
- 시각화: [`viz/employment_by_age_latest.png`](viz/employment_by_age_latest.png)
- 노트북: [`notebooks/employment_by_age_latest.ipynb`](notebooks/employment_by_age_latest.ipynb)
- 스크립트(선택): [`src/plot_employment_by_age_latest.py`](src/plot_employment_by_age_latest.py)

## 재현 방법

1. Jupyter에서 `employment_wage/notebooks/employment_by_age_latest.ipynb`를 열고 전체 셀 실행
2. 결과 이미지가 `employment_wage/viz/employment_by_age_latest.png`에 저장됨
3. 삶의 질-고용 EDA는 `employment_wage/notebooks/01_eda_kosis_employment_life_quality.ipynb`를 열고 전체 셀 실행

## 인사이트
- 최신 월 기준, 중복 구간(15-29세/15-64세)을 제외한 기본 연령대 분포를 확인할 수 있음
- (작성) 향후 성별/지역 분해 그래프를 추가하면 해석력이 높아짐
