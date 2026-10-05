import pytest

from vocab import Word, check_jp, check_vi, vi_alternatives


def word(kana, meaning, kanji=""):
    return Word(kanji, kana, meaning, "kanji-vocab" if kanji else "hiragana")


@pytest.mark.parametrize("w, answer, expected", [
    (word("がくせい", "học sinh", "学生"), "学生", True),
    (word("がくせい", "học sinh", "学生"), "がくせい", True),
    (word("がくせい", "học sinh", "学生"), "ガクセイ", True),
    (word("がくせい", "học sinh", "学生"), "gakusei", True),
    (word("がくせい", "học sinh", "学生"), "がっせい", False),
    (word("わたし", "tôi"), "わたしたち", False),
    (word("わたし", "tôi"), "", False),
    (word("テレビ", "tivi"), "てれび", True),
    (word("テレビ", "tivi"), "terebi", True),
    # các kiểu ghi trong dữ liệu xuất từ claude.ai
    (word("この ひと", "người này"), "このひと", True),
    (word("この ひと", "người này"), "kono hito", True),
    (word("～さん", "anh～"), "さん", True),
    (word("～さん", "anh～"), "san", True),
    (word("だれ？", "ai?"), "だれ", True),
    (word("おしごとは？", "làm nghề gì?"), "oshigoto wa", True),
    (word("おはよう ございます", "chào"), "ohayo gozaimasu", True),
    (word("HO CHI MINH し", "TP Hồ Chí Minh"), "hochiminhshi", True),
])
def test_check_jp(w, answer, expected):
    assert bool(check_jp(answer, w)) is expected


@pytest.mark.parametrize("meaning, answer, expected", [
    ("cao/đắt", "cao", "exact"),
    ("cao/đắt", "Đắt", "exact"),
    ("cao/đắt", "dat", "noaccent"),
    ("cao/đắt", "to", None),
    ("bạn/anh/chị (ngôi thứ 2)", "bạn", "exact"),
    ("bạn/anh/chị (ngôi thứ 2)", "bạn/anh/chị", "exact"),
    ("(anh/chị) tên gì?", "tên gì", "exact"),
    ("(anh/chị) tên gì?", "(anh/chị) tên gì?", "exact"),
    ("bạn～/anh～/chị～", "chị", "exact"),
    ("chào (buổi sáng)", "chào", "exact"),
    ("chào (buổi sáng)", "chào buổi sáng", "exact"),
    ("ai?", "ai", "exact"),
    ("học sinh", "  học   sinh ", "exact"),
    ("học sinh", "", None),
])
def test_check_vi(meaning, answer, expected):
    assert check_vi(answer, word("x", meaning)) == expected


def test_vi_alternatives_does_not_split_inside_parentheses():
    alts = vi_alternatives("(anh/chị) tên gì?")
    assert "anh" not in alts
    assert "chị tên gì" not in alts


def kanji(char, hanviet, meaning):
    return Word(char, "", meaning, "kanji", hanviet=hanviet)


GAKU = kanji("学", "HỌC", "học")
SEI = kanji("生", "SINH", "sống/sinh ra")


@pytest.mark.parametrize("w, answer, expected", [
    (GAKU, "学", True),
    (GAKU, " 学 ", True),
    (GAKU, "がく", False),
    (GAKU, "gaku", False),
    (GAKU, "生", False),
    (GAKU, "", False),
])
def test_check_jp_single_kanji_only_accepts_the_character(w, answer, expected):
    assert bool(check_jp(answer, w)) is expected


@pytest.mark.parametrize("w, answer, expected", [
    (GAKU, "học", "exact"),
    (GAKU, "HỌC", "exact"),
    (SEI, "sinh", "exact"),
    (SEI, "sống", "exact"),
    (SEI, "sinh ra", "exact"),
    (SEI, "chết", None),
])
def test_check_vi_single_kanji_accepts_hanviet(w, answer, expected):
    assert check_vi(answer, w) == expected


def test_kanji_vocab_does_not_accept_hanviet_as_meaning():
    w = Word("先生", "せんせい", "thầy/cô", "kanji-vocab", hanviet="TIÊN SINH")
    assert check_vi("tiên sinh", w) is None
    assert check_vi("thầy", w) == "exact"


def test_single_kanji_key_and_summary():
    assert GAKU.key == "字|学"
    assert GAKU.summary() == "学 HỌC  —  học"
