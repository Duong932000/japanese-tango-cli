"""Kiểm tra các file từ vựng thật trong data/ mỗi khi thêm bài mới."""

import csv
import re
from collections import Counter

import pytest

import vocab

HEADERS = {
    "kanji": ["lesson", "kanji", "kana", "meaning_vi"],
    "hiragana": ["lesson", "kana", "meaning_vi"],
    "katakana": ["lesson", "kana", "meaning_vi"],
}
KANJI = re.compile(r"[一-鿿々]")
CSV_FILES = sorted(vocab.DATA_DIR.glob("*/*.csv"))


def rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        data = [(n, r) for n, r in enumerate(reader, start=2)
                if not (r.get("lesson") or "").startswith("#")]
        return reader.fieldnames, data


def file_id(path):
    return f"{path.parent.name}/{path.name}"


pytestmark = pytest.mark.skipif(not CSV_FILES, reason="chưa có dữ liệu trong data/")


@pytest.mark.parametrize("path", CSV_FILES, ids=file_id)
def test_header(path):
    header, _ = rows(path)
    assert header == HEADERS.get(path.stem, header), f"header phải là {HEADERS[path.stem]}"


@pytest.mark.parametrize("path", CSV_FILES, ids=file_id)
def test_rows_complete(path):
    _, data = rows(path)
    bad = [n for n, r in data
           if not all((r.get(c) or "").strip() for c in ("lesson", "kana", "meaning_vi"))]
    assert not bad, f"dòng thiếu lesson/kana/meaning_vi: {bad}"


@pytest.mark.parametrize("path", CSV_FILES, ids=file_id)
def test_lesson_is_number(path):
    _, data = rows(path)
    bad = [n for n, r in data if not (r["lesson"] or "").strip().isdigit()]
    assert not bad, f"cột lesson phải là số, ví dụ 3 (không ghi 'Bài 3'): dòng {bad}"


@pytest.mark.parametrize("path", [p for p in CSV_FILES if p.stem == "kanji"], ids=file_id)
def test_kanji_file_has_kanji(path):
    _, data = rows(path)
    bad = [n for n, r in data if not KANJI.search(r.get("kanji") or "")]
    assert not bad, f"cột kanji không có chữ kanji: dòng {bad}"


@pytest.mark.parametrize("path", CSV_FILES, ids=file_id)
def test_kana_column_has_no_kanji(path):
    _, data = rows(path)
    bad = [n for n, r in data if KANJI.search(r.get("kana") or "")]
    assert not bad, f"cột kana chứa kanji: dòng {bad}"


@pytest.mark.parametrize("level", sorted({p.parent.name for p in CSV_FILES}))
def test_no_duplicate_in_same_lesson(level):
    seen = Counter()
    for path in (vocab.DATA_DIR / level).glob("*.csv"):
        for _, r in rows(path)[1]:
            seen[(r["lesson"].strip(), (r.get("kanji") or "").strip(), r["kana"].strip())] += 1
    dups = [k for k, c in seen.items() if c > 1]
    assert not dups, f"từ bị lặp trong cùng một bài: {dups}"
