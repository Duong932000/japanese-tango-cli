import pytest

import vocab
from conftest import write_csv


def by_key(words):
    return {w.key: w for w in words}


def test_list_levels_only_folders_with_csv(sample_n5, data_dir):
    (data_dir / "N4").mkdir()
    write_csv(data_dir / "N3" / "kanji.csv", ["lesson", "kanji", "kana", "meaning_vi"], [])
    assert vocab.list_levels() == ["N3", "N5"]


def test_list_levels_without_data_dir(data_dir):
    data_dir.rmdir()
    assert vocab.list_levels() == []


def test_load_level_reads_all_files(sample_n5):
    words = by_key(vocab.load_level("N5"))
    assert len(words) == 7
    assert words["学生|がくせい"].kind == "kanji"
    assert words["|はい"].kind == "hiragana"
    assert words["|テレビ"].kind == "katakana"


def test_word_in_several_lessons_is_merged(sample_n5):
    words = by_key(vocab.load_level("N5"))
    assert words["学生|がくせい"].lessons == ["1", "3"]


def test_load_level_skips_comments_and_bad_rows(data_dir, capsys):
    write_csv(data_dir / "N5" / "kanji.csv", ["lesson", "kanji", "kana", "meaning_vi"], [
        ["# ví dụ", "学生", "がくせい", "học sinh"],
        ["1", "本", "ほん", "sách"],
        ["1", "傘", "", "ô"],
        ["", "", "", ""],
    ])
    words = vocab.load_level("N5")
    assert [w.key for w in words] == ["本|ほん"]
    out = capsys.readouterr().out
    assert "dòng 4" in out
    assert "dòng 5" not in out


def test_kind_falls_back_to_content_for_other_files(data_dir):
    write_csv(data_dir / "N5" / "extra.csv", ["lesson", "kanji", "kana", "meaning_vi"], [
        ["1", "", "テレビ", "tivi"],
        ["1", "", "はい", "vâng"],
        ["1", "本", "ほん", "sách"],
    ])
    kinds = {w.kana: w.kind for w in vocab.load_level("N5")}
    assert kinds == {"テレビ": "katakana", "はい": "hiragana", "ほん": "kanji"}


def test_csv_with_bom_is_read(data_dir):
    path = data_dir / "N5" / "hiragana.csv"
    path.parent.mkdir()
    path.write_text("﻿lesson,kana,meaning_vi\n1,はい,vâng\n", encoding="utf-8")
    assert [w.kana for w in vocab.load_level("N5")] == ["はい"]


AVAILABLE = ["1", "2", "3", "10", "extra"]


@pytest.mark.parametrize("text, expected", [
    ("all", None),
    ("ALL", None),
    ("", None),
    ("2", {"2"}),
    ("1-3", {"1", "2", "3"}),
    ("3-1", {"1", "2", "3"}),
    ("1, 10", {"1", "10"}),
    ("2-20", {"2", "3", "10"}),
    ("Extra", {"extra"}),
])
def test_parse_lessons(text, expected):
    assert vocab.parse_lessons(text, AVAILABLE) == expected


@pytest.mark.parametrize("text", ["7", "abc", "50-60"])
def test_parse_lessons_rejects_unknown(text):
    with pytest.raises(ValueError):
        vocab.parse_lessons(text, AVAILABLE)


def test_lessons_sorted_numerically():
    assert sorted(["10", "2", "extra", "1"], key=vocab.lesson_sort_key) == ["1", "2", "10", "extra"]
