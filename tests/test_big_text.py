import pytest

import vocab

needs_font = pytest.mark.skipif(vocab._big_font(vocab.BIG_SIZE) is None,
                                reason="chưa cài Pillow hoặc không có font tiếng Nhật")


@needs_font
def test_big_lines_size():
    lines = vocab.big_lines("学", 32)
    assert 8 < len(lines) <= 16
    assert lines[0] and lines[-1]
    assert max(len(l) for l in lines) <= 32
    assert set("".join(lines)) <= set(" ▀▄█")
    assert sum(ch != " " for l in lines for ch in l) > 50


@needs_font
def test_big_lines_width_grows_with_text():
    lines = vocab.big_lines("図書館", 16)
    assert len(lines) <= 8
    assert max(len(l) for l in lines) > 32


@needs_font
def test_show_japanese_big_only_for_kanji(monkeypatch, capsys):
    monkeypatch.setattr(vocab, "BIG_TEXT", True)
    vocab.show_japanese("学")
    assert "█" in capsys.readouterr().out
    vocab.show_japanese("がくせい")
    assert "がくせい" in capsys.readouterr().out


@needs_font
def test_show_japanese_falls_back_when_terminal_too_narrow(monkeypatch, capsys):
    monkeypatch.setattr(vocab, "BIG_TEXT", True)
    monkeypatch.setattr(vocab.shutil, "get_terminal_size", lambda: __import__("os").terminal_size((40, 24)))
    vocab.show_japanese("電話番号")
    assert "電話番号" in capsys.readouterr().out


def test_show_japanese_plain_when_disabled(monkeypatch, capsys):
    monkeypatch.setattr(vocab, "BIG_TEXT", False)
    vocab.show_japanese("学")
    assert capsys.readouterr().out == "    学\n\n"


def test_big_lines_without_font(monkeypatch):
    monkeypatch.setattr(vocab, "_big_font", lambda size: None)
    assert vocab.big_lines("学") is None
