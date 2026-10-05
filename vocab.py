#!/usr/bin/env python3
"""Học từ vựng và kanji tiếng Nhật theo bài, bằng thẻ ngẫu nhiên trên terminal.

Chạy: python3 vocab.py --help
"""

import argparse
import csv
import json
import os
import random
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROGRESS_FILE = BASE_DIR / "progress.json"
KINDS = ("hiragana", "katakana", "kanji", "kanji-vocab")

# Loại thẻ chọn ở menu đầu: số -> (tên, mô tả, các kind thuộc loại đó).
CATEGORIES = {
    "1": ("vocab", "Từ vựng (hiragana/katakana)", {"hiragana", "katakana"}),
    "2": ("kanji", "Kanji đơn", {"kanji"}),
    "3": ("kanji-vocab", "Từ vựng kanji", {"kanji-vocab"}),
    "4": ("all", "Tất cả", None),
}

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
    """Một thẻ học. kind 'kanji' là một chữ kanji đơn (có hanviet, không có kana);
    các kind khác là từ vựng."""
    kanji: str
    kana: str
    meaning: str
    kind: str
    hanviet: str = ""
    lessons: list = field(default_factory=list)
    hira: str = field(init=False)
    romaji: str = field(init=False)

    def __post_init__(self):
        self.hira = kata_to_hira(self.kana)
        self.romaji = to_romaji(self.kana)

    @property
    def is_single_kanji(self):
        return self.kind == "kanji"

    @property
    def key(self):
        return f"字|{self.kanji}" if self.is_single_kanji else f"{self.kanji}|{self.kana}"

    def display(self):
        if self.is_single_kanji:
            return f"{self.kanji} {self.hanviet}".strip()
        return f"{self.kanji}【{self.kana}】" if self.kanji else self.kana

    def summary(self):
        if self.is_single_kanji:
            return f"{self.display()}  —  {self.meaning}"
        return f"{self.display()}  {self.romaji}  —  {self.meaning}"


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
                get = lambda col: (row.get(col) or "").strip()
                kanji, kana, meaning = get("kanji"), get("kana"), get("meaning_vi")
                single = path.stem == "kanji"
                required = "kanji" if single else "kana"
                if not (lesson and meaning and (kanji if single else kana)):
                    if any((v or "").strip() for v in row.values()):
                        print(yellow(f"Bỏ qua {level}/{path.name} dòng {n}: "
                                     f"thiếu lesson, {required} hoặc meaning_vi"))
                    continue
                if path.stem in KINDS:
                    kind = path.stem
                elif kanji:
                    kind = "kanji-vocab"
                else:
                    kind = "katakana" if is_katakana(kana) else "hiragana"
                new = Word(kanji, "" if single else kana, meaning, kind, hanviet=get("hanviet"))
                w = words.setdefault(new.key, new)
                if lesson not in w.lessons:
                    w.lessons.append(lesson)
    return list(words.values())


def parse_lessons(text, available, unit="bài"):
    """'3', '1-5', '1,3,7', 'all' -> tập các bài (hoặc trang), hoặc None nếu là all."""
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
                raise ValueError(f"Không có {unit} '{part}'")
            chosen.add(match)
    if not chosen:
        raise ValueError(f"Không có {unit} nào trong khoảng đã chọn")
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
    if not word.kana:
        return word.kanji
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
    if a == norm_jp(word.kanji):
        return True
    if not word.kana:
        return False
    if a == norm_jp(word.kana):
        return True
    return a.isascii() and norm_romaji(a) == norm_romaji(word.romaji)


def check_vi(answer, word):
    """Trả về 'exact', 'noaccent' hoặc None. Chữ kanji đơn nhận cả âm Hán Việt."""
    a = norm_vi(answer)
    if not a:
        return None
    alts = vi_alternatives(word.meaning)
    if word.is_single_kanji and word.hanviet:
        alts |= vi_alternatives(word.hanviet)
    if a in alts:
        return "exact"
    if strip_accents(a) in {strip_accents(x) for x in alts}:
        return "noaccent"
    return None


# ---------------------------------------------------------------- chữ kanji cỡ lớn

