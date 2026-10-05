#!/usr/bin/env bash
# Chạy tool học từ vựng hoặc bộ test trong môi trường ảo .venv.
#
#   ./run.sh [tham số của vocab.py]   học từ vựng, ví dụ: ./run.sh -b 3
#   ./run.sh test [tham số pytest]    chạy test, ví dụ: ./run.sh test -k romaji
#   ./run.sh setup                    tạo .venv và cài thư viện cho test
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

VENV=".venv"
PY="$VENV/bin/python"

ensure_venv() {
    if [[ ! -x "$PY" ]]; then
        command -v python3 >/dev/null || { echo "Không tìm thấy python3." >&2; exit 1; }
        echo "Tạo môi trường ảo $VENV ..."
        python3 -m venv "$VENV"
    fi
}

ensure_dev_deps() {
    ensure_venv
    if ! "$PY" -c "import pytest" 2>/dev/null; then
        echo "Cài thư viện cho test ..."
        "$PY" -m pip install --quiet --disable-pip-version-check -r requirements-dev.txt
    fi
}

case "${1:-}" in
    test)
        shift
        ensure_dev_deps
        exec "$PY" -m pytest "$@"
        ;;
    setup)
        ensure_dev_deps
        echo "Đã sẵn sàng: $VENV"
        ;;
    *)
        ensure_venv
        exec "$PY" vocab.py "$@"
        ;;
esac
