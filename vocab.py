#!/usr/bin/env python3
"""Học từ vựng tiếng Nhật N5 bằng thẻ ngẫu nhiên trên terminal.

Chạy: python3 vocab.py --help
"""

import argparse
import csv
import json
import os
import random
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROGRESS_FILE = BASE_DIR / "progress.json"
KINDS = ("hiragana", "katakana", "kanji")

# Hộp Leitner: trả lời đúng thì lên hộp, số ngày chờ trước khi gặp lại tăng dần.
INTERVALS = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
MAX_BOX = 5
LEARNED_BOX = 4
REQUEUE_GAP = 4
MAX_REPEATS = 2

# ---------------------------------------------------------------- màu sắc

USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def _c(code):
    return lambda t: f"\033[{code}m{t}\033[0m" if USE_COLOR else str(t)


bold, dim, red, green, yellow, cyan = (_c(x) for x in ("1", "2", "31", "32", "33", "36"))

# ---------------------------------------------------------------- kana / romaji

_KANA = ("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめも"
         "やゆよらりるれろわをんがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
         "ゔぁぃぅぇぉゃゅょ")
_ROMA = ("a i u e o ka ki ku ke ko sa shi su se so ta chi tsu te to na ni nu ne no "
         "ha hi fu he ho ma mi mu me mo ya yu yo ra ri ru re ro wa o n "
         "ga gi gu ge go za ji zu ze zo da ji zu de do ba bi bu be bo pa pi pu pe po "
         "vu a i u e o ya yu yo").split()
KANA_ROMAJI = dict(zip(_KANA, _ROMA, strict=True))
SPECIAL_PAIRS = {
    "てぃ": "ti", "でぃ": "di", "でゅ": "dyu", "とぅ": "tu",
    "ふぁ": "fa", "ふぃ": "fi", "ふぇ": "fe", "ふぉ": "fo",
    "しぇ": "she", "じぇ": "je", "ちぇ": "che",
    "うぃ": "wi", "うぇ": "we", "うぉ": "wo",
    "ゔぁ": "va", "ゔぃ": "vi", "ゔぇ": "ve", "ゔぉ": "vo",
}