BIG_TEXT = False  # main() bật khi chạy trên terminal thật
BIG_SIZE = 32
MIN_BIG_SIZE = 16
# kanji, 々 và bộ thủ (⺮, ⻌...)
KANJI_CHAR = re.compile(r"[\u4e00-\u9fff々\u2e80-\u2fdf]")
FONT_CANDIDATES = (
    "/usr/share/fonts/google-noto-sans-cjk-vf-fonts/NotoSansCJK-VF.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "C:/Windows/Fonts/YuGothM.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
)


def _font_paths():
    try:
        out = subprocess.run(["fc-match", "-f", "%{file}", "sans:lang=ja"],
                             capture_output=True, text=True, timeout=3).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        out = ""
    return ([out] if out else []) + list(FONT_CANDIDATES)


@lru_cache(maxsize=None)
def _big_font(size):
    """Font tiếng Nhật qua Pillow, hoặc None nếu thiếu Pillow / font."""
    try:
        from PIL import ImageFont
    except ImportError:
        return None
    for path in _font_paths():
        try:
            font = ImageFont.truetype(path, size)
        except OSError:
            continue
        try:
            font.set_variation_by_name("Regular")
        except Exception:
            pass
        if font.getmask("学").getbbox():
            return font
    return None


def big_lines(text, size=BIG_SIZE, threshold=128):
    """Vẽ text thành các dòng ký tự khối ▀▄█ (mỗi ô terminal = 1×2 điểm ảnh)."""
    font = _big_font(size)
    if font is None:
        return None
    from PIL import Image, ImageDraw
    width = size * len(text)
    img = Image.new("L", (width, size), 0)
    draw = ImageDraw.Draw(img)
    for i, ch in enumerate(text):
        left, top, right, bottom = draw.textbbox((0, 0), ch, font=font)
        draw.text((i * size + (size - (right - left)) / 2 - left,
                   (size - (bottom - top)) / 2 - top), ch, fill=255, font=font)
    px = img.load()
    lines = []
    for y in range(0, size, 2):
        row = []
        for x in range(width):
            top_on = px[x, y] > threshold
            bottom_on = y + 1 < size and px[x, y + 1] > threshold
            row.append("█" if top_on and bottom_on else "▀" if top_on else "▄" if bottom_on else " ")
        lines.append("".join(row).rstrip())
    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)
    return lines


