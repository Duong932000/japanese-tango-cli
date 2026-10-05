# Học từ vựng tiếng Nhật theo bài

Tool chạy trên terminal, hiện từ vựng ngẫu nhiên theo từng bài học để luyện nhớ nhanh:

- Hiện **nghĩa tiếng Việt**: bạn viết từ tiếng Nhật (gõ kana, kanji hoặc romaji).
- Hiện **từ tiếng Nhật** (kanji hoặc hiragana): bạn nói và gõ nghĩa tiếng Việt.
- Học **chữ kanji đơn**: nhìn chữ để nói âm Hán Việt và nghĩa, hoặc nhìn âm Hán Việt để viết chữ.

Tool chạy nhẹ trên máy cá nhân, không cần mạng. Chỉ cần Python. Pillow là tùy chọn, dùng để vẽ chữ kanji cỡ lớn. Tiến độ được lưu lại, từ đã thuộc sẽ được ôn giãn ra theo lịch, từ hay sai sẽ được ôn lại sớm.

## Yêu cầu

- Python 3.10 trở lên
- Linux hoặc macOS (để chạy `run.sh`). Trên Windows có thể chạy trực tiếp `python vocab.py`.

## Bắt đầu nhanh

```bash
git clone <địa-chỉ-repo> japanese
cd japanese
./run.sh
```

Lần chạy đầu, `run.sh` tự tạo môi trường ảo `.venv` và cài Pillow (thư viện vẽ chữ kanji cỡ lớn). Sau đó tool hỏi bạn muốn học loại thẻ nào:

```
Chọn loại thẻ:
  1. Từ vựng (hiragana/katakana) (166)
  2. Kanji đơn (67)
  3. Từ vựng kanji (49)
  4. Tất cả (282)
Chọn (1-4, Enter = 1):
```

Rồi hỏi bài nào:

```
Các bài hiện có:
  Bài 1 (105 từ)   Bài 2 (95 từ)   Bài 3 (104 từ)
Chọn bài (vd: 3 · 1-5 · 1,3,7 · all):
```

| Bạn nhập | Ý nghĩa |
|---|---|
| `3` | chỉ học bài 3 |
| `1-5` | học từ bài 1 đến bài 5 |
| `1,3,7` | học các bài 1, 3 và 7 |
| `all` | học tất cả các bài |

## Trong lúc học

Có bốn loại thẻ, tương ứng bốn file dữ liệu:

| Loại | Nhật → Việt | Việt → Nhật |
|---|---|---|
| hiragana / katakana | hiện `せんせい`, bạn gõ nghĩa | hiện `thầy/cô`, bạn viết `せんせい` |
| kanji-vocab (từ vựng kanji) | hiện `先生`, bạn gõ nghĩa | hiện `thầy/cô (TIÊN SINH)`, bạn viết `先生` |
| kanji (chữ đơn) | hiện `先`, bạn gõ âm Hán Việt `tiên` hoặc nghĩa | hiện `TIÊN — trước`, bạn viết `先` ra giấy rồi bấm Enter để tự chấm |

Đáp án hiện màu xanh lá. Ở đề bài Nhật → Việt, chữ có kanji được **vẽ cỡ lớn** bằng ký tự khối để dễ nhìn nét. Từ dài tự thu nhỏ cho vừa terminal. Nếu terminal quá hẹp, chưa cài Pillow hoặc máy không có font tiếng Nhật, tool hiện chữ cỡ thường. Tắt chữ lớn bằng `--no-big`.


Mỗi thẻ hiện một từ hoặc một nghĩa. Bạn có hai cách trả lời:

1. **Gõ câu trả lời rồi Enter.** Tool tự chấm.
   - Tiếng Nhật: gõ kanji, hiragana, katakana hoặc romaji đều được. Với chữ kanji đơn, chỉ nhận đúng chữ kanji đó. Romaji được chấm dễ: `gakkou` hay `gakko`, `shi` hay `si`, `wa` hay `ha` đều đúng.
   - Tiếng Việt: gõ một trong các nghĩa là đủ. Gõ thiếu dấu vẫn tính đúng nhưng có ghi chú.
   - Bỏ qua dấu cách, `～` và dấu câu: `この ひと` gõ `このひと` cũng đúng.
2. **Bấm Enter ngay** để xem đáp án, rồi tự chấm `y` (nhớ) hoặc `n` (quên). Dùng cách này khi bạn muốn viết ra giấy hoặc nói thành tiếng.

Nếu tool chấm sai nhưng bạn trả lời đúng (ví dụ dùng từ đồng nghĩa), bấm `y` khi được hỏi để vẫn tính là đúng.

Từ trả lời sai sẽ được hỏi lại thêm một lần trong cùng lượt học. Cuối lượt, tool in tỉ lệ đúng và danh sách từ cần ôn thêm.

**Thoát:** gõ `:q` rồi Enter, hoặc bấm `Ctrl+C`. Tiến độ đã được lưu sau mỗi câu, không bị mất.

## Các lệnh thường dùng

```bash
./run.sh                    # hỏi chọn bài rồi học
./run.sh -t 1 -b 3          # học ngay từ vựng bài 3, không hỏi menu
./run.sh -b 1-5 --mode vj   # bài 1–5, chỉ hỏi Việt → Nhật
./run.sh -b all             # ôn theo lịch: từ đến hạn trước, rồi thêm từ mới
./run.sh -b 2 --hard        # chỉ ôn những từ bài 2 bạn đã từng sai
./run.sh -t 2 -b 1-3        # luyện chữ kanji đơn bài 1–3
./run.sh --stats            # xem tiến độ từng bài
./run.sh --help             # xem tất cả tùy chọn
```

