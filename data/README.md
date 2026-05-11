# Data

팀 공통 데이터 폴더입니다. 분석 코드는 각 주제 폴더에 두고, 여러 사람이 재사용해야 하는 데이터만 이곳에서 관리합니다.

## 구조

```text
data/
  raw/
    employment_wage/      # 고용·임금 KOSIS 원본 및 안정 파일명 사본
    life_quality/         # 삶의 만족도/삶의 질 원본 CSV 위치
  processed/
    kosis_life_quality_employment_panel.csv
    employment_wage/      # 고용 EDA 중간 산출물
```

## Git에 올리는 기준

- 공개 데이터이고 파일 크기가 작으며 팀원이 같은 입력으로 재현해야 하면 Git에 포함한다.
- 파일이 크거나, 자주 바뀌거나, 재배포 조건이 애매하면 Git에 올리지 않고 다운로드 경로와 파일명을 문서화한다.
- 최종 공통 패널은 `data/processed/`에 두고, 생성 코드는 반드시 각 주제 폴더의 `notebooks/` 또는 `src/`에서 재실행 가능해야 한다.

## 현재 상태

- 고용 원본: `data/raw/employment_wage/`
- KOSIS 원본 다운로드 파일명 보존본: `data/raw/employment_wage/source_downloads/`
- 삶의 만족도 원본: 아직 없음. 추가 시 `data/raw/life_quality/life_satisfaction.csv`에 둔다.
- 최종 패널: `data/processed/kosis_life_quality_employment_panel.csv`
