import json

import pytest

import vocab


@pytest.fixture
def run(monkeypatch, capsys):
    """Chạy main() với tham số dòng lệnh và danh sách câu trả lời giả lập."""
    def _run(argv, answers=()):
        feed = iter(answers)

        def fake_input(prompt=""):
            print(prompt, end="")
            try:
                return next(feed)
            except StopIteration:
                raise EOFError

        monkeypatch.setattr("builtins.input", fake_input)
        monkeypatch.setattr("sys.argv", ["vocab.py", *argv])
        code = 0
        try:
            vocab.main()
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
        return code, capsys.readouterr().out
    return _run


def saved_progress():
    return json.loads(vocab.PROGRESS_FILE.read_text(encoding="utf-8"))


def test_study_one_lesson_shows_only_its_words(sample_n5, run):
    code, out = run(["-b", "1", "--mode", "jv"], ["", "y"] * 10)
    assert code == 0
    assert "N5 · bài 1 · 3 thẻ" in out
    assert "Kết quả: 3/3" in out
    assert set(saved_progress()["words"]) == {"学生|がくせい", "先生|せんせい", "|はい"}


def test_lesson_chosen_from_menu(sample_n5, run):
    code, out = run([], ["7", "2", ":q"])
    assert "Bài 1 (3 từ)" in out and "Bài 10 (1 từ)" in out
    assert "Không có bài '7'" in out
    assert "N5 · bài 2 · 3 thẻ" in out


def test_typed_answer_is_checked(sample_n5, run):
    code, out = run(["-b", "10", "--kind", "kanji", "--mode", "vj"], ["mizu"])
    assert "✓ Đúng!" in out
    assert saved_progress()["words"]["水|みず"]["box"] == 1


def test_wrong_answer_is_asked_again(sample_n5, run):
    code, out = run(["-b", "10", "--kind", "kanji", "--mode", "vj"], ["sai", "n", "mizu"])
    assert "✗ Chưa đúng." in out
    assert "[ôn lại]" in out
    assert "Kết quả: 0/1" in out
    assert saved_progress()["words"]["水|みず"]["wrong"] == 1


def test_kind_filter(sample_n5, run):
    code, out = run(["-b", "all", "--kind", "katakana", "--mode", "jv"], ["", "y"])
    assert "1 thẻ" in out and "テレビ" in out


def test_all_lessons_uses_schedule(sample_n5, run):
    code, out = run(["-b", "all", "--new", "2"], [":q"])
    assert "Chưa học: 7 từ" in out
    assert "tất cả các bài · 2 thẻ" in out


def test_stats_per_lesson(sample_n5, run):
    code, out = run(["--stats"])
    assert code == 0
    assert "N5 · tất cả các bài: 7 từ" in out
    assert "Bài 10" in out


def test_unknown_lesson_exits(sample_n5, run):
    code, out = run(["-b", "99"])
    assert code != 0


def test_no_data_exits(data_dir, run):
    code, _ = run([])
    assert code != 0


def test_reset_needs_confirmation(sample_n5, run):
    vocab.save_progress({"words": {}, "history": {}})
    run(["--reset"], ["n"])
    assert vocab.PROGRESS_FILE.exists()
    run(["--reset"], ["y"])
    assert not vocab.PROGRESS_FILE.exists()