def kata_to_hira(text):
    return "".join(chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヶ" else ch for ch in text)


def is_katakana(text):
    return any("ァ" <= ch <= "ヺ" for ch in text)


def to_romaji(kana):
    s = kata_to_hira(kana)
    out, i, double_next = [], 0, False
    while i < len(s):
        ch, pair = s[i], s[i:i + 2]
        if ch == "っ":
            double_next, i = True, i + 1
            continue
        if ch == "ー":
            if out:
                out.append(out[-1][-1])
            i += 1
            continue
        if pair in SPECIAL_PAIRS:
            r, i = SPECIAL_PAIRS[pair], i + 2
        elif (len(pair) == 2 and pair[1] in "ゃゅょ" and ch != "い"
              and KANA_ROMAJI.get(ch, "").endswith("i")):
            head, vowel = KANA_ROMAJI[ch][:-1], KANA_ROMAJI[pair[1]][-1]
            r = head + vowel if head in ("sh", "ch", "j") else head + "y" + vowel
            i += 2
        elif ch == "は" and s[i + 1:i + 2] in ("？", "?"):
            r, i = "wa", i + 1
        else:
            r, i = KANA_ROMAJI.get(ch, ch), i + 1
        if double_next:
            r = "t" + r if r.startswith("ch") else r[0] + r
            double_next = False
        out.append(r)
    return "".join(out)


def strip_accents(text):
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D")


def norm_romaji(text):
    """Chuẩn hóa để chấp nhận nhiều cách gõ: shi/si, tsu/tu, ou/oo/ō..."""
    s = "".join(ch for ch in strip_accents(text.lower()) if ch.isalpha())
    for a, b in (("cch", "tch"), ("sh", "sy"), ("ch", "ty"), ("tsu", "tu"),
                 ("fu", "hu"), ("j", "zy"), ("syi", "si"), ("tyi", "ti"), ("zyi", "zi")):
        s = s.replace(a, b)
    for v in "aiueo":
        s = s.replace(v + v, v)
    # trợ từ は đọc là "wa": coi wa và ha là một khi so sánh
    return s.replace("ou", "o").replace("wa", "ha")


# Dấu cách, ～ và dấu câu trong dữ liệu không bắt người học phải gõ lại.
_JP_JUNK = re.compile(r"[\s~〜?!.,、。・…]")
_VI_JUNK = re.compile(r"[~〜?!.,…]")


def norm_jp(text):
    return kata_to_hira(_JP_JUNK.sub("", unicodedata.normalize("NFKC", text)))


def norm_vi(text):
    text = _VI_JUNK.sub(" ", unicodedata.normalize("NFKC", text).lower())
    return " ".join(text.split())


def vi_alternatives(meaning):
    """'(anh/chị) tên gì?' -> {'tên gì', 'anh/chị tên gì', ...}; 'cao/đắt' -> {'cao', 'đắt', ...}."""
    no_paren = re.sub(r"\(.*?\)", " ", meaning)
    alts = {norm_vi(meaning), norm_vi(no_paren), norm_vi(re.sub(r"[()]", " ", meaning))}
    alts |= {norm_vi(part) for part in no_paren.split("/")}
    alts.discard("")
    return alts


# ---------------------------------------------------------------- dữ liệu


@dataclass
class Word:
    kanji: str
    kana: str
    meaning: str
    kind: str
    lessons: list = field(default_factory=list)
    hira: str = field(init=False)
    romaji: str = field(init=False)

    def __post_init__(self):
        self.hira = kata_to_hira(self.kana)
        self.romaji = to_romaji(self.kana)

    @property
    def key(self):
        return f"{self.kanji}|{self.kana}"

    def display(self):
        return f"{self.kanji}【{self.kana}】" if self.kanji else self.kana


def lesson_sort_key(lesson):
    return (0, int(lesson), "") if lesson.isdigit() else (1, 0, lesson)


def list_levels():
    if not DATA_DIR.is_dir():
        return []
    return sorted(d.name for d in DATA_DIR.iterdir() if d.is_dir() and any(d.glob("*.csv")))


def load_level(level):
    """Đọc mọi file CSV trong data/<level>/. Một từ có thể thuộc nhiều bài."""
    words = {}
    for path in sorted((DATA_DIR / level).glob("*.csv")):
        with open(path, encoding="utf-8-sig", newline="") as f:
            for n, row in enumerate(csv.DictReader(f), start=2):
                lesson = (row.get("lesson") or "").strip()
                if lesson.startswith("#"):
                    continue
                kanji = (row.get("kanji") or "").strip()
                kana = (row.get("kana") or "").strip()
                meaning = (row.get("meaning_vi") or "").strip()
                if not (kana and meaning and lesson):
                    if any((v or "").strip() for v in row.values()):
                        print(yellow(f"Bỏ qua {level}/{path.name} dòng {n}: "
                                     "thiếu lesson, kana hoặc meaning_vi"))
                    continue
                if path.stem in KINDS:
                    kind = path.stem
                elif kanji:
                    kind = "kanji"
                else:
                    kind = "katakana" if is_katakana(kana) else "hiragana"
                w = words.setdefault(f"{kanji}|{kana}", Word(kanji, kana, meaning, kind))
                if lesson not in w.lessons:
                    w.lessons.append(lesson)
    return list(words.values())


def parse_lessons(text, available):
    """'3', '1-5', '1,3,7', 'all' -> tập các bài, hoặc None nếu là all."""
    text = text.strip().lower()
    if text in ("", "all", "a", "tất cả", "tat ca"):
        return None
    chosen = set()
    for part in text.replace(" ", "").split(","):
        m = re.fullmatch(r"(\d+)-(\d+)", part)
        if m:
            lo, hi = sorted((int(m[1]), int(m[2])))
            chosen |= {l for l in available if l.isdigit() and lo <= int(l) <= hi}
        elif part:
            match = next((l for l in available if l.lower() == part), None)
            if match is None:
                raise ValueError(f"Không có bài '{part}'")
            chosen.add(match)
    if not chosen:
        raise ValueError("Không có bài nào trong khoảng đã chọn")
    return chosen


def load_progress():
    text = PROGRESS_FILE.read_text(encoding="utf-8") if PROGRESS_FILE.exists() else ""
    if not text.strip():
        return {"words": {}, "history": {}}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        sys.exit(red(f"File {PROGRESS_FILE.name} bị lỗi. Sửa hoặc xóa nó rồi chạy lại."))
    data.setdefault("words", {})
    data.setdefault("history", {})
    return data


def save_progress(progress):
    tmp = PROGRESS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(progress, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, PROGRESS_FILE)


def record(progress, word, ok, today):
    e = progress["words"].setdefault(word.key, {"box": 0, "right": 0, "wrong": 0})
    if ok:
        e["box"] = min(e["box"] + 1, MAX_BOX)
        e["right"] += 1
        e["due"] = (today + timedelta(days=INTERVALS[e["box"]])).isoformat()
    else:
        e["box"] = 1
        e["wrong"] += 1
        e["due"] = today.isoformat()
    e["last"] = today.isoformat()
    day = progress["history"].setdefault(today.isoformat(), {"right": 0, "wrong": 0})
    day["right" if ok else "wrong"] += 1


# ---------------------------------------------------------------- chọn thẻ


def build_queue(words, progress, n, new_limit, today):
    due, new = [], []
    for w in words:
        e = progress["words"].get(w.key)
        if not e or e.get("box", 0) == 0:
            new.append(w)
        elif e["due"] <= today.isoformat():
            due.append(w)
    random.shuffle(due)
    due.sort(key=lambda w: progress["words"][w.key]["box"])
    random.shuffle(new)
    queue = due[:n]
    queue += new[:max(0, min(new_limit, n - len(queue)))]
    random.shuffle(queue)
    return queue, len(due), len(new)


def build_hard_queue(words, progress, n):
    hard = [w for w in words if progress["words"].get(w.key, {}).get("wrong", 0) > 0]
    hard.sort(key=lambda w: (progress["words"][w.key]["box"], -progress["words"][w.key]["wrong"]))
    queue = hard[:n]
    random.shuffle(queue)
    return queue


# ---------------------------------------------------------------- hỏi đáp


def read(prompt):
    try:
        return input(prompt)
    except EOFError:
        return None


def yes_no(prompt, default=None):
    while True:
        ans = read(prompt)
        if ans is None or ans.strip() == ":q":
            return None
        ans = ans.strip().lower()
        if ans in ("y", "c", "co", "có", "yes"):
            return True
        if ans in ("n", "k", "khong", "không", "no"):
            return False
        if ans == "" and default is not None:
            return default


def jp_prompt_text(word, script, dup_kana):
    if not word.kanji:
        return word.kana
    if script == "kanji" or word.hira in dup_kana:
        return word.kanji
    if script == "kana":
        return word.kana
    return random.choice((word.kanji, word.kana))


def check_jp(answer, word):
    a = norm_jp(answer)
    if not a:
        return False
    if a in (norm_jp(word.kanji), norm_jp(word.kana)):
        return True
    return a.isascii() and norm_romaji(a) == norm_romaji(word.romaji)


def check_vi(answer, word):
    """Trả về 'exact', 'noaccent' hoặc None."""
    a = norm_vi(answer)
    if not a:
        return None
    alts = vi_alternatives(word.meaning)
    if a in alts:
        return "exact"
    if strip_accents(a) in {strip_accents(x) for x in alts}:
        return "noaccent"
    return None


def reveal(word):
    print(f"    {bold(word.display())}  {dim(word.romaji)}  —  {word.meaning}\n")


def ask(word, direction, script, dup_kana, header):
    print(dim("─" * 48))
    if direction == "jv":
        print(f"{header} {dim('Nhật → Việt')}\n")
        print("    " + bold(cyan(jp_prompt_text(word, script, dup_kana))) + "\n")
        ans = read("Nghĩa tiếng Việt: ")
    else:
        print(f"{header} {dim('Việt → Nhật')}\n")
        print("    " + bold(yellow(word.meaning)) + "\n")
        ans = read("Tiếng Nhật (kana / kanji / romaji): ")
    if ans is None or ans.strip() == ":q":
        return None
    ans = ans.strip()

    if not ans:
        reveal(word)
        return yes_no("Bạn có nhớ đúng không? [y/n]: ")

    result = check_jp(ans, word) if direction == "vj" else check_vi(ans, word)
    if result:
        note = dim(" (đúng nhưng thiếu dấu)") if result == "noaccent" else ""
        print(green("✓ Đúng!") + note)
        reveal(word)
        return True
    print(red("✗ Chưa đúng."))
    reveal(word)
    return yes_no("Vẫn tính là đúng (đồng nghĩa / cách viết khác)? [y/N]: ", default=False)


def run_session(cards, progress, args, dup_kana, today):
    queue = [(w, False) for w in cards]
    total, done, right = len(cards), 0, 0
    missed, repeats = [], Counter()
    print(dim("Gõ câu trả lời, hoặc Enter để xem đáp án rồi tự chấm. Gõ :q để dừng.\n"))
    i = 0
    try:
        while i < len(queue):
            word, is_repeat = queue[i]
            i += 1
            direction = args.mode if args.mode != "mix" else random.choice(("vj", "jv"))
            header = yellow("[ôn lại]") if is_repeat else bold(f"[{done + 1}/{total}]")
            ok = ask(word, direction, args.script, dup_kana, header)
            if ok is None:
                break
            if not is_repeat:
                done += 1
                right += ok
                record(progress, word, ok, today)
                save_progress(progress)
                if not ok:
                    missed.append(word)
            if not ok and repeats[word.key] < MAX_REPEATS:
                repeats[word.key] += 1
                queue.insert(min(len(queue), i + REQUEUE_GAP), (word, True))
    except KeyboardInterrupt:
        print()
    save_progress(progress)

    print(dim("═" * 48))
    if done:
        print(bold(f"Kết quả: {right}/{done} đúng ({right * 100 // done}%)"))
    if missed:
        print(red("\nCác từ cần ôn thêm:"))
        for w in missed:
            print(f"  • {w.display()}  {dim(w.romaji)}  —  {w.meaning}")
    print()


# ---------------------------------------------------------------- thống kê


def streak(history, today):
    day = today if today.isoformat() in history else today - timedelta(days=1)
    count = 0
    while day.isoformat() in history:
        count += 1
        day -= timedelta(days=1)
    return count


def progress_bar(done, total, width=20):
    filled = done * width // total if total else 0
    return f"{green('█' * filled)}{dim('░' * (width - filled))} {done}/{total}"


def is_learned(progress, word):
    return progress["words"].get(word.key, {}).get("box", 0) >= LEARNED_BOX


def show_stats(words, progress, today, title, by_lesson):
    boxes = Counter()
    due = 0
    for w in words:
        e = progress["words"].get(w.key)
        box = e.get("box", 0) if e else 0
        boxes[box] += 1
        if e and box > 0 and e["due"] <= today.isoformat():
            due += 1
    learned = sum(boxes[b] for b in range(LEARNED_BOX, MAX_BOX + 1))

    print(bold(f"\n{title}: {len(words)} từ"))
    print(f"Đã thuộc (hộp {LEARNED_BOX}+): {progress_bar(learned, len(words), 30)}")
    print(f"Chưa học: {boxes[0]}   Đến hạn ôn hôm nay: {due}")
    print("Theo hộp: " + "  ".join(f"hộp {b}: {boxes[b]}" for b in range(1, MAX_BOX + 1)))
    by_kind = Counter(w.kind for w in words)
    print("Phân loại: " + "  ".join(f"{k}: {by_kind[k]}" for k in KINDS))

    if by_lesson:
        print(bold("\nTheo bài:"))
        for lesson, ws in by_lesson:
            done = sum(is_learned(progress, w) for w in ws)
            print(f"  Bài {lesson:<6} {progress_bar(done, len(ws))}")

    today_h = progress["history"].get(today.isoformat(), {"right": 0, "wrong": 0})
    print(f"\nHôm nay: {today_h['right']} đúng, {today_h['wrong']} sai   "
          f"Chuỗi ngày học: {streak(progress['history'], today)} ngày")

    worst = sorted((w for w in words if progress["words"].get(w.key, {}).get("wrong")),
                   key=lambda w: -progress["words"][w.key]["wrong"])[:10]
    if worst:
        print(red("\nHay sai nhất:"))
        for w in worst:
            e = progress["words"][w.key]
            print(f"  {e['wrong']:>2}× sai  {w.display()}  —  {w.meaning}")
    print()


# ---------------------------------------------------------------- chọn cấp độ / bài


def choose_level(levels, wanted):
    if wanted:
        match = next((l for l in levels if l.lower() == wanted.lower()), None)
        if match is None:
            sys.exit(red(f"Không có cấp độ {wanted}. Hiện có: {', '.join(levels)}"))
        return match
    if len(levels) == 1:
        return levels[0]
    while True:
        ans = read(f"Chọn cấp độ ({', '.join(levels)}): ")
        if ans is None or ans.strip() == ":q":
            sys.exit(0)
        match = next((l for l in levels if l.lower() == ans.strip().lower()), None)
        if match:
            return match


def choose_lessons(words, wanted):
    counts = Counter(l for w in words for l in w.lessons)
    available = sorted(counts, key=lesson_sort_key)
    if wanted is not None:
        try:
            return parse_lessons(wanted, available)
        except ValueError as e:
            sys.exit(red(f"{e}. Các bài hiện có: {', '.join(available)}"))
    print(bold("Các bài hiện có:"))
    print("  " + "   ".join(f"Bài {l} {dim(f'({counts[l]} từ)')}" for l in available))
    while True:
        ans = read("Chọn bài (vd: 3 · 1-5 · 1,3,7 · all): ")
        if ans is None or ans.strip() == ":q":
            sys.exit(0)
        try:
            return parse_lessons(ans, available)
        except ValueError as e:
            print(red(str(e)))


def lesson_label(level, lessons):
    if lessons is None:
        return f"{level} · tất cả các bài"
    return f"{level} · bài " + ", ".join(sorted(lessons, key=lesson_sort_key))


# ---------------------------------------------------------------- main


def main():
    p = argparse.ArgumentParser(
        description="Học từ vựng tiếng Nhật theo bài, bằng thẻ ngẫu nhiên.",
        epilog="Chọn một bài: học toàn bộ từ của bài đó. Chọn all: ôn các từ đến hạn "
               "trước, sau đó thêm từ mới.")
    p.add_argument("-l", "--level", help="cấp độ, ví dụ N5 (tên thư mục trong data/)")
    p.add_argument("-b", "--lesson", help="bài cần học: 3 · 1-5 · 1,3,7 · all")
    p.add_argument("-n", type=int, help="số thẻ mỗi lượt (mặc định: cả bài, hoặc 20 khi chọn all)")
    p.add_argument("--new", type=int, default=10,
                   help="khi chọn all: tối đa số từ mới mỗi lượt (mặc định 10)")
    p.add_argument("--mode", choices=("mix", "vj", "jv"), default="mix",
                   help="vj = Việt→Nhật, jv = Nhật→Việt, mix = ngẫu nhiên (mặc định)")
    p.add_argument("--script", choices=("mix", "kanji", "kana"), default="mix",
                   help="khi hiện tiếng Nhật: kanji, kana, hay ngẫu nhiên (mặc định)")
    p.add_argument("--kind", choices=("all",) + KINDS, default="all",
                   help="chỉ học một loại từ (tương ứng file kanji/hiragana/katakana.csv)")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--random", action="store_true",
                       help="random tự do trong các bài đã chọn, bỏ qua lịch ôn")
    group.add_argument("--hard", action="store_true", help="chỉ ôn các từ đã từng sai")
    group.add_argument("--stats", action="store_true", help="xem thống kê tiến độ")
    group.add_argument("--reset", action="store_true", help="xóa toàn bộ tiến độ")
    args = p.parse_args()

    if args.reset:
        if yes_no("Xóa toàn bộ tiến độ học? [y/N]: ", default=False):
            PROGRESS_FILE.unlink(missing_ok=True)
            print("Đã xóa.")
        return

    levels = list_levels()
    if not levels:
        sys.exit(red(f"Chưa có dữ liệu. Tạo thư mục {DATA_DIR}/N5 chứa các file CSV."))
    level = choose_level(levels, args.level)
    all_words = load_level(level)
    if not all_words:
        sys.exit(red(f"Chưa có từ nào trong data/{level}/. Điền từ vựng vào các file CSV."))
    dup_kana = {h for h, c in Counter(w.hira for w in all_words).items() if c > 1}

    if args.stats and args.lesson is None:
        lessons = None
    else:
        lessons = choose_lessons(all_words, args.lesson)
    words = [w for w in all_words
             if (args.kind == "all" or w.kind == args.kind)
             and (lessons is None or lessons.intersection(w.lessons))]
    if not words:
        sys.exit(red("Không có từ nào khớp lựa chọn."))

    label = lesson_label(level, lessons)
    today = date.today()
    progress = load_progress()

    if args.stats:
        by_lesson = None
        if lessons is None:
            names = sorted({l for w in words for l in w.lessons}, key=lesson_sort_key)
            by_lesson = [(l, [w for w in words if l in w.lessons]) for l in names]
        show_stats(words, progress, today, label, by_lesson)
        return

    if args.random:
        cards = random.sample(words, min(args.n or len(words), len(words)))
    elif args.hard:
        cards = build_hard_queue(words, progress, args.n or len(words))
        if not cards:
            print("Chưa có từ nào sai trong phần này. Học thêm đã nhé!")
            return
    elif lessons is not None:
        cards = random.sample(words, min(args.n or len(words), len(words)))
    else:
        cards, n_due, n_new = build_queue(words, progress, args.n or 20, args.new, today)
        print(dim(f"Đến hạn ôn: {n_due} từ · Chưa học: {n_new} từ"))
        if not cards:
            print("Hôm nay hết từ cần ôn và không còn từ mới. Dùng --random để luyện tự do.")
            return
    print(bold(f"\n{label} · {len(cards)} thẻ"))
    run_session(cards, progress, args, dup_kana, today)


if __name__ == "__main__":
    main()
