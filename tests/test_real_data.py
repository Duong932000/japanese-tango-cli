"""Kiểm tra các file từ vựng thật trong data/ mỗi khi thêm bài mới."""

import csv
import re
from collections import Counter

import pytest

import vocab

HEADERS = {
    "hiragana": ["lesson", "kana", "meaning_vi"],
    "katakana": ["lesson", "kana", "meaning_vi"],
    "kanji": ["lesson", "kanji", "hanviet", "meaning_vi"],
    "kanji-vocab": ["lesson", "kanji", "kana", "hanviet", "meaning_vi"],
}
REQUIRED = {
    "kanji": ("lesson", "kanji", "hanviet", "meaning_vi"),
    "kanji-vocab": ("lesson", "kanji", "kana", "hanviet", "meaning_vi"),
}
KANJI = re.compile(r"[一-鿿々]")
KANJI_OR_RADICAL = re.compile(r"[一-鿿々⺀-⿟]")
CSV_FILES = sorted(vocab.DATA_DIR.glob("*/*.csv"))


def rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        data = [(n, r) for n, r in enumerate(reader, start=2)
                if not (r.get("lesson") or "").startswith("#")]
        return reader.fieldnames, data


def col(r, name):
    return (r.get(name) or "").strip()


def file_id(path):
    return f"{path.parent.name}/{path.name}"


def files(stem):
    return [p for p in CSV_FILES if p.stem == stem]


pytestmark = pytest.mark.skipif(not CSV_FILES, reason="chưa có dữ liệu trong data/")


@pytest.mark.parametrize("path", CSV_FILES, ids=file_id)
def test_header(path):
    header, _ = rows(path)
    if header is None:
        pytest.skip("file rỗng")
    expected = HEADERS.get(path.stem, header)
    assert header == expected, f"header phải là {','.join(expected)}"


@pytest.mark.parametrize("path", CSV_FILES, ids=file_id)
def test_rows_complete(path):
    _, data = rows(path)
    required = REQUIRED.get(path.stem, ("lesson", "kana", "meaning_vi"))
    bad = [n for n, r in data if not all(col(r, c) for c in required)]
    assert not bad, f"dòng thiếu một trong các cột {required}: {bad}"


@pytest.mark.parametrize("path", CSV_FILES, ids=file_id)
def test_lesson_is_number(path):
    _, data = rows(path)
    bad = [n for n, r in data if not col(r, "lesson").isdigit()]
    assert not bad, f"cột lesson phải là số, ví dụ 3 (không ghi 'Bài 3'): dòng {bad}"


@pytest.mark.parametrize("path", files("kanji"), ids=file_id)
def test_single_kanji_is_one_character(path):
    _, data = rows(path)
    def ok(cell):
        char = cell.strip("～〜~")  # bộ thủ ghi kèm vị trí, ví dụ ～阝
        return len(char) == 1 and KANJI_OR_RADICAL.match(char)
    bad = [n for n, r in data if not ok(col(r, "kanji"))]
    assert not bad, f"kanji.csv chỉ chứa đúng một chữ kanji hoặc bộ thủ mỗi dòng: dòng {bad}"


@pytest.mark.parametrize("path", files("kanji-vocab"), ids=file_id)
def test_kanji_vocab_has_kanji(path):
    _, data = rows(path)
    bad = [n for n, r in data if not KANJI.search(col(r, "kanji"))]
    assert not bad, f"cột kanji không có chữ kanji: dòng {bad}"


@pytest.mark.parametrize("path", [p for p in CSV_FILES if p.stem != "kanji"], ids=file_id)
def test_kana_column_has_no_kanji(path):
    _, data = rows(path)
    bad = [n for n, r in data if KANJI.search(col(r, "kana"))]
    assert not bad, f"cột kana chứa kanji: dòng {bad}"


@pytest.mark.parametrize("path", files("kanji-vocab"), ids=file_id)
def test_every_kanji_in_vocab_is_listed(path):
    """Mỗi chữ kanji trong kanji-vocab.csv phải có trong kanji.csv cùng cấp độ."""
    single_path = path.with_name("kanji.csv")
    if not single_path.exists():
        pytest.skip("chưa có kanji.csv")
    listed = {col(r, "kanji") for _, r in rows(single_path)[1]}
    missing = sorted({ch for _, r in rows(path)[1] for ch in KANJI.findall(col(r, "kanji"))} - listed)
    assert not missing, f"thêm các chữ này vào kanji.csv: {' '.join(missing)}"


@pytest.mark.parametrize("level", sorted({p.parent.name for p in CSV_FILES}))
def test_no_duplicate_in_same_lesson(level):
    seen = Counter()
    for path in (vocab.DATA_DIR / level).glob("*.csv"):
        for _, r in rows(path)[1]:
            seen[(path.stem, col(r, "lesson"), col(r, "kanji"), col(r, "kana"))] += 1
    dups = [k for k, c in seen.items() if c > 1]
    assert not dups, f"bị lặp trong cùng một bài: {dups}"
