Tôi gửi ảnh chụp trang từ vựng (たんご) trong giáo trình của trung tâm tiếng Nhật. Hãy đọc ảnh và tạo **4 file CSV** để tôi tải về, dùng cho một tool học từ vựng. Tool đọc file bằng máy, nên định dạng phải chính xác tuyệt đối.

## Thông tin của đợt này
- Cấp độ: N5
- Bài: [ghi số bài, ví dụ 4. Nếu ảnh có nhiều bài thì lấy số bài in ở góc trang, ví dụ 第4課 = bài 4]

## Cách giáo trình trình bày
- Từ vựng được in bằng hiragana, kèm nghĩa tiếng Việt.
- Một số từ có **âm Hán Việt in hoa trong ngoặc** ở cột bên phải, ví dụ `(TIÊN SINH)`, `(HỌC HIỆU)`. Đây là những từ trung tâm dạy chữ kanji. Giáo trình **không in chữ kanji**, bạn phải tự điền chữ kanji đúng cho các từ này.
- Từ **gạch chân** là từ ngoại lai, thực tế viết bằng katakana (ví dụ べとなむ gạch chân = ベトナム).
- Cả phần chính và phần 【PHẦN MỞ RỘNG】 đều lấy hết.

## 4 file cần tạo

### 1. hiragana.csv: mọi từ không gạch chân, giữ nguyên chữ hiragana như trong sách
```
lesson,kana,meaning_vi
4,せんせい,thầy/cô
4,なんですか？,là cái gì?
```
Từ có ghi Hán Việt **vẫn phải có trong file này** (dạng hiragana), đồng thời có thêm trong kanji-vocab.csv.

### 2. katakana.csv: các từ gạch chân, chuyển sang katakana
```
lesson,kana,meaning_vi
4,ベトナム,Việt Nam
4,カメラ,máy chụp hình
```
Nếu chỉ một phần của từ gạch chân (ví dụ けしごむ chỉ gạch chân ごむ) thì chỉ chuyển phần đó: けしゴム.

### 3. kanji-vocab.csv: chỉ các từ có ghi âm Hán Việt trong sách
```
lesson,kanji,kana,hanviet,meaning_vi
4,先生,せんせい,TIÊN SINH,thầy/cô
4,自転車,じてんしゃ,TỰ CHUYỂN XA,xe đạp
4,お菓子,おかし,QUẢ TỬ,bánh kẹo
```
- `kanji`: cách viết kanji chuẩn của từ, giữ phần kana đi kèm (お菓子, 何番ですか？).
- `kana`: giống hệt cách viết hiragana trong sách.
- `hanviet`: chép **đúng như sách in**, viết hoa, bỏ ngoặc. Không tự sửa (sách ghi NGÂN HÀNH thì giữ NGÂN HÀNH).

### 4. kanji.csv: từng chữ kanji đơn xuất hiện trong kanji-vocab.csv của bài này
```
lesson,kanji,hanviet,meaning_vi
4,先,TIÊN,trước
4,生,SINH,sống/sinh ra
4,師,SƯ,thầy/người có chuyên môn
```
- Mỗi dòng **đúng một chữ kanji**. Mỗi chữ chỉ một dòng trong mỗi bài.
- Liệt kê **tất cả** các chữ có trong kanji-vocab.csv của bài này, kể cả chữ đã gặp ở bài trước.
- `hanviet`: âm Hán Việt của chữ đó, viết hoa, khớp với âm sách dùng trong từ (先生 = TIÊN SINH thì 先 = TIÊN).
- Không ghi âm On, âm Kun hay cách đọc nào khác.
- `meaning_vi`: nghĩa ngắn gọn của riêng chữ đó.

## Quy tắc chung cho cả 4 file
1. Dòng đầu tiên là tiêu đề, giữ đúng tên và thứ tự cột như mẫu, không thêm cột.
2. `lesson` chỉ ghi số (ví dụ `4`), không ghi "Bài 4".
3. `meaning_vi`: dùng đúng nghĩa tiếng Việt trong sách. Nhiều nghĩa ngăn cách bằng `/`. Phần giải thích nhỏ trong sách thì đặt trong ngoặc tròn, ví dụ `cái này (chỉ vật gần người nói)`.
4. **Không dùng dấu phẩy `,` trong bất kỳ ô nào** (dấu phẩy trong sách thì đổi thành `/`). Không dùng dấu ngoặc kép.
5. Giữ nguyên ký hiệu `～` và dấu `？` như trong sách.
6. Không thêm romaji, số thứ tự, cột loại từ (N), dòng trống hay câu ví dụ.
7. Không bỏ sót từ nào trong ảnh, kể cả các từ không có số thứ tự.
8. File không có dòng nào thì vẫn tạo với chỉ dòng tiêu đề.
9. Mã hóa UTF-8.

## Sau khi tạo file
- Cho tôi tải về 4 file: `hiragana.csv`, `katakana.csv`, `kanji-vocab.csv`, `kanji.csv`.
- Kèm một bảng ghi số dòng của mỗi file, để tôi đối chiếu với ảnh.
- Liệt kê riêng những chỗ bạn **không chắc**: chữ mờ không đọc rõ, chữ kanji bạn tự điền mà có nhiều cách viết, âm Hán Việt của chữ đơn không khớp với sách. Không được tự đoán mà không báo.