def show_japanese(text):
    """In chữ tiếng Nhật ở đề bài; chữ có kanji được vẽ cỡ lớn nếu terminal đủ rộng."""
    if BIG_TEXT and KANJI_CHAR.search(text):
        columns = shutil.get_terminal_size().columns - 6
        size = min(BIG_SIZE, columns // len(text)) // 2 * 2
        lines = big_lines(text, size) if size >= MIN_BIG_SIZE else None
        if lines:
            print("\n".join("    " + cyan(line) for line in lines) + "\n")
            return
    print("    " + bold(cyan(text)) + "\n")


def reveal(word, direction="jv"):
    if word.is_single_kanji:
        if direction == "vj":
            show_japanese(word.kanji)
        print(f"    {bold(word.kanji)}  {green(f'{word.hanviet}  —  {word.meaning}')}\n")
        return
    extra = f"  ({word.hanviet})" if word.hanviet else ""
    print(f"    {bold(word.display())}  {green(f'{word.romaji}  —  {word.meaning}{extra}')}\n")


def ask(word, direction, script, dup_kana, header):
    print(dim("─" * 48))
    if direction == "jv":
        print(f"{header} {dim('Nhật → Việt')}\n")
        show_japanese(jp_prompt_text(word, script, dup_kana))
        ans = read("Âm Hán Việt hoặc nghĩa: " if word.is_single_kanji else "Nghĩa tiếng Việt: ")
    else:
        print(f"{header} {dim('Việt → Nhật')}\n")
        if word.is_single_kanji:
            print("    " + bold(yellow(f"{word.hanviet}  —  {word.meaning}")) + "\n")
            ans = read("Viết chữ kanji ra giấy rồi bấm Enter (hoặc gõ chữ): ")
        else:
            hint = dim(f"  ({word.hanviet})") if word.hanviet else ""
            print("    " + bold(yellow(word.meaning)) + hint + "\n")
            ans = read("Tiếng Nhật (kana / kanji / romaji): ")
    if ans is None or ans.strip() == ":q":
        return None
    ans = ans.strip()

    if not ans:
        reveal(word, direction)
        return yes_no("Bạn có nhớ đúng không? [y/n]: ")

    result = check_jp(ans, word) if direction == "vj" else check_vi(ans, word)
    if result:
        note = dim(" (đúng nhưng thiếu dấu)") if result == "noaccent" else ""
        print(green("✓ Đúng!") + note)
        reveal(word, direction)
        return True
    print(red("✗ Chưa đúng."))
    reveal(word, direction)
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
            print(f"  • {w.summary()}")
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


def show_stats(words, progress, today, title, by_lesson, unit="bài", noun="từ"):
    boxes = Counter()
    due = 0
    for w in words:
        e = progress["words"].get(w.key)
        box = e.get("box", 0) if e else 0
        boxes[box] += 1
        if e and box > 0 and e["due"] <= today.isoformat():
            due += 1
    learned = sum(boxes[b] for b in range(LEARNED_BOX, MAX_BOX + 1))

    print(bold(f"\n{title}: {len(words)} {noun}"))
    print(f"Đã thuộc (hộp {LEARNED_BOX}+): {progress_bar(learned, len(words), 30)}")
    print(f"Chưa học: {boxes[0]}   Đến hạn ôn hôm nay: {due}")
    print("Theo hộp: " + "  ".join(f"hộp {b}: {boxes[b]}" for b in range(1, MAX_BOX + 1)))
    by_kind = Counter(w.kind for w in words)
    print("Phân loại: " + "  ".join(f"{k}: {by_kind[k]}" for k in KINDS))

    if by_lesson:
        print(bold(f"\nTheo {unit}:"))
        for lesson, ws in by_lesson:
            done = sum(is_learned(progress, w) for w in ws)
            print(f"  {unit.capitalize()} {lesson:<6} {progress_bar(done, len(ws))}")

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


def units_for(kinds):
    """Cột đầu của kanji.csv là số trang; các file khác là số bài."""
    return ("trang", "chữ") if kinds == {"kanji"} else ("bài", "từ")


def choose_lessons(words, wanted, unit="bài", noun="từ"):
    counts = Counter(l for w in words for l in w.lessons)
    available = sorted(counts, key=lesson_sort_key)
    if wanted is not None:
        try:
            return parse_lessons(wanted, available, unit)
        except ValueError as e:
            sys.exit(red(f"{e}. Các {unit} hiện có: {', '.join(available)}"))
    print(bold(f"Các {unit} hiện có:"))
    print("  " + "   ".join(f"{unit.capitalize()} {l} {dim(f'({counts[l]} {noun})')}"
                           for l in available))
    while True:
        ans = read(f"Chọn {unit} (vd: 3 · 1-5 · 1,3,7 · all): ")
        if ans is None or ans.strip() == ":q":
            sys.exit(0)
        try:
            return parse_lessons(ans, available, unit)
        except ValueError as e:
            print(red(str(e)))


def category_for(wanted):
    """'1'..'4', tên loại (vocab, kanji, kanji-vocab, all) hoặc hiragana/katakana."""
    for number, (name, title, kinds) in CATEGORIES.items():
        if wanted in (number, name):
            return title, kinds
    if wanted in KINDS:
        return wanted, {wanted}
    return None


def in_category(word, kinds):
    return kinds is None or word.kind in kinds


def choose_category(words, wanted):
    if wanted is not None:
        found = category_for(wanted.strip().lower())
        if found is None:
            sys.exit(red(f"Không có loại '{wanted}'. Dùng 1-4 hoặc: "
                         + ", ".join(name for name, _, _ in CATEGORIES.values())))
        return found
    print(bold("Chọn loại thẻ:"))
    for number, (_, title, kinds) in CATEGORIES.items():
        count = sum(in_category(w, kinds) for w in words)
        print(f"  {number}. {title} {dim(f'({count})')}")
    while True:
        ans = read("Chọn (1-4, Enter = 1): ")
        if ans is None or ans.strip() == ":q":
            sys.exit(0)
        number = ans.strip() or "1"
        if number not in CATEGORIES:
            continue
        _, title, kinds = CATEGORIES[number]
        if any(in_category(w, kinds) for w in words):
            return title, kinds
        print(red(f"Chưa có thẻ nào thuộc loại {title}."))


KANJI_MODES = {
    "1": ("jv", "Nhìn chữ kanji → đoán âm Hán Việt / nghĩa"),
    "2": ("vj", "Nhìn âm Hán Việt → viết chữ kanji"),
    "3": ("mix", "Trộn cả hai"),
}


def choose_kanji_mode():
    print(bold("Cách học kanji đơn:"))
    for number, (_, title) in KANJI_MODES.items():
        print(f"  {number}. {title}")
    while True:
        ans = read("Chọn (1-3, Enter = 1): ")
        if ans is None or ans.strip() == ":q":
            sys.exit(0)
        number = ans.strip() or "1"
        if number in KANJI_MODES:
            return KANJI_MODES[number][0]


def lesson_label(level, category, lessons, unit="bài"):
    where = f"tất cả các {unit}" if lessons is None else \
        f"{unit} " + ", ".join(sorted(lessons, key=lesson_sort_key))
    return f"{level} · {category} · {where}"


# ---------------------------------------------------------------- main


def main():
    p = argparse.ArgumentParser(
        description="Học từ vựng tiếng Nhật theo bài, bằng thẻ ngẫu nhiên.",
        epilog="Chọn một bài: học toàn bộ từ của bài đó. Chọn all: ôn các từ đến hạn "
               "trước, sau đó thêm từ mới.")
    p.add_argument("-l", "--level", help="cấp độ, ví dụ N5 (tên thư mục trong data/)")
    p.add_argument("-b", "--lesson", help="bài cần học (với kanji đơn là trang): 3 · 1-5 · 1,3,7 · all")
    p.add_argument("-n", type=int, help="số thẻ mỗi lượt (mặc định: cả bài, hoặc 20 khi chọn all)")
    p.add_argument("--new", type=int, default=10,
                   help="khi chọn all: tối đa số từ mới mỗi lượt (mặc định 10)")
    p.add_argument("--mode", choices=("mix", "vj", "jv"),
                   help="vj = Việt→Nhật, jv = Nhật→Việt, mix = ngẫu nhiên (mặc định). "
                        "Với kanji đơn: jv = nhìn kanji đoán Hán Việt, vj = nhìn Hán Việt viết kanji")
    p.add_argument("--script", choices=("kanji", "kana", "mix"), default="kanji",
                   help="từ vựng kanji hiện bằng kanji (mặc định), kana, hay ngẫu nhiên")
    p.add_argument("-t", "--kind", metavar="LOẠI",
                   help="loại thẻ: 1 = từ vựng, 2 = kanji đơn, 3 = từ vựng kanji, 4 = tất cả "
                        "(hoặc vocab, kanji, kanji-vocab, all, hiragana, katakana)")
    p.add_argument("--no-big", action="store_true", help="không vẽ chữ kanji cỡ lớn")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--random", action="store_true",
                       help="random tự do trong các bài đã chọn, bỏ qua lịch ôn")
    group.add_argument("--hard", action="store_true", help="chỉ ôn các từ đã từng sai")
    group.add_argument("--stats", action="store_true", help="xem thống kê tiến độ")
    group.add_argument("--reset", action="store_true", help="xóa toàn bộ tiến độ")
    args = p.parse_args()

    global BIG_TEXT
    BIG_TEXT = sys.stdout.isatty() and not args.no_big

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
    dup_kana = {h for h, c in Counter(w.hira for w in all_words if w.hira).items() if c > 1}

    if args.stats and args.kind is None:
        category, kinds = CATEGORIES["4"][1:]
    else:
        category, kinds = choose_category(all_words, args.kind)
    pool = [w for w in all_words if in_category(w, kinds)]
    if not pool:
        sys.exit(red(f"Chưa có thẻ nào thuộc loại {category}."))
    if args.mode is None:
        args.mode = choose_kanji_mode() if kinds == {"kanji"} and not args.stats else "mix"
    unit, noun = units_for(kinds)

    if args.stats and args.lesson is None:
        lessons = None
    else:
        lessons = choose_lessons(pool, args.lesson, unit, noun)
    words = [w for w in pool if lessons is None or lessons.intersection(w.lessons)]
    if not words:
        sys.exit(red("Không có từ nào khớp lựa chọn."))

    label = lesson_label(level, category, lessons, unit)
    today = date.today()
    progress = load_progress()

    if args.stats:
        by_lesson = None
        if lessons is None:
            names = sorted({l for w in words for l in w.lessons}, key=lesson_sort_key)
            by_lesson = [(l, [w for w in words if l in w.lessons]) for l in names]
        show_stats(words, progress, today, label, by_lesson, unit, noun)
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
