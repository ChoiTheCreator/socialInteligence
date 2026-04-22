# CONTRIBUTING

## 브랜치 전략

- 브랜치명: `feat/<topic>-<name>`
- 예시: `feat/housing-dabin`, `feat/employment-wage-wonbin`

## 커밋 규칙

- `feat: ...` 새로운 분석/시각화
- `docs: ...` 문서 보강
- `fix: ...` 데이터 정리/오류 수정

## 커밋 하네스 (필수)

```bash
bash scripts/install-commit-harness.sh
```

- 메시지 자동 포맷/검증: `fix : "한국어 메시지"`
- 한 커밋 큰 덩어리 제한(기본):
  - 파일 수 `<= 6`
  - 변경 라인 `<= 180`
  - 변경 영역 `<= 2`

제한값 커스터마이즈:

```bash
bash scripts/install-commit-harness.sh --max-files 8 --max-lines 220 --max-areas 3
```

빠른 커밋:

```bash
bash scripts/commit-fix.sh "교육 지표 범례 정리"
```

## PR 체크리스트

1. 담당 폴더에 `README.md` 업데이트
2. 데이터 출처 URL 및 조회일 명시
3. 시각화 결과 파일(`viz/`) 포함
4. 재현 방법(실행 명령) 포함
5. 핵심 인사이트 2~3줄 요약

## README 필수 항목

- 연구 질문
- KOSIS 지표명/지표코드
- 기간/지역/단위
- 원본 데이터 파일명
- 시각화 파일 경로
- 해석 및 한계
