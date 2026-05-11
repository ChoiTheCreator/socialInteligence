# KOSIS 삶의 만족도-고용 EDA 요약

## 1. 분석 목적
본 분석은 KOSIS의 삶의 만족도 자료와 고용 관련 지역 통계를 결합하여, 수도권과 비수도권 간 삶의 만족도 차이가 고용 여건과 어떤 관련을 갖는지 탐색하는 것을 목적으로 한다.

## 2. 데이터 진단 결과
- 분석 기간: 2025~2026
- 사용한 지역 단위: 17개 시도, 수도권은 서울·경기·인천으로 정의
- 사용 가능한 필수 고용 변수: temporary_worker_ratio, daily_worker_ratio, self_employed_ratio, short_hours_worker_ratio, long_hours_worker_ratio
- 결측 및 2026년 부분자료 여부: 2026년 부분자료 파일 수: 5
- 병합 과정에서 제외/불일치된 데이터: `outputs/tables/05_merge_failed_rows.csv` 참고

## 3. 삶의 만족도 차이
- `life_satisfaction` target이 충분히 존재할 때만 수도권/비수도권 차이와 추세를 해석한다.
- 현재 target이 없거나 부족하면 차이 존재 여부를 판단하지 않는다.

## 4. 고용 지표의 차이
- 생성 가능한 고용 변수는 `temporary_worker_ratio, daily_worker_ratio, self_employed_ratio, short_hours_worker_ratio, long_hours_worker_ratio`이다.
- 고용률·실업률·경제활동참가율 원자료가 없으면 해당 변수는 생성 불가로 기록하며, 값을 추정하지 않는다.
- 취업자 수 기반 변수는 전체 취업자 대비 비율로 바꾼 경우에만 구조 비교용으로 사용한다.

## 5. 삶의 만족도와 고용 변수의 관계
- 계산 가능한 상관관계가 없다. target 또는 고용 변수 표본이 부족하다.

## 6. 보조 모델링 결과
- permutation importance를 계산하지 않았다. target/feature/표본 수가 부족하다.

## 7. 결론
선택 결론: C. 삶의 만족도 target 또는 표본 수가 부족해 고용 지표와의 관계를 충분히 검증할 수 없다.

이 결론은 현재 데이터에 근거한 자동 요약이다. 상관관계를 인과관계로 해석하지 않으며, 삶의 만족도 target 또는 핵심 고용률 지표가 부족한 경우 추가 데이터 확보가 필요하다.