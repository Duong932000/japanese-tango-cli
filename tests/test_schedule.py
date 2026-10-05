from datetime import date, timedelta

import pytest

import vocab
from vocab import Word

TODAY = date(2026, 10, 5)


def make_words(n):
    return [Word("", f"かな{i}", f"nghĩa {i}", "hiragana") for i in range(n)]


def empty_progress():
    return {"words": {}, "history": {}}


def test_correct_answer_moves_up_one_box():
    progress, w = empty_progress(), make_words(1)[0]
    vocab.record(progress, w, True, TODAY)
    e = progress["words"][w.key]
    assert e["box"] == 1
    assert e["due"] == (TODAY + timedelta(days=vocab.INTERVALS[1])).isoformat()
    assert progress["history"][TODAY.isoformat()] == {"right": 1, "wrong": 0}


def test_box_is_capped():
    progress, w = empty_progress(), make_words(1)[0]
    for _ in range(vocab.MAX_BOX + 3):
        vocab.record(progress, w, True, TODAY)
    assert progress["words"][w.key]["box"] == vocab.MAX_BOX


def test_wrong_answer_resets_to_box_1_due_today():
    progress, w = empty_progress(), make_words(1)[0]
    for _ in range(3):
        vocab.record(progress, w, True, TODAY)
    vocab.record(progress, w, False, TODAY)
    e = progress["words"][w.key]
    assert (e["box"], e["due"], e["right"], e["wrong"]) == (1, TODAY.isoformat(), 3, 1)


def test_build_queue_due_first_then_limited_new():
    words = make_words(30)
    progress = empty_progress()
    for w in words[:5]:
        progress["words"][w.key] = {"box": 2, "due": TODAY.isoformat(), "right": 1, "wrong": 0}
    for w in words[5:8]:
        progress["words"][w.key] = {"box": 3, "due": "2099-01-01", "right": 2, "wrong": 0}

    queue, n_due, n_new = vocab.build_queue(words, progress, n=20, new_limit=4, today=TODAY)
    assert (n_due, n_new) == (5, 22)
    assert len(queue) == 9
    keys = {w.key for w in queue}
    assert {w.key for w in words[:5]} <= keys
    assert not {w.key for w in words[5:8]} & keys


def test_build_queue_respects_session_size():
    words = make_words(30)
    progress = {"words": {w.key: {"box": 1, "due": TODAY.isoformat(), "right": 0, "wrong": 1}
                          for w in words}, "history": {}}
    queue, _, _ = vocab.build_queue(words, progress, n=10, new_limit=10, today=TODAY)
    assert len(queue) == 10


def test_hard_queue_only_words_with_mistakes():
    words = make_words(5)
    progress = empty_progress()
    progress["words"][words[0].key] = {"box": 1, "due": "x", "right": 0, "wrong": 3}
    progress["words"][words[1].key] = {"box": 3, "due": "x", "right": 5, "wrong": 0}
    assert vocab.build_hard_queue(words, progress, 10) == [words[0]]


def test_streak():
    days = lambda *offsets: {(TODAY - timedelta(days=d)).isoformat(): {} for d in offsets}
    assert vocab.streak(days(0, 1, 2), TODAY) == 3
    assert vocab.streak(days(1, 2), TODAY) == 2
    assert vocab.streak(days(0, 2), TODAY) == 1
    assert vocab.streak({}, TODAY) == 0


def test_progress_roundtrip(data_dir):
    progress, w = empty_progress(), make_words(1)[0]
    vocab.record(progress, w, True, TODAY)
    vocab.save_progress(progress)
    assert vocab.load_progress() == progress


@pytest.mark.parametrize("content", [None, "", "  \n"])
def test_missing_or_empty_progress_starts_fresh(data_dir, content):
    if content is not None:
        vocab.PROGRESS_FILE.write_text(content, encoding="utf-8")
    assert vocab.load_progress() == {"words": {}, "history": {}}


def test_corrupt_progress_stops_without_overwriting(data_dir):
    vocab.PROGRESS_FILE.write_text("{broken", encoding="utf-8")
    with pytest.raises(SystemExit):
        vocab.load_progress()
    assert vocab.PROGRESS_FILE.read_text(encoding="utf-8") == "{broken"
