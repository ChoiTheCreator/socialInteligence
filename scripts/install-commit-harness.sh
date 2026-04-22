#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

max_files="6"
max_lines="180"
max_areas="2"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --max-files)
      max_files="$2"
      shift 2
      ;;
    --max-lines)
      max_lines="$2"
      shift 2
      ;;
    --max-areas)
      max_areas="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--max-files N] [--max-lines N] [--max-areas N]"
      exit 1
      ;;
  esac
done

git config core.hooksPath .githooks
git config harness.maxFiles "$max_files"
git config harness.maxLines "$max_lines"
git config harness.maxAreas "$max_areas"

echo "[commit-harness] installed"
echo "- hooksPath: .githooks"
echo "- harness.maxFiles: $max_files"
echo "- harness.maxLines: $max_lines"
echo "- harness.maxAreas: $max_areas"
