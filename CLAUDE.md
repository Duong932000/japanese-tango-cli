# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tổng quan

Tool CLI học từ vựng / kanji tiếng Nhật (N5…) theo bài, chạy trên terminal, giao diện và dữ liệu bằng tiếng Việt. Toàn bộ chương trình nằm trong một file [vocab.py](vocab.py) (Python ≥ 3.10, chỉ dùng thư viện chuẩn; Pillow là tùy chọn để vẽ kanji cỡ lớn). README, thông báo, docstring và tên test đều viết bằng tiếng Việt — giữ nguyên quy ước này khi sửa code.

## Lệnh thường dùng

```bash
./run.sh                       # chạy tool (tự tạo .venv, thử cài Pillow lần đầu)
./run.sh -t 1 -b 3 --mode jv   # tham số được chuyển thẳng cho vocab.py
./run.sh test                  # chạy toàn bộ pytest (tự cài requirements-dev.txt)
./run.sh test -k romaji        # lọc test theo tên
./run.sh test tests/test_cli.py::test_study_one_lesson_shows_only_its_words   # một test
./run.sh setup                 # chỉ tạo .venv và cài thư viện
```

`pytest.ini` đặt `pythonpath = . tests` nên test `import vocab` trực tiếp. Không có linter/build step.

## Kiến trúc vocab.py

Luồng `main()`: chọn level (thư mục con của `data/`) → `load_level()` → chọn loại thẻ (`CATEGORIES`/`-t`) → chọn bài (`parse_lessons`) → tạo hàng đợi thẻ → `run_session()` hỏi đáp, ghi tiến độ sau mỗi câu.

- **Nạp dữ liệu**: `load_level()` đọc mọi `data/<level>/*.csv`. Tên file (stem) quyết định `kind` (`hiragana`, `katakana`, `kanji`, `kanji-vocab`); file khác thì suy ra kind từ cột. Riêng `kanji.csv` là chữ đơn: không có `kana`, và cột `lesson` mang nghĩa **số trang** (UI gọi là "trang" thay vì "bài" — xem `units_for`). Dòng có `lesson` bắt đầu bằng `#` bị bỏ qua.
- **`Word` và khóa tiến độ**: `Word.key` là `字|<kanji>` cho chữ đơn, `<kanji>|<kana>` cho từ vựng. Các dòng trùng key giữa nhiều bài được gộp thành một `Word` với `lessons` là danh sách. `progress.json` lưu theo key này — đổi cách tạo key sẽ làm mất tiến độ người dùng. Vì key khác nhau nên thẻ せんせい (hiragana.csv) và 先生 (kanji-vocab.csv) có tiến độ riêng.
- **Lịch ôn Leitner**: `INTERVALS` hộp 1–5, `record()` cập nhật box/due/history; `build_queue()` chỉ dùng khi chọn `all` (đến hạn trước, thêm tối đa `--new` từ mới). Chọn bài cụ thể thì lấy ngẫu nhiên toàn bộ từ của bài, `--hard` dùng `build_hard_queue()`. Trong lượt, câu sai được chèn lại (`REQUEUE_GAP`, `MAX_REPEATS`).
- **Chấm đáp án**: `check_jp()` so sánh qua `norm_jp`/`kata_to_hira`/`norm_romaji` (romaji chấm lỏng: nguyên âm dài, shi/si, wa/ha…); chữ kanji đơn chỉ nhận đúng chữ đó. `check_vi()` tách nghĩa bằng `vi_alternatives` (ngăn cách `/`, bỏ ghi chú trong ngoặc), chấp nhận thiếu dấu qua `strip_accents`. `dup_kana` (các cách đọc trùng nhau giữa nhiều từ) buộc `jp_prompt_text()` hiện dạng kanji thay vì kana để đề bài không bị mơ hồ.
- **Chữ lớn**: `big_lines()` dùng Pillow + font CJK hệ thống (`FONT_CANDIDATES`) để vẽ kanji bằng ký tự khối; tự fallback về chữ thường nếu thiếu Pillow/font hoặc terminal hẹp. Bật qua biến toàn cục `BIG_TEXT` trong `main()`.
- **Tiến độ**: `save_progress()` ghi atomic (file `.tmp` rồi `os.replace`). `progress.json` nằm trong `.gitignore`.

## Test

- Fixture `data_dir` trong [tests/conftest.py](tests/conftest.py) monkeypatch `vocab.DATA_DIR` và `vocab.PROGRESS_FILE` sang `tmp_path`; `sample_n5` tạo bộ CSV mẫu. Test mới đụng tới dữ liệu/tiến độ phải dùng các fixture này để không chạm vào `data/` và `progress.json` thật.
- [tests/test_cli.py](tests/test_cli.py) chạy `vocab.main()` end-to-end với `sys.argv` và `input` giả lập (fixture `run`), rồi assert trên output.
- [tests/test_real_data.py](tests/test_real_data.py) kiểm tra **dữ liệu thật** trong `data/` (header, ô trống, kanji/kana đúng cột, mỗi dòng `kanji.csv` đúng một chữ, mọi chữ kanji xuất hiện trong `kanji-vocab.csv` đều có trong `kanji.csv` cùng cấp độ, trùng từ trong cùng bài). Sau khi sửa CSV luôn chạy `./run.sh test`.

## Dữ liệu

- Định dạng cột và quy tắc CSV (UTF-8, `lesson` chỉ là số, nhiều nghĩa ngăn bằng `/`, **không dùng dấu phẩy trong ô**) mô tả chi tiết trong [README.md](README.md#dữ-liệu-từ-vựng).
- Bài mới được tạo bằng cách đưa ảnh giáo trình (`data/raw/`) cùng [prompt_claude_ai.md](prompt_claude_ai.md) cho claude.ai; kết quả phải được **nối vào cuối** các CSV hiện có, không ghi đè. Giáo trình chỉ in hiragana + âm Hán Việt; chữ kanji do người/AI tự điền, còn `hanviet` phải chép đúng như sách.
- `samples/n5_tonghop.csv` và `data/raw/` chỉ để tham khảo, tool không đọc.
