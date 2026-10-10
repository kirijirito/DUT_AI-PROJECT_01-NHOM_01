# Quy trình Git và uv cho nhóm 5 người

## 1. Chuẩn bị lần đầu

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Nếu repo chưa có `uv.lock`, một thành viên chạy `uv lock` rồi commit file `uv.lock`. Sau đó mọi thành viên cùng dùng `uv sync` để đồng bộ môi trường.

## 2. Branch và PR

- Nhánh tích hợp: `develop`.
- Bản ổn định nộp/demo: `main`.
- Mỗi việc làm trên nhánh riêng được tạo từ `develop`:
  - `feature/models-json-store`
  - `feature/repositories`
  - `feature/order-kitchen`
  - `feature/payment-table-report`
  - `feature/gradio-ui`
  - `fix/queue-rebuild`
- Không push trực tiếp lên `main`/`develop`.
- Mỗi PR phải có: mục tiêu, file chính, cách test, ảnh hưởng API/Schema (nếu có), checklist tự kiểm tra.
- Ít nhất một thành viên khác review. Thành viên tạo PR không tự bỏ qua lỗi test.

## 3. Ví dụ commit

```text
feat(models): define order and table models
feat(repository): add menu hash map lookup
feat(kitchen): process queue in FIFO order
fix(payment): prevent checkout twice
 test(order): cover invalid quantity
 docs(team): clarify controller contract
```

Sửa khoảng trắng/tên biến cũng được commit, nhưng không tạo commit chỉ để spam lịch sử. Tránh commit `.venv`, cache, file tạm hoặc dữ liệu cá nhân.

## 4. Thứ tự ghép code

1. Contract/Model/JSON mẫu.
2. JsonStore và Repository.
3. Service và test đơn vị.
4. Controller.
5. UI Gradio gọi Controller.
6. Test tích hợp từ UI tới JSON.
7. Merge `develop` ổn định sang `main` và tag phiên bản demo nếu nhóm muốn.

**Không đợi đến ngày cuối mới tích hợp.** Ngay ngày 2–3, hãy chạy được một luồng nhỏ từ Controller tới Repository và JSON.

## 5. Definition of Done cho mỗi PR

- [ ] Code đúng phạm vi, không nhét nghiệp vụ vào UI.
- [ ] Hàm có tên rõ ràng, kiểu dữ liệu và lỗi có thể hiểu được.
- [ ] Có test hoặc lý do rõ ràng vì sao chưa thể test.
- [ ] `uv run pytest` chạy qua.
- [ ] `uv run ruff check .` chạy qua.
- [ ] Không commit secret, `.venv`, cache hoặc file tạm.
- [ ] Nếu đổi contract, cập nhật `docs/API_CONTRACT.md` và báo nhóm.
