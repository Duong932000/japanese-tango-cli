import csv

import pytest

import vocab


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Thư mục data/ và progress.json tạm, không đụng vào dữ liệu thật."""
    root = tmp_path / "data"
    root.mkdir()
    monkeypatch.setattr(vocab, "DATA_DIR", root)
    monkeypatch.setattr(vocab, "PROGRESS_FILE", tmp_path / "progress.json")
    return root


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


@pytest.fixture
def sample_n5(data_dir):
    level = data_dir / "N5"
    write_csv(level / "kanji.csv", ["lesson", "kanji", "hanviet", "meaning_vi"], [
        ["1", "学", "HỌC", "học"],
        ["2", "本", "BẢN", "sách/gốc"],
    ])
    write_csv(level / "kanji-vocab.csv", ["lesson", "kanji", "kana", "hanviet", "meaning_vi"], [
        ["1", "学生", "がくせい", "HỌC SINH", "học sinh/sinh viên"],
        ["1", "先生", "せんせい", "TIÊN SINH", "giáo viên"],
        ["2", "本", "ほん", "BẢN", "sách"],
        ["3", "学生", "がくせい", "HỌC SINH", "học sinh/sinh viên"],
        ["10", "水", "みず", "THỦY", "nước"],
    ])
    write_csv(level / "hiragana.csv", ["lesson", "kana", "meaning_vi"], [
        ["1", "はい", "vâng"],
        ["2", "これ", "cái này"],
    ])
    write_csv(level / "katakana.csv", ["lesson", "kana", "meaning_vi"], [
        ["2", "テレビ", "tivi"],
    ])
    return level
