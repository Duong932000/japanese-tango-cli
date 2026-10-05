# Học từ vựng tiếng Nhật theo bài

Tool chạy trên terminal, hiện từ vựng ngẫu nhiên theo từng bài học để luyện nhớ nhanh:

- Hiện **nghĩa tiếng Việt**: bạn viết từ tiếng Nhật (gõ kana, kanji hoặc romaji).
- Hiện **từ tiếng Nhật** (kanji hoặc hiragana): bạn nói và gõ nghĩa tiếng Việt.

Tool chỉ dùng thư viện có sẵn của Python, không cần mạng, chạy nhẹ trên máy cá nhân. Tiến độ được lưu lại, từ đã thuộc sẽ được ôn giãn ra theo lịch, từ hay sai sẽ được ôn lại sớm.

## Yêu cầu

- Python 3.10 trở lên
- Linux hoặc macOS (để chạy `run.sh`). Trên Windows có thể chạy trực tiếp `python vocab.py`.

## Bắt đầu nhanh

```bash
git clone <địa-chỉ-repo> japanese
cd japanese
./run.sh
```

Lần chạy đầu, `run.sh` tự tạo môi trường ảo `.venv`. Sau đó tool liệt kê các bài hiện có và hỏi bạn muốn học bài nào:

```
Các bài hiện có:
  Bài 1 (66 từ)   Bài 2 (40 từ)
Chọn bài (vd: 3 · 1-5 · 1,3,7 · all):
```

| Bạn nhập | Ý nghĩa |
|---|---|
| `3` | chỉ học bài 3 |
| `1-5` | học từ bài 1 đến bài 5 |
| `1,3,7` | học các bài 1, 3 và 7 |
| `all` | học tất cả các bài |

## Trong lúc học

Mỗi thẻ hiện một từ hoặc một nghĩa. Bạn có hai cách trả lời:

1. **Gõ câu trả lời rồi Enter.** Tool tự chấm.
   - Tiếng Nhật: gõ kanji, hiragana, katakana hoặc romaji đều được. Romaji được chấm dễ: `gakkou` hay `gakko`, `shi` hay `si`, `wa` hay `ha` đều đúng.
   - Tiếng Việt: gõ một trong các nghĩa là đủ. Gõ thiếu dấu vẫn tính đúng nhưng có ghi chú.
   - Bỏ qua dấu cách, `～` và dấu câu: `この ひと` gõ `このひと` cũng đúng.
2. **Bấm Enter ngay** để xem đáp án, rồi tự chấm `y` (nhớ) hoặc `n` (quên). Dùng cách này khi bạn muốn viết ra giấy hoặc nói thành tiếng.

Nếu tool chấm sai nhưng bạn trả lời đúng (ví dụ dùng từ đồng nghĩa), bấm `y` khi được hỏi để vẫn tính là đúng.

Từ trả lời sai sẽ được hỏi lại thêm một lần trong cùng lượt học. Cuối lượt, tool in tỉ lệ đúng và danh sách từ cần ôn thêm.

**Thoát:** gõ `:q` rồi Enter, hoặc bấm `Ctrl+C`. Tiến độ đã được lưu sau mỗi câu, không bị mất.

## Các lệnh thường dùng

```bash
./run.sh                    # hỏi chọn bài rồi học
./run.sh -b 3               # học ngay bài 3
./run.sh -b 1-5 --mode vj   # bài 1–5, chỉ hỏi Việt → Nhật
./run.sh -b all             # ôn theo lịch: từ đến hạn trước, rồi thêm từ mới
./run.sh -b 2 --hard        # chỉ ôn những từ bài 2 bạn đã từng sai
./run.sh --stats            # xem tiến độ từng bài
./run.sh --help             # xem tất cả tùy chọn
```

| Tùy chọn | Tác dụng |
|---|---|
| `-b`, `--lesson` | chọn bài: `3`, `1-5`, `1,3,7`, `all` |
| `-l`, `--level` | chọn cấp độ, ví dụ `N4` (mặc định tự chọn nếu chỉ có một cấp) |
| `--mode` | `vj` Việt→Nhật, `jv` Nhật→Việt, `mix` trộn ngẫu nhiên (mặc định) |
| `--script` | khi hiện tiếng Nhật: `kanji`, `kana`, hoặc `mix` (mặc định) |
| `--kind` | chỉ học từ `kanji`, `hiragana` hoặc `katakana` |
| `-n` | số thẻ mỗi lượt |
| `--new` | khi chọn `all`: số từ mới tối đa mỗi lượt (mặc định 10) |
| `--random` | random tự do, bỏ qua lịch ôn |
| `--hard` | chỉ ôn các từ đã từng sai |
| `--stats` | xem thống kê |
| `--reset` | xóa toàn bộ tiến độ (có hỏi xác nhận) |

### Học một bài và học `all` khác nhau thế nào

