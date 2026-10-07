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
    code, out = run(["-t", "4", "-b", "1", "--mode", "jv"], ["", "y"] * 10)
    assert code == 0
    assert "N5 · Tất cả · bài 1 · 4 thẻ" in out
    assert "Kết quả: 4/4" in out
    assert set(saved_progress()["words"]) == {"学生|がくせい", "先生|せんせい", "|はい", "字|学"}


def test_category_and_lesson_chosen_from_menu(sample_n5, run):
    code, out = run([], ["9", "4", "", "7", "2", ":q"])
    assert "1. Từ vựng (hiragana/katakana) (3)" in out
    assert "2. Kanji đơn (2)" in out
    assert "3. Từ vựng kanji (4)" in out
    assert "4. Tất cả (9)" in out
    assert "Bài 1 (4 từ)" in out and "Bài 10 (1 từ)" in out
    assert "Không có bài '7'" in out
    assert "N5 · Tất cả · bài 2 · 4 thẻ" in out


def test_enter_picks_vocab_category(sample_n5, run):
    code, out = run([], ["", "", "2", ":q"])
    assert "Bài 2 (2 từ)" in out
    assert "N5 · Từ vựng (hiragana/katakana) · bài 2 · 2 thẻ" in out


@pytest.mark.parametrize("number, title, count", [
    ("2", "Kanji đơn · trang", 1),
    ("3", "Từ vựng kanji · bài", 2),
])
def test_category_numbers_from_command_line(sample_n5, run, number, title, count):
    code, out = run(["-t", number, "-b", "1", "--mode", "jv"], [":q"])
    assert f"N5 · {title} 1 · {count} thẻ" in out


def test_unknown_category_exits(sample_n5, run):
    code, out = run(["-t", "9"])
    assert code != 0


def test_typed_answer_is_checked(sample_n5, run):
    code, out = run(["-b", "10", "--kind", "kanji-vocab", "--mode", "vj"], ["mizu"])
    assert "✓ Đúng!" in out
    assert saved_progress()["words"]["水|みず"]["box"] == 1


def test_wrong_answer_is_asked_again(sample_n5, run):
    code, out = run(["-b", "10", "--kind", "kanji-vocab", "--mode", "vj"], ["sai", "n", "mizu"])
    assert "✗ Chưa đúng." in out
    assert "[ôn lại]" in out
    assert "Kết quả: 0/1" in out
    assert saved_progress()["words"]["水|みず"]["wrong"] == 1


def test_kind_filter(sample_n5, run):
    code, out = run(["-b", "all", "--kind", "katakana", "--mode", "jv"], ["", "y"])
    assert "1 thẻ" in out and "テレビ" in out


def test_all_lessons_uses_schedule(sample_n5, run):
    code, out = run(["-t", "all", "-b", "all", "--new", "2"], ["", ":q"])
    assert "Chưa học: 9 từ" in out
    assert "N5 · Tất cả · tất cả các bài · 2 thẻ" in out


def test_stats_per_lesson(sample_n5, run):
    code, out = run(["--stats"])
    assert code == 0
    assert "N5 · Tất cả · tất cả các bài: 9 từ" in out
    assert "Bài 10" in out


def test_unknown_lesson_exits(sample_n5, run):
    code, out = run(["-t", "4", "-b", "99", "--mode", "jv"])
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


def test_single_kanji_card(sample_n5, run):
    code, out = run(["-b", "1", "--kind", "kanji", "--mode", "jv"], ["học"])
    assert "Âm Hán Việt hoặc nghĩa" in out
    assert "✓ Đúng!" in out
    assert "学  HỌC  —  học" in out
    assert "On:" not in out


def test_single_kanji_vj_shows_hanviet(sample_n5, run):
    code, out = run(["-b", "1", "--kind", "kanji", "--mode", "vj"], ["学"])
    assert "HỌC  —  học" in out
    assert "✓ Đúng!" in out


def test_kanji_vocab_shows_kanji_by_default(sample_n5, run):
    code, out = run(["-b", "10", "--kind", "kanji-vocab", "--mode", "jv"], ["nước"])
    assert "    水\n" in out
    assert "(THỦY)" in out


@pytest.mark.parametrize("choice, prompt", [
    ("", "Âm Hán Việt hoặc nghĩa"),
    ("1", "Âm Hán Việt hoặc nghĩa"),
    ("2", "Viết chữ kanji ra giấy"),
])
def test_kanji_mode_menu(sample_n5, run, choice, prompt):
    code, out = run([], ["2", choice, "1", ":q"])
    assert "Cách học kanji đơn:" in out
    assert "2. Nhìn âm Hán Việt → viết chữ kanji" in out
    assert prompt in out


def test_kanji_mode_menu_skipped_when_mode_given(sample_n5, run):
    code, out = run(["-t", "2", "-b", "1", "--mode", "vj"], [":q"])
    assert "Cách học kanji đơn:" not in out
    assert "HỌC  —  học" in out


def test_write_kanji_reveals_character(sample_n5, run):
    code, out = run(["-t", "2", "-b", "1", "--mode", "vj"], ["", "y"])
    assert "Viết chữ kanji ra giấy" in out
    assert "学  HỌC  —  học" in out
    assert "Kết quả: 1/1" in out


@pytest.mark.parametrize("category", ["1", "3", "4"])
@pytest.mark.parametrize("choice, prompt", [
    ("1", "Nghĩa tiếng Việt"),
    ("2", "Tiếng Nhật (kana / kanji / romaji)"),
])
def test_study_mode_menu_for_vocab_categories(sample_n5, run, category, choice, prompt):
    code, out = run(["-b", "2" if category == "1" else "10"], [category, choice, ":q"])
    assert "Cách học kanji đơn:" not in out
    assert "Cách học:" in out
    assert "2. Nhìn nghĩa tiếng Việt → viết tiếng Nhật" in out
    assert prompt in out


def test_study_mode_menu_skipped_when_mode_given(sample_n5, run):
    code, out = run(["-t", "1", "-b", "2", "--mode", "vj"], [":q"])
    assert "Cách học:" not in out
    assert "Tiếng Nhật (kana / kanji / romaji)" in out


def test_single_kanji_is_studied_by_page(sample_n5, run):
    code, out = run(["-t", "2", "--mode", "jv"], ["8", "2", ":q"])
    assert "Các trang hiện có:" in out
    assert "Trang 1 (1 chữ)   Trang 2 (1 chữ)" in out
    assert "Chọn trang" in out
    assert "Không có trang '8'" in out
    assert "N5 · Kanji đơn · trang 2 · 1 thẻ" in out
    assert "本" in out and "学" not in out.split("trang 2 · 1 thẻ")[1]


def test_kanji_stats_by_page(sample_n5, run):
    code, out = run(["--stats", "-t", "2"])
    assert "N5 · Kanji đơn · tất cả các trang: 2 chữ" in out
    assert "Theo trang:" in out and "Trang 1" in out
