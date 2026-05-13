# Employment Wage Raw Data

KOSIS 고용·임금 분석에 사용하는 원본 데이터 보관 위치다.

## 구조

- `source_downloads/`: KOSIS에서 내려받은 원본 파일명 그대로 보관
- `employment_*.csv`: 분석 코드가 참조하는 안정 파일명 사본

## 현재 포함 파일

- `employment_econ_activity_sex.csv`: 성별 경제활동인구, 고용률, 실업률, 경제활동참가율, 15~64세 고용률
- `employment_region_age.csv`: 행정구역(시도)별 연령별 취업자
- `employment_region_sex_age.csv`: 행정구역(시도)별 성·연령별 취업자
- `employment_status.csv`: 행정구역(시도)별 종사상지위별 취업자
- `employment_hours.csv`: 행정구역(시도)별 취업시간별 취업자
- `employment_education.csv`: 행정구역(시도)별 교육정도별 취업자

## 기간

- 수록 기간: 2016.1/4~2026.1/4
- 완전 연도 분석 기간: 2016~2025
- 2026년은 1분기만 있으므로 최종 정책 결론에서는 제외하고 최신 참고값으로만 사용한다.
