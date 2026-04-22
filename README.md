# socialInteligence

KOSIS 기반 사회 이슈(주거/건강/교육/고용·임금) 리서치 및 시각화 저장소입니다.

## 디렉터리 구조

```text
socialInteligence/
  housing/            # 주거 (다빈)
  health/             # 건강 (유진)
  education/          # 교육 (승민)
  employment_wage/    # 고용·임금 (원빈)
  data_raw/           # 원본 데이터 보관
  docs/               # 협업 문서
```

## 협업 원칙

1. 메인 브랜치(`main`) 직접 푸시 금지
2. 주제별 개인 브랜치에서 작업 후 PR로 머지
3. 각 주제 폴더에 최소 산출물:
   - `README.md` (지표코드/기간/지역/출처/해석)
   - 시각화 파일(`viz/`)
   - 재현 스크립트 또는 노트북

자세한 규칙은 [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)를 참고하세요.

## Commit Harness

팀 공통 커밋 규칙 자동화를 위해 아래를 1회 실행하세요.

```bash
bash scripts/install-commit-harness.sh
```

- 커밋 메시지 형식: `fix : "한국어 메시지"`
- 큰 덩어리 커밋 차단: 기본 제한
  - 파일 수 `<= 6`
  - 변경 라인(추가+삭제) `<= 180`
  - 변경 영역(상위 경로) `<= 2`

간편 커밋:

```bash
bash scripts/commit-fix.sh "고용 연령축 라벨 정리"
```
