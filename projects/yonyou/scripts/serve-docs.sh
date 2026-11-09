#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$project_dir"

if [[ ! -x .venv-docs/bin/mkdocs ]]; then
  echo '请先按 TEACHING-GUIDE.md 安装文档预览环境。'
  exit 1
fi

exec .venv-docs/bin/mkdocs serve --dev-addr 127.0.0.1:8765
