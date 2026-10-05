import pytest

from vocab import kata_to_hira, norm_romaji, to_romaji


@pytest.mark.parametrize("kana, romaji", [
    ("わたし", "watashi"),
    ("がっこう", "gakkou"),
    ("ちょっと", "chotto"),
    ("きっさてん", "kissaten"),
    ("りゅうがくせい", "ryuugakusei"),
    ("しゅくだい", "shukudai"),
    ("じゃあ", "jaa"),
    ("ちゃわん", "chawan"),
    ("コーヒー", "koohii"),
    ("パーティー", "paatii"),
    ("フォーク", "fooku"),
    ("エレベーター", "erebeetaa"),
    ("この ひと", "kono hito"),
    ("おしごとは？", "oshigotowa？"),
    ("～さん", "～san"),
])
def test_to_romaji(kana, romaji):
    assert to_romaji(kana) == romaji


def test_ha_is_wa_only_before_question_mark():
    assert to_romaji("はな") == "hana"
    assert to_romaji("は") == "ha"


def test_kata_to_hira():
    assert kata_to_hira("テレビ") == "てれび"
    assert kata_to_hira("コーヒー") == "こーひー"
    assert kata_to_hira("学生がくせい") == "学生がくせい"


@pytest.mark.parametrize("a, b", [
    ("shi", "si"),
    ("tsukue", "tukue"),
    ("ji", "zi"),
    ("ja", "zya"),
    ("fuku", "huku"),
    ("gakkou", "gakko"),
    ("toukyou", "tōkyō"),
    ("matcha", "maccha"),
    ("oshigotowa", "oshigotoha"),
    ("Kono Hito", "konohito"),
])
def test_norm_romaji_accepts_variants(a, b):
    assert norm_romaji(a) == norm_romaji(b)


def test_norm_romaji_keeps_small_tsu():
    assert norm_romaji("gakou") != norm_romaji("gakkou")