| Tùy chọn | Tác dụng |
|---|---|
| `-b`, `--lesson` | chọn bài (với kanji đơn là trang): `3`, `1-5`, `1,3,7`, `all` |
| `-l`, `--level` | chọn cấp độ, ví dụ `N4` (mặc định tự chọn nếu chỉ có một cấp) |
| `--mode` | `vj` Việt→Nhật, `jv` Nhật→Việt, `mix` trộn ngẫu nhiên (mặc định) |
| `--script` | từ vựng kanji hiện bằng `kanji` (mặc định), `kana`, hoặc `mix` |
| `-t`, `--kind` | loại thẻ: `1` từ vựng, `2` kanji đơn, `3` từ vựng kanji, `4` tất cả (hoặc `hiragana`, `katakana` để lọc riêng) |
| `--no-big` | không vẽ chữ kanji cỡ lớn |
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
│   ├── hiragana.csv      # từ viết bằng hiragana
│   ├── katakana.csv      # từ viết bằng katakana
│   ├── kanji-vocab.csv   # từ vựng kanji (từ có ghi âm Hán Việt trong giáo trình)
│   └── kanji.csv         # chữ kanji đơn
├── N4/                   # thêm khi học tới, cùng định dạng
└── raw/                  # ảnh chụp giáo trình (tool không đọc)
```

Mỗi cấp độ là một thư mục trong `data/`. Tool tự nhận thư mục mới. Mỗi dòng là một thẻ, cột `lesson` là số bài theo giáo trình của trung tâm.

**hiragana.csv** và **katakana.csv**

```csv
lesson,kana,meaning_vi
1,せんせい,thầy/cô
2,カメラ,máy chụp hình
```

**kanji-vocab.csv**: từ vựng ghép từ chữ kanji. `hanviet` là âm Hán Việt của cả từ, chép đúng như giáo trình.

```csv
lesson,kanji,kana,hanviet,meaning_vi
1,先生,せんせい,TIÊN SINH,thầy/cô
2,自転車,じてんしゃ,TỰ CHUYỂN XA,xe đạp
```

**kanji.csv**: mỗi dòng một chữ kanji đơn (hoặc bộ thủ), kèm âm Hán Việt và nghĩa. Với file này, cột `lesson` là **số trang**: chọn Kanji đơn thì tool hỏi "Chọn trang", chọn `1` thì chỉ học các chữ có số 1, để mỗi ngày học từng phần nhỏ.

```csv
lesson,kanji,hanviet,meaning_vi
1,先,TIÊN,trước
1,生,SINH,sống/sinh ra
```

Mỗi bài liệt kê đủ các chữ kanji dùng trong kanji-vocab của bài đó, kể cả chữ đã có ở bài trước. Test sẽ báo nếu thiếu chữ nào.

Một từ thường có mặt ở cả `hiragana.csv` (thẻ せんせい) lẫn `kanji-vocab.csv` (thẻ 先生). Hai thẻ được học và tính tiến độ riêng, chọn loại ở menu đầu.

### Lấy dữ liệu từ ảnh giáo trình

File [prompt_claude_ai.md](prompt_claude_ai.md) là prompt để claude.ai đọc ảnh trang từ vựng và xuất ra đủ 4 file CSV đúng định dạng. Sửa số bài trong prompt, dán vào claude.ai kèm ảnh, rồi tải 4 file về. **Không chép đè lên `data/N5/`**: mỗi lần tải về chỉ có từ của bài mới, cần nối vào cuối các file hiện có. Sau đó chạy `./run.sh test` để kiểm tra.

Quy tắc:

- File lưu dạng UTF-8. Dòng đầu tiên là tiêu đề, giữ nguyên tên cột như trên.
- `lesson` chỉ ghi số (`3`, không ghi `Bài 3`).
- `kana` là cách đọc của cả từ, kể cả phần okurigana.
- Chữ kanji đơn và từ vựng kanji dùng một chữ (ví dụ 本 và 本【ほん】) là hai thẻ riêng.
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
| `test_cli.py` | chạy thử cả lượt học với câu trả lời giả lập, menu chọn loại và bài |
| `test_big_text.py` | vẽ chữ kanji cỡ lớn (bỏ qua nếu chưa cài Pillow hoặc thiếu font) |
| `test_real_data.py` | kiểm tra **dữ liệu thật** trong `data/`: tiêu đề, ô thiếu, số bài, kanji/kana đúng cột, mỗi dòng kanji.csv đúng một chữ, mỗi chữ trong kanji-vocab đều có trong kanji.csv, từ lặp trong cùng bài |

Các test dùng thư mục tạm nên không đụng tới `data/` hay `progress.json` thật, trừ `test_real_data.py` chỉ đọc dữ liệu thật để báo lỗi.

## Cấu trúc thư mục

```
japanese/
├── vocab.py               # toàn bộ chương trình
├── run.sh                 # chạy tool / test trong .venv
├── data/                  # từ vựng theo cấp độ và bài
├── prompt_claude_ai.md    # prompt để claude.ai chuyển ảnh giáo trình thành CSV
├── samples/               # danh sách tham khảo, không được tool đọc
├── tests/                 # bộ test pytest
├── requirements.txt       # Pillow (tùy chọn, để vẽ kanji cỡ lớn)
├── requirements-dev.txt   # thư viện cho test (pytest)
├── pytest.ini
└── progress.json          # tiến độ học (tự tạo, không đưa lên git)
```