- **Chọn một hoặc vài bài:** hiện **toàn bộ** từ của các bài đó theo thứ tự ngẫu nhiên. Phù hợp để học bài mới hoặc ôn lại bài cũ trước buổi học.
- **Chọn `all`:** dùng lịch ôn (hộp Leitner), mỗi lượt 20 thẻ. Từ đến hạn được ôn trước, sau đó thêm tối đa 10 từ mới. Phù hợp để ôn hằng ngày.

### Lịch ôn

Mỗi từ nằm trong một "hộp" từ 1 đến 5. Trả lời đúng thì lên một hộp và chờ lâu hơn mới gặp lại. Trả lời sai thì về hộp 1 và được ôn lại ngay trong ngày.

| Hộp | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Gặp lại sau | 1 ngày | 3 ngày | 7 ngày | 14 ngày | 30 ngày |

Từ ở hộp 4 trở lên được tính là **đã thuộc** trong phần thống kê.

## Dữ liệu từ vựng

```
data/
├── N5/
│   ├── kanji.csv
│   ├── hiragana.csv
│   └── katakana.csv
└── N4/              # thêm khi học tới, cùng định dạng
```

Mỗi cấp độ là một thư mục trong `data/`. Tool tự nhận thư mục mới. Mỗi dòng là một từ, cột `lesson` là số bài theo giáo trình của trung tâm.

**kanji.csv**: từ có chứa chữ kanji

```csv
lesson,kanji,kana,meaning_vi
3,学生,がくせい,học sinh/sinh viên
3,食べます,たべます,ăn
```

**hiragana.csv** và **katakana.csv**: từ chỉ viết bằng hiragana hoặc katakana

```csv
lesson,kana,meaning_vi
1,わたし,tôi
1,テレビ,tivi
```

Quy tắc:

- File lưu dạng UTF-8. Dòng đầu tiên là tiêu đề, giữ nguyên tên cột như trên.
- `lesson` chỉ ghi số (`3`, không ghi `Bài 3`).
- `kana` là cách đọc của cả từ, kể cả phần okurigana.
- Nhiều nghĩa ngăn cách bằng `/`, ghi chú đặt trong ngoặc tròn: `bố (của mình)`.
- Không dùng dấu phẩy trong ô (dấu phẩy là ký tự ngăn cột).
- Dòng có `lesson` bắt đầu bằng `#` được coi là ghi chú và bị bỏ qua.
- Cùng một từ có thể xuất hiện ở nhiều bài. Tool gộp lại và tính chung tiến độ.

Dòng thiếu dữ liệu sẽ bị bỏ qua, tool in số dòng để bạn sửa. Sau khi thêm bài mới, chạy `./run.sh test` để kiểm tra lỗi định dạng (xem phần dưới).

`samples/n5_tonghop.csv` là danh sách N5 tổng hợp khoảng 550 từ, chỉ để tham khảo. Tool không đọc file này.

## Tiến độ học

Tiến độ được lưu trong `progress.json` ở thư mục gốc. File này nằm trong `.gitignore` vì là dữ liệu cá nhân. Nếu muốn đồng bộ tiến độ giữa nhiều máy qua git, xóa dòng `progress.json` trong `.gitignore`.

Xóa tiến độ: `./run.sh --reset`.

## Chạy test

```bash
./run.sh test              # chạy toàn bộ test
./run.sh test -k romaji    # chỉ chạy test có tên chứa "romaji"
./run.sh test -v           # in chi tiết từng test
```

Lần đầu, `run.sh` tự cài `pytest` vào `.venv` (cần mạng một lần). Các test nằm trong `tests/`:

| File | Kiểm tra |
|---|---|
| `test_romaji.py` | chuyển kana sang romaji và các cách gõ romaji tương đương |
| `test_checking.py` | chấm đáp án tiếng Nhật và tiếng Việt |
| `test_data.py` | đọc file CSV, gộp từ trùng, phân tích lựa chọn bài |
| `test_schedule.py` | lịch ôn Leitner, chọn thẻ, lưu và đọc tiến độ |
| `test_cli.py` | chạy thử cả lượt học với câu trả lời giả lập |
| `test_real_data.py` | kiểm tra **dữ liệu thật** trong `data/`: tiêu đề, ô thiếu, số bài, kanji/kana đúng cột, từ lặp trong cùng bài |

Các test dùng thư mục tạm nên không đụng tới `data/` hay `progress.json` thật, trừ `test_real_data.py` chỉ đọc dữ liệu thật để báo lỗi.

## Cấu trúc thư mục

```
japanese/
├── vocab.py               # toàn bộ chương trình
├── run.sh                 # chạy tool / test trong .venv
├── data/                  # từ vựng theo cấp độ và bài
├── samples/               # danh sách tham khảo, không được tool đọc
├── tests/                 # bộ test pytest
├── requirements-dev.txt   # thư viện cho test (pytest)
├── pytest.ini
└── progress.json          # tiến độ học (tự tạo, không đưa lên git)
```
