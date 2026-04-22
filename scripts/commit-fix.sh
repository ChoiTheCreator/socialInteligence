#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"한국어 커밋 메시지\""
  echo "Example: $0 \"고용 연령축 라벨 정리\""
  exit 1
fi

message="$*"
git commit -m "fix : \"$message\""
