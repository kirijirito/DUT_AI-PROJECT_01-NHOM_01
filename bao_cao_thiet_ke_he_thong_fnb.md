# BÁO CÁO THIẾT KẾ HỆ THỐNG & DANH SÁCH CÔNG VIỆC

## Hệ thống Quản lý Đơn hàng và Bàn ăn F&B

**Phiên bản:** 1.0 — Tài liệu thống nhất trước khi triển khai  
**Nhóm:** 5 thành viên  
**Công nghệ:** Python, `uv`, Git Flow, Gradio, JSON, Queue (`collections.deque`), Hash Map (`dict`)

---

## 1. Mục tiêu và phạm vi

Xây dựng ứng dụng quản lý nhà hàng đơn giản, cho phép nhân viên xem menu, tạo đơn theo bàn, chuyển món qua hàng đợi bếp, theo dõi trạng thái bàn, thanh toán và xem báo cáo doanh thu. Ứng dụng chạy trong một tiến trình, lưu dữ liệu vào file JSON và sử dụng Gradio làm giao diện.

### 1.1. Phạm vi phiên bản môn học

**Có trong phạm vi:**
- Xem menu và tra cứu món theo mã.
- Xem danh sách bàn, tra cứu bàn theo mã và trạng thái hiện tại.
- Tạo đơn, thêm món vào đơn đang mở.
- Xếp món vào Queue bếp; chuyển món từ `QUEUED` → `PREPARING` → `READY` → `SERVED`.
- Xem chi tiết đơn, tính trước hóa đơn, xác nhận thanh toán.
- Hủy đơn chưa bắt đầu chế biến theo quy tắc nghiệp vụ.
- Cập nhật bàn `AVAILABLE` / `OCCUPIED`.
- Báo cáo doanh thu theo ngày và các số liệu tổng quan cơ bản.
- Khởi tạo dữ liệu mẫu và khôi phục trạng thái từ JSON khi chạy lại.

**Chưa làm trong phiên bản đầu:** đăng nhập/phân quyền, nhiều chi nhánh, đặt bàn trước, tích hợp cổng thanh toán thật, đồng bộ nhiều máy/tiến trình, hóa đơn điện tử, tồn kho nguyên liệu, khuyến mãi phức tạp.

### 1.2. Nguyên tắc nghiệp vụ cần thống nhất

1. Mã định danh (`id`) là duy nhất; UI không tự sinh mã nghiệp vụ.
2. Giá tiền lưu bằng **số nguyên VND**, không dùng `float` để tránh sai số.
3. Mỗi bàn chỉ có tối đa một đơn `OPEN` tại một thời điểm.
4. Khi thêm món vào đơn, lưu `unit_price_vnd` và `item_name` tại thời điểm đặt. Hóa đơn cũ không đổi nếu giá menu thay đổi sau này.
5. Một dòng món với `quantity = n` là một ticket Queue, chứa số lượng `n`; không tạo `n` ticket riêng ở phiên bản đầu.
6. Queue xử lý theo FIFO (First In, First Out). Món đang `PREPARING` không còn nằm trong hàng đợi chờ.
7. Chỉ thanh toán đơn còn `OPEN`; mặc định yêu cầu mọi món đã đạt `READY` hoặc `SERVED`.
8. Không xóa vật lý đơn đã thanh toán khỏi dữ liệu nghiệp vụ. “Xóa đơn” trên giao diện nên được thể hiện là **Hủy đơn** nếu đơn chưa bắt đầu chế biến, hoặc **Đóng đơn** sau thanh toán. Lưu lịch sử để báo cáo và đối chiếu.
9. Dữ liệu được thiết kế cho **một tiến trình ứng dụng**. Chưa cam kết an toàn khi nhiều tiến trình cùng ghi một bộ file JSON.

---

## 2. Use Cases và luồng nghiệp vụ

### 2.1. Danh sách Use Case

| Mã | Use Case | Tác nhân | Input chính | Kết quả mong đợi |
|---|---|---|---|---|
| UC-01 | Xem/tra cứu menu | Nhân viên | `menu_item_id` hoặc yêu cầu xem menu | Danh sách món còn bán hoặc một món; tra cứu theo `dict` trung bình O(1) |
| UC-02 | Xem/tra cứu bàn | Nhân viên | `table_id` hoặc yêu cầu xem tất cả bàn | Bàn và trạng thái hiện tại; tra cứu theo `dict` trung bình O(1) |
| UC-03 | Tạo đơn | Nhân viên phục vụ | `table_id`, danh sách `{menu_item_id, quantity, note}` | Tạo đơn `OPEN`, bàn thành `OCCUPIED`, các món được thêm vào Queue |
| UC-04 | Thêm món vào đơn | Nhân viên phục vụ | `order_id`, danh sách món | Tạo các dòng món mới, cấp số Queue, lưu JSON và enqueue |
| UC-05 | Nhận món tiếp theo ở bếp | Nhân viên bếp | Không cần input hoặc chọn “Món tiếp theo” | Lấy ticket đầu Queue, đổi trạng thái món sang `PREPARING` |
| UC-06 | Cập nhật món bếp | Nhân viên bếp | `order_id`, `order_item_id`, trạng thái đích | Chuyển `PREPARING` → `READY` → `SERVED`; cập nhật JSON |
| UC-07 | Xem hóa đơn/thanh toán | Thu ngân | `order_id`, phương thức, giảm giá nếu có | Tính tổng từ snapshot giá, lưu `PAID`, tạo biên nhận, giải phóng bàn |
| UC-08 | Hủy đơn | Quản lý/nhân viên có quyền | `order_id`, lý do tùy chọn | Chỉ hủy nếu mọi món còn `QUEUED`; bỏ ticket khỏi Queue, đơn thành `CANCELLED`, bàn thành `AVAILABLE` |
| UC-09 | Xem báo cáo ngày | Quản lý | Ngày báo cáo | Doanh thu, số đơn đã thanh toán, giá trị trung bình đơn và top món nếu đủ dữ liệu |
| UC-10 | Khôi phục hệ thống | Hệ thống khi khởi động | Các file JSON hiện có | Nạp dữ liệu, dựng Hash Map, dựng lại Queue từ món `QUEUED`, kiểm tra tham chiếu |

### 2.2. Luồng chính: tạo đơn hàng

1. UI gửi `table_id` và danh sách món lên `OrderService`.
2. Service kiểm tra input: bàn tồn tại/còn trống, số lượng là số nguyên dương, món tồn tại và đang bán.
3. Service tra cứu món qua `MenuRepository.get_by_id()`; thao tác tra cứu dùng Hash Map.
4. Service tạo `Order` và các `OrderItem`, chụp tên/giá món tại thời điểm gọi.
5. Mỗi dòng món nhận `queue_seq` từ `StateRepository`, trạng thái ban đầu là `QUEUED`.
6. Lưu đơn vào JSON và chuyển bàn sang `OCCUPIED` với `current_order_id` trỏ tới đơn mới.
7. Đưa từng dòng món vào `KitchenQueue` theo `queue_seq`.
8. UI nhận đối tượng kết quả hoặc lỗi nghiệp vụ để hiển thị thông báo.

**Lưu ý tích hợp:** vì đơn và bàn nằm ở hai file JSON, các bước ghi cần được thực hiện theo thứ tự đã thống nhất và có xử lý bù khi lỗi. Với quy mô môn học, ghi file nguyên tử từng file và kiểm tra tính nhất quán lúc khởi động là đủ; không tuyên bố có giao dịch ACID giữa nhiều file.

### 2.3. Luồng chính: Queue bếp

1. `KitchenService.start_next_item()` nhìn đầu Queue bằng `peek()`.
2. Tìm đơn và dòng món tương ứng; nếu ticket đã cũ/không còn `QUEUED`, loại ticket cũ và tiếp tục.
3. Cập nhật trạng thái dòng món sang `PREPARING`, lưu đơn thành công rồi mới pop ticket khỏi Queue.
4. Bếp chọn “Hoàn thành” để chuyển `PREPARING` → `READY`.
5. Khi món được đưa ra bàn, nhân viên chuyển `READY` → `SERVED`.
6. Khi khởi động lại, chỉ dựng lại Queue từ các dòng có trạng thái `QUEUED`; các món `PREPARING`/`READY` không bị tự đưa trở lại hàng chờ.

### 2.4. Luồng chính: thanh toán và trạng thái bàn

1. UI chọn đơn `OPEN` và yêu cầu xem hóa đơn.
2. `PaymentService.preview_bill()` tính `subtotal = Σ(unit_price_vnd × quantity)`; xác thực giảm giá không âm và không vượt subtotal.
3. Khi xác nhận, `PaymentService.checkout()` kiểm tra lại trạng thái đơn và trạng thái món để tránh thanh toán đơn không hợp lệ.
4. Lưu `payment_method`, `paid_at`, `discount_vnd`, `total_vnd` và chuyển đơn thành `PAID`.
5. `TableService.release_table(table_id, order_id)` chỉ giải phóng bàn nếu `current_order_id` đúng với đơn vừa thanh toán.
6. UI hiển thị biên nhận và làm mới bảng bàn/đơn.

---

## 3. Kiến trúc phân lớp

### 3.1. Sơ đồ phụ thuộc

```text
┌─────────────────────────────────────────────────────┐
│ Frontend: Gradio Blocks                             │
│ pages.py / handlers.py / app.py                     │
└────────────────────────┬────────────────────────────┘
                         │ gọi Service, không gọi Repo
┌────────────────────────▼────────────────────────────┐
│ Controller & Service                                │
│ MenuService / OrderService / KitchenService         │
│ TableService / PaymentService / ReportService       │
└────────────────────────┬────────────────────────────┘
                         │ gọi interface Repository
┌────────────────────────▼────────────────────────────┐
│ Repository                                          │
│ MenuRepository / OrderRepository / TableRepository  │
│ StateRepository                                     │
│ CRUD, Hash Map index, chuyển Model ↔ JSON           │
└────────────────────────┬────────────────────────────┘
                         │ dùng JsonFileStore + Models
┌────────────────────────▼────────────────────────────┐
│ Database / Schema / Models                          │
│ dataclasses, enums, validation cơ bản, JSON files   │
│ data/seed + data/runtime                            │
└─────────────────────────────────────────────────────┘
```

**Quy tắc phụ thuộc:** lớp trên được gọi lớp dưới; lớp dưới không import UI. Repository không quyết định quy tắc thanh toán/bếp. UI không tính tiền, không tự sửa JSON và không tự quản lý Queue. Model không phụ thuộc Gradio.

### 3.2. Trách nhiệm từng lớp

| Lớp | Chịu trách nhiệm | Không được làm |
|---|---|---|
| Frontend | Nhận input, gọi service/handler, hiển thị bảng/kết quả/lỗi, refresh UI | Không chứa nghiệp vụ; không truy cập file JSON trực tiếp |
| Controller/Service | Validation nghiệp vụ, điều phối luồng, Queue và thanh toán | Không tự đọc/ghi file trực tiếp; không phụ thuộc Gradio |
| Repository | CRUD, tra cứu theo ID, lưu/nạp và cập nhật index | Không quyết định một đơn có được thanh toán/hủy hay không |
| Models/Schema | Kiểu dữ liệu, enum, trường bắt buộc, chuyển đổi dict | Không chứa UI hoặc luồng nghiệp vụ phức tạp |
| JsonFileStore | Đọc/ghi JSON dùng chung, ghi nguyên tử từng file | Không biết `Order`, `Table` hay quy tắc nghiệp vụ |

### 3.3. Xử lý lỗi thống nhất

Tạo các exception ở `domain/exceptions.py`:

- `ValidationError`: dữ liệu nhập không hợp lệ.
- `NotFoundError`: không tìm thấy menu item, bàn, đơn hoặc dòng món.
- `ConflictError`: bàn đang bận, trạng thái không cho phép chuyển, đơn đã thanh toán.
- `PersistenceError`: JSON lỗi, không ghi/đọc được file.

Service ném lỗi có thông điệp dễ hiểu. Handler của UI bắt lỗi nghiệp vụ và chuyển thành thông báo Gradio; không dùng `except Exception: pass`. Lỗi không dự kiến cần được log bằng `logging` và hiển thị thông báo chung, tránh để traceback lộ trong giao diện người dùng.

---

## 4. Cấu trúc thư mục đề xuất

```text
restaurant-fnb/
├── .github/
│   └── pull_request_template.md
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
├── README.md
├── data/
│   ├── seed/
│   │   ├── menu.json
│   │   └── tables.json
│   └── runtime/
│       └── .gitkeep
├── src/
│   └── restaurant_pos/
│       ├── __init__.py
│       ├── app.py                    # Chỉ lắp ráp và chạy Gradio
│       ├── bootstrap.py              # Dựng Store/Repo/Service và seed dữ liệu
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── models.py             # MenuItem, Table, Order, OrderItem, Receipt
│       │   ├── enums.py              # Trạng thái chuẩn hóa
│       │   └── exceptions.py         # Lỗi domain/service
│       ├── storage/
│       │   ├── __init__.py
│       │   └── json_store.py         # Đọc/ghi JSON mức thấp, atomic replace
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── menu_repository.py
│       │   ├── table_repository.py
│       │   ├── order_repository.py
│       │   └── state_repository.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── menu_service.py
│       │   ├── order_service.py
│       │   ├── kitchen_queue.py      # Cài đặt Queue bằng collections.deque
│       │   ├── kitchen_service.py
│       │   ├── table_service.py
│       │   ├── payment_service.py
│       │   └── report_service.py
│       └── ui/
│           ├── __init__.py
│           ├── handlers.py            # Adapter: UI input → Service → UI output
│           └── pages.py               # Gradio components/Blocks
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_json_store.py
│   ├── test_repositories.py
│   ├── test_kitchen_queue.py
│   ├── test_order_service.py
│   ├── test_payment_service.py
│   └── test_report_service.py
└── docs/
    └── architecture.md               # Có thể copy báo cáo này vào đây
```

### 4.1. Quy ước file runtime

- `data/seed/` chứa menu/bàn mẫu được commit lên Git.
- `data/runtime/` chứa dữ liệu thật trong lúc chạy: `menu.json`, `tables.json`, `orders.json`, `app_state.json`. Thư mục runtime được ignore để dữ liệu demo không làm bẩn Git.
- Khi chạy lần đầu, `bootstrap.py` copy seed sang runtime nếu file đích chưa tồn tại; không ghi đè dữ liệu runtime đã có.
- Các file runtime nếu chưa có được tạo với cấu trúc hợp lệ, ví dụ `orders.json` là `[]`, `app_state.json` là `{"next_queue_seq": 1}`.
- Đường dẫn dữ liệu phải được cấu hình tập trung; không viết đường dẫn tương đối khác nhau ở nhiều module.

### 4.2. Quy định cho `app.py`

`app.py` chỉ nên thực hiện các bước tương tự:

```python
from restaurant_pos.bootstrap import build_app_context
from restaurant_pos.ui.pages import build_demo


def main() -> None:
    context = build_app_context()
    demo = build_demo(context)
    demo.launch()


if __name__ == "__main__":
    main()
```

Không đặt `json.load`, công thức tính tiền, kiểm tra bàn hay logic Queue trong `app.py` hoặc callback Gradio. Callback được khai báo ở UI/handlers và chỉ gọi Service.

---

## 5. Thiết kế Models và JSON Schema

> Các đoạn dưới đây là **mẫu cấu trúc JSON** để cả nhóm thống nhất tên trường. Đây không phải bản JSON Schema Draft chính thức.

### 5.1. `menu.json`

```json
[
  {
    "id": "MI-001",
    "name": "Phở bò",
    "category": "Món chính",
    "price_vnd": 55000,
    "description": "Phở bò truyền thống",
    "is_available": true
  },
  {
    "id": "MI-002",
    "name": "Trà tắc",
    "category": "Đồ uống",
    "price_vnd": 18000,
    "description": "Trà tắc mát lạnh",
    "is_available": true
  }
]
```

**Bất biến:** `id` duy nhất; `price_vnd >= 0`; `is_available` là boolean; `name` không rỗng. Menu chỉ chứa dữ liệu hiện hành, còn đơn hàng giữ snapshot tên/giá để không ảnh hưởng lịch sử.

### 5.2. `tables.json`

```json
[
  {
    "id": "TBL-01",
    "name": "Bàn 01",
    "capacity": 4,
    "status": "AVAILABLE",
    "current_order_id": null
  },
  {
    "id": "TBL-02",
    "name": "Bàn 02",
    "capacity": 2,
    "status": "OCCUPIED",
    "current_order_id": "ORD-20261010-A1B2"
  }
]
```

**Bất biến:** `capacity > 0`; `status` thuộc `AVAILABLE` hoặc `OCCUPIED`; bàn `AVAILABLE` phải có `current_order_id = null`; bàn `OCCUPIED` phải trỏ đến đơn `OPEN` tương ứng.

### 5.3. `orders.json`

```json
[
  {
    "id": "ORD-20261010-A1B2",
    "table_id": "TBL-02",
    "status": "OPEN",
    "created_at": "2026-10-10T18:30:00+07:00",
    "paid_at": null,
    "payment_method": null,
    "discount_vnd": 0,
    "subtotal_vnd": 128000,
    "total_vnd": 128000,
    "cancel_reason": null,
    "items": [
      {
        "id": "OI-C100",
        "menu_item_id": "MI-001",
        "item_name": "Phở bò",
        "unit_price_vnd": 55000,
        "quantity": 2,
        "note": "Một tô không hành",
        "status": "QUEUED",
        "queued_at": "2026-10-10T18:30:03+07:00",
        "queue_seq": 1
      },
      {
        "id": "OI-C101",
        "menu_item_id": "MI-002",
        "item_name": "Trà tắc",
        "unit_price_vnd": 18000,
        "quantity": 1,
        "note": "Ít đá",
        "status": "QUEUED",
        "queued_at": "2026-10-10T18:30:04+07:00",
        "queue_seq": 2
      }
    ]
  }
]
```

**Bất biến:** `quantity` là số nguyên dương; `unit_price_vnd >= 0`; `queue_seq` là số nguyên tăng dần được cấp qua `app_state.json`; `status` của đơn là `OPEN`, `PAID` hoặc `CANCELLED`. `subtotal_vnd`/`total_vnd` phải được tính từ dữ liệu đơn và không tin giá trị UI gửi lên.

### 5.4. `app_state.json`

```json
{
  "next_queue_seq": 3
}
```

`StateRepository.next_queue_seq()` trả về số hiện tại rồi tăng và lưu lại. Nhờ vậy, sau khi khởi động lại vẫn có thể dựng FIFO ổn định mà không phụ thuộc việc hai món có timestamp trùng nhau hay không.

### 5.5. Models và enum đề xuất

Dùng `dataclasses` để đóng gói dữ liệu; nên có `from_dict()` và `to_dict()` ở Model hoặc một mapper rõ ràng. Trạng thái dùng `Enum` thay vì rải chuỗi tùy ý trong code.

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class TableStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"


class OrderStatus(StrEnum):
    OPEN = "OPEN"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class OrderItemStatus(StrEnum):
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    READY = "READY"
    SERVED = "SERVED"
    CANCELLED = "CANCELLED"
```

Có thể dùng `StrEnum` khi nhóm thống nhất Python 3.11 trở lên. Nếu môi trường của trường yêu cầu Python thấp hơn, dùng `class ... (str, Enum)`.

### 5.6. Queue và Hash Map được áp dụng ở đâu?

**Queue — `collections.deque`:**

```python
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class QueueEntry:
    queue_seq: int
    order_id: str
    order_item_id: str


class KitchenQueue:
    def __init__(self) -> None:
        self._items: deque[QueueEntry] = deque()

    def enqueue(self, entry: QueueEntry) -> None:
        self._items.append(entry)

    def peek(self) -> QueueEntry | None:
        return self._items[0] if self._items else None

    def pop(self) -> QueueEntry | None:
        return self._items.popleft() if self._items else None

    def remove_order(self, order_id: str) -> None:
        self._items = deque(x for x in self._items if x.order_id != order_id)

    def __len__(self) -> int:
        return len(self._items)
```

`append()` và `popleft()` của `deque` phù hợp cho thao tác FIFO ở hai đầu. Queue chỉ giữ tham chiếu ID, không giữ bản sao `OrderItem` có thể bị cũ. Dữ liệu gốc vẫn là `orders.json`; Queue được dựng lại khi khởi động từ các món `QUEUED`, sắp xếp theo `queue_seq`.

**Hash Map — `dict`:**

```python
self._by_id: dict[str, MenuItem] = {
    item.id: item for item in self._load_all_from_json()
}


def get_by_id(self, menu_item_id: str) -> MenuItem | None:
    return self._by_id.get(menu_item_id)
```

Áp dụng tương tự với `TableRepository` và có thể cả `OrderRepository`. Tra cứu theo mã có độ phức tạp trung bình **O(1)**; liệt kê toàn bộ vẫn là **O(n)**. Khi create/update/delete, repository phải đồng bộ cả JSON và `_by_id`; sau khi ghi file thành công mới cập nhật index trong bộ nhớ.

### 5.7. Ghi JSON ổn định

`JsonFileStore` cần:
- Đọc UTF-8; kiểm tra file và dữ liệu đầu vào.
- Tạo thư mục cha nếu chưa tồn tại.
- Ghi dữ liệu ra file tạm cùng thư mục, `flush`/đóng file, sau đó `replace` file đích để tránh file bị ghi dở khi tiến trình gặp lỗi.
- Báo lỗi qua `PersistenceError`, không âm thầm bỏ qua lỗi parse.
- Không ghi lại toàn bộ JSON khi chỉ cần hiển thị dữ liệu.

Ghi nguyên tử từng file không đồng nghĩa giao dịch nguyên tử cho nhiều file. Vì vậy cần thứ tự ghi, xử lý bù và kiểm tra nhất quán lúc khởi động như mô tả ở phần nghiệp vụ.

---

## 6. Hợp đồng hàm giữa các module

Chữ ký dưới đây là **API nội bộ** mà 5 thành viên cần chốt trước khi code. Có thể bổ sung kiểu trả về DTO, nhưng không đổi tên/ý nghĩa tùy ý mà không cập nhật PR hoặc trao đổi nhóm.

### 6.1. Models / storage — Thành viên 1

```python
# storage/json_store.py
class JsonFileStore:
    def read_json(self, path: Path, default: object) -> object: ...
    def write_json_atomic(self, path: Path, data: object) -> None: ...

# domain/models.py (các lớp dataclass)
class MenuItem: ...
class Table: ...
class OrderItem: ...
class Order: ...
class Receipt: ...
```

Model tối thiểu cần có các trường đúng với JSON mẫu và phương thức chuyển đổi dữ liệu. Không để Model import repository/service.

### 6.2. Repository — Thành viên 2

```python
class MenuRepository:
    def list_all(self) -> list[MenuItem]: ...
    def list_available(self) -> list[MenuItem]: ...
    def get_by_id(self, menu_item_id: str) -> MenuItem | None: ...
    def upsert(self, item: MenuItem) -> MenuItem: ...
    def delete(self, menu_item_id: str) -> bool: ...

class TableRepository:
    def list_all(self) -> list[Table]: ...
    def get_by_id(self, table_id: str) -> Table | None: ...
    def upsert(self, table: Table) -> Table: ...
    def delete(self, table_id: str) -> bool: ...

class OrderRepository:
    def list_all(self) -> list[Order]: ...
    def list_open(self) -> list[Order]: ...
    def get_by_id(self, order_id: str) -> Order | None: ...
    def upsert(self, order: Order) -> Order: ...
    def delete(self, order_id: str) -> bool: ...

class StateRepository:
    def next_queue_seq(self) -> int: ...
```

`delete()` của repository là CRUD mức dữ liệu. Service nghiệp vụ không dùng hard delete để xóa đơn đã thanh toán; nên chuyển trạng thái theo quy tắc đã chốt.

### 6.3. Controller & Service — Thành viên 3

```python
class MenuService:
    def list_available_menu(self) -> list[MenuItem]: ...
    def get_menu_item(self, menu_item_id: str) -> MenuItem: ...

class OrderService:
    def create_order(
        self, table_id: str, lines: list[dict[str, object]]
    ) -> Order: ...
    def add_items(
        self, order_id: str, lines: list[dict[str, object]]
    ) -> Order: ...
    def get_order(self, order_id: str) -> Order: ...
    def list_open_orders(self) -> list[Order]: ...
    def cancel_order(self, order_id: str, reason: str = "") -> Order: ...

class KitchenService:
    def get_queue(self) -> list[QueueEntry]: ...
    def start_next_item(self) -> tuple[Order, OrderItem] | None: ...
    def mark_item_ready(self, order_id: str, item_id: str) -> Order: ...
    def mark_item_served(self, order_id: str, item_id: str) -> Order: ...
```

Cấu trúc `lines` đầu vào ví dụ: `[{'menu_item_id': 'MI-001', 'quantity': 2, 'note': 'Ít hành'}]`. Service phải validate và tạo `OrderItem`, không chấp nhận `unit_price_vnd` do UI gửi.

### 6.4. Controller & Service — Thành viên 4

```python
class TableService:
    def list_tables(self) -> list[Table]: ...
    def get_table(self, table_id: str) -> Table: ...
    def occupy_table(self, table_id: str, order_id: str) -> Table: ...
    def release_table(self, table_id: str, order_id: str) -> Table: ...

class PaymentService:
    def preview_bill(
        self, order_id: str, discount_vnd: int = 0
    ) -> BillSummary: ...
    def checkout(
        self, order_id: str, payment_method: str, discount_vnd: int = 0
    ) -> Receipt: ...

class ReportService:
    def daily_summary(self, report_date: date) -> dict[str, object]: ...
```

`payment_method` trong phiên bản đầu có thể giới hạn `CASH`, `BANK_TRANSFER`, `CARD`. `checkout()` phải kiểm tra trạng thái đơn hiện tại, tính lại số tiền ở service, không dùng số tổng UI đưa lên. `release_table()` chỉ giải phóng nếu `table.current_order_id == order_id` để tránh giải phóng nhầm bàn.

### 6.5. Frontend / UI — Thành viên 5

```python
# ui/handlers.py — ví dụ adapter
class UIHandlers:
    def create_order(self, table_id: str, selected_lines: list[dict]): ...
    def refresh_tables(self) -> list[list[object]]: ...
    def refresh_menu(self) -> list[list[object]]: ...
    def refresh_kitchen_queue(self) -> list[list[object]]: ...
    def checkout(self, order_id: str, method: str, discount_vnd: int): ...
    def refresh_daily_report(self, report_date: str): ...

# ui/pages.py
# build_demo(context) -> gr.Blocks
```

Các hàm handler chuyển input từ component thành kiểu service yêu cầu, gọi service, đổi kết quả thành text/DataFrame/update của Gradio. Handler không tự truy cập repository/JSON và không thực hiện phép tính nghiệp vụ độc lập.

---

## 7. Task Matrix chi tiết theo thành viên

## Thành viên 1 — Thanh Bình: Project Bootstrap, Database, Schema, Models

### Phạm vi

Chịu trách nhiệm nền móng dùng chung: cấu trúc dự án, môi trường `uv`, quy ước dữ liệu, Model, file seed và bộ đọc/ghi JSON mức thấp. Không triển khai nghiệp vụ đơn hàng hoặc UI.

### Tasks

| ID | Task | Input | Output / tiêu chí hoàn thành |
|---|---|---|---|
| M1-01 | Tạo skeleton thư mục `src/` và `tests/` | Quyết định kiến trúc ở mục 3–4 | Package `restaurant_pos`, các `__init__.py`, thư mục module sẵn sàng |
| M1-02 | Khởi tạo project với `uv` | Tên project và phiên bản Python nhóm thống nhất | `pyproject.toml`, `.python-version`, `uv.lock`; README hướng dẫn setup |
| M1-03 | Chuẩn hóa Model và enum | JSON mẫu ở mục 5 | `domain/models.py`, `domain/enums.py`, `domain/exceptions.py`; có type hints và `to_dict/from_dict` |
| M1-04 | Tạo `JsonFileStore` | Đường dẫn file runtime thống nhất | `read_json`, `write_json_atomic`, tạo folder, lỗi được chuẩn hóa |
| M1-05 | Tạo seed menu và bàn | Danh mục món/bàn mẫu nhóm thống nhất | `data/seed/menu.json`, `data/seed/tables.json`; ID không trùng, JSON hợp lệ |
| M1-06 | Viết bootstrap dữ liệu ban đầu | Models, JsonFileStore, seed files | Tạo runtime files nếu chưa tồn tại; không ghi đè dữ liệu cũ |
| M1-07 | Viết test Model/JsonFileStore | Đặc tả schema | Test parse/serialize, file chưa có, JSON hỏng, ghi và đọc lại |
| M1-08 | Chốt quy ước API chung | Phản hồi từ M2–M5 | Tài liệu này được đưa vào `docs/architecture.md`, mọi thành viên xác nhận chữ ký hàm |

### Input / Output bàn giao

- **Input:** yêu cầu nghiệp vụ, schema ở mục 5 và thống nhất Python tối thiểu.
- **Output:** package khởi tạo chạy được; Model và enums ổn định; `JsonFileStore`; dữ liệu seed; lệnh setup trong README.
- **Bàn giao cho:** M2 dùng `JsonFileStore`/Models; M3/M4 dùng Model/enums/exceptions; M5 dùng bootstrap và package path.
- **Không làm:** CRUD theo thực thể, Queue, tính tổng hóa đơn hoặc tạo Gradio page.

### Definition of Done

`uv sync` chạy được; `uv run pytest tests/test_models.py tests/test_json_store.py` qua; seed/runtime được tạo đúng; không commit `.venv/`, cache hoặc dữ liệu demo runtime.

---

## Thành viên 2 — Repository / CRUD

### Phạm vi

Đọc/ghi dữ liệu JSON theo từng thực thể; quản lý Hash Map để tra cứu menu/bàn theo mã trung bình O(1); không đưa quy tắc nghiệp vụ vào repository.

### Tasks

| ID | Task | Input | Output / tiêu chí hoàn thành |
|---|---|---|---|
| M2-01 | Cài đặt `MenuRepository` | `MenuItem`, `JsonFileStore`, `menu.json` | CRUD, `list_available()`, `_by_id: dict[str, MenuItem]` |
| M2-02 | Cài đặt `TableRepository` | `Table`, `JsonFileStore`, `tables.json` | CRUD, `_by_id: dict[str, Table]`, cập nhật cache sau mỗi mutation |
| M2-03 | Cài đặt `OrderRepository` | `Order`, `JsonFileStore`, `orders.json` | CRUD, tìm đơn, liệt kê đơn `OPEN`, duy trì index theo ID |
| M2-04 | Cài đặt `StateRepository` | Quy ước `app_state.json` | `next_queue_seq()` tăng và lưu số tiếp theo một cách nhất quán |
| M2-05 | Xử lý lỗi lưu trữ | `PersistenceError` và API `JsonFileStore` | Không nuốt lỗi; không trả dữ liệu giả khi JSON hỏng |
| M2-06 | Viết repository tests | Test fixtures với `tmp_path` | Test create/get/update/delete, ID trùng, không tìm thấy, cache sau update |
| M2-07 | Bàn giao contract và demo | Chữ ký tại mục 6.2 | Ví dụ khởi tạo repo; README ngắn hoặc test chứng minh CRUD chạy |

### Input / Output bàn giao

- **Input:** các dataclass/enums, `JsonFileStore`, vị trí runtime files.
- **Output:** `menu_repository.py`, `table_repository.py`, `order_repository.py`, `state_repository.py` và unit tests.
- **Bàn giao cho:** M3 dùng Menu/Order/State repositories; M4 dùng Order/Table repositories; M5 không gọi repository trực tiếp.
- **Không làm:** tự enqueue, xác nhận thanh toán hay quyết định khi nào bàn được giải phóng.

### Definition of Done

Tra cứu ID đi qua `dict`, không đọc lại toàn bộ file cho mỗi lookup; CRUD ghi xuống file và cache đồng bộ; tests chạy độc lập, không sửa `data/runtime` thật.

---

## Thành viên 3 — Order & Kitchen Services

### Phạm vi

Điều phối tạo đơn, thêm món, hủy đơn đúng điều kiện và luồng bếp FIFO. Dùng Menu/Order/State repositories; dùng `TableService` qua dependency injection để giữ đúng quyền sở hữu nghiệp vụ bàn của M4.

### Tasks

| ID | Task | Input | Output / tiêu chí hoàn thành |
|---|---|---|---|
| M3-01 | Cài đặt `MenuService` | `MenuRepository` | API liệt kê món đang bán và lấy món theo mã; lỗi `NotFoundError` nhất quán |
| M3-02 | Cài đặt `KitchenQueue` | `QueueEntry` và quy tắc FIFO | `enqueue`, `peek`, `pop`, `remove_order`, `len`, test FIFO |
| M3-03 | Khôi phục Queue khi startup | `OrderRepository.list_all()` | Enqueue các dòng `QUEUED`, sort theo `queue_seq`; không thêm món `PREPARING`/`READY` |
| M3-04 | Cài đặt `OrderService.create_order` | table/menu/order/state repo + TableService | Validate, snapshot giá/tên, lưu đơn, occupy bàn, enqueue món theo thứ tự |
| M3-05 | Cài đặt `add_items` | Đơn `OPEN`, danh sách dòng món | Thêm món, cấp sequence mới, đồng bộ JSON và Queue |
| M3-06 | Cài đặt `KitchenService.start_next_item` | Queue + OrderRepository | Chuyển ticket đầu từ `QUEUED` sang `PREPARING` và pop Queue sau khi lưu thành công |
| M3-07 | Cài đặt `mark_item_ready/served` | ID đơn và ID dòng món | Kiểm tra trạng thái nguồn hợp lệ, cập nhật JSON |
| M3-08 | Cài đặt `cancel_order` | Đơn `OPEN`, Queue, TableService | Chỉ hủy khi mọi món còn `QUEUED`; xóa ticket của đơn, ghi `CANCELLED`, giải phóng bàn |
| M3-09 | Viết service tests | Repositories thật trên thư mục tạm hoặc fake repo | Test input sai, bàn bận, menu không tồn tại, FIFO, cancel conflict, restart Queue |

### Input / Output bàn giao

- **Input:** Models/enums/exceptions từ M1; repository contracts từ M2; API `TableService` do M4 công bố.
- **Output:** `menu_service.py`, `order_service.py`, `kitchen_queue.py`, `kitchen_service.py`, test và danh sách lỗi nghiệp vụ.
- **Bàn giao cho:** M5 dùng Menu/Order/Kitchen services; M4 nhận API `get_order/list_open_orders/cancel_order` nếu cần tích hợp thanh toán/báo cáo.
- **Không làm:** tính hóa đơn cuối cùng, giải phóng bàn trực tiếp qua repo trong UI, dựng Gradio.

### Definition of Done

Mọi món tạo mới được lưu và đưa vào Queue đúng FIFO; trạng thái bếp tồn tại sau restart; tạo đơn lỗi không để bàn/đơn ở trạng thái dở dang trong luồng lỗi có thể xử lý; không có logic nghiệp vụ trong UI.

---

## Thành viên 4 — Table, Payment & Report Services

### Phạm vi

Quản lý vòng đời trạng thái bàn, xem trước hóa đơn, checkout và báo cáo từ đơn đã lưu. Không thực hiện CRUD file trực tiếp; dùng repositories.

### Tasks

| ID | Task | Input | Output / tiêu chí hoàn thành |
|---|---|---|---|
| M4-01 | Cài đặt `TableService` | `TableRepository`, có thể dùng `OrderRepository` để kiểm tra tham chiếu | `list_tables`, `get_table`, `occupy_table`, `release_table`; đảm bảo current order khớp |
| M4-02 | Chốt trạng thái bàn và invariant | Schema `Table` và `Order` | Kiểm tra `AVAILABLE` ↔ `current_order_id=None`, `OCCUPIED` ↔ đơn mở đúng bàn |
| M4-03 | Cài đặt `BillSummary`/`Receipt` | Model contract | DTO hóa đơn có subtotal, discount, total, phương thức và thời điểm thanh toán |
| M4-04 | Cài đặt `preview_bill` | `OrderRepository`, đơn `OPEN` | Tính tổng từ item snapshots; validate giảm giá; không ghi trạng thái thanh toán |
| M4-05 | Cài đặt `checkout` | OrderRepository + TableService | Kiểm tra trạng thái; lưu `PAID`/`paid_at`/method; giải phóng đúng bàn |
| M4-06 | Cài đặt `ReportService` | Danh sách đơn từ repository | Doanh thu theo ngày, số đơn PAID, giá trị trung bình, top món tùy phạm vi |
| M4-07 | Xử lý lỗi và tính nhất quán | Conflict/Persistence errors | Không thanh toán hai lần; không giải phóng nhầm bàn; có chiến lược xử lý nếu bước lưu thứ hai lỗi |
| M4-08 | Viết service tests | Orders/tables fixture | Test tổng tiền, discount âm/quá lớn, đơn chưa sẵn sàng, checkout lặp, report lọc ngày |

### Input / Output bàn giao

- **Input:** Models/enums/exceptions từ M1; Table/Order repositories từ M2; contract Order từ M3.
- **Output:** `table_service.py`, `payment_service.py`, `report_service.py`, DTO hóa đơn và tests.
- **Bàn giao cho:** M3 gọi `occupy_table/release_table`; M5 dùng bảng bàn, preview/checkout, report services.
- **Không làm:** dùng số tiền UI truyền lên làm số tiền có thẩm quyền; xóa vật lý lịch sử đơn PAID.

### Definition of Done

Hóa đơn tính đúng từ snapshot giá; thanh toán bị từ chối nếu đơn sai trạng thái; bàn trở về `AVAILABLE` sau checkout thành công; báo cáo chỉ tính đơn `PAID` và theo đúng ngày.

---

## Thành viên 5 — Frontend Gradio & Integration

### Phạm vi

Dựng giao diện và kết nối đến Service. Đảm bảo UI hiển thị trạng thái mới nhất, thông báo lỗi dễ hiểu, không nhúng business logic vào callback.

### Tasks

| ID | Task | Input | Output / tiêu chí hoàn thành |
|---|---|---|---|
| M5-01 | Vẽ wireframe và chốt màn hình | Use cases, service contracts | Các tab: Menu/Order, Kitchen Queue, Tables, Checkout, Reports |
| M5-02 | Cài đặt `UIHandlers` | API từ M3/M4 | Handler chuyển kiểu input/output và bắt lỗi nghiệp vụ; không gọi repository |
| M5-03 | Dựng Gradio Blocks | Wireframe và handler contracts | Components rõ label, validation, bảng menu/bàn/queue, chi tiết đơn |
| M5-04 | Liên kết event listener | Service handler đã có | Button/Dropdown/Select/Refresh gọi đúng handler; đầu ra phản hồi sau hành động |
| M5-05 | Refresh UI đúng thời điểm | Lệnh create/add/start/ready/checkout/cancel | Sau mutation, refresh các bảng bị ảnh hưởng; không refresh vô hạn hoặc giữ state cũ |
| M5-06 | Tạo bootstrap/container | Constructors của repo/services | Dựng các dependency một lần và truyền vào UI; không tạo nhiều Queue độc lập |
| M5-07 | Smoke test giao diện | Project đã tích hợp | App launch, xem menu/bàn, tạo đơn, thao tác bếp, checkout và báo cáo bằng luồng thật |
| M5-08 | Hoàn thiện UX/demo | Dữ liệu seed và kịch bản báo cáo | Thông báo thành công/thất bại, trạng thái rỗng, xác nhận hành động nhạy cảm, demo script |

### Input / Output bàn giao

- **Input:** Service APIs ổn định từ M3/M4; Models; seed data.
- **Output:** `ui/pages.py`, `ui/handlers.py`, `app.py` mỏng, `bootstrap.py`/container wiring, hướng dẫn chạy và kịch bản demo.
- **Bàn giao cho:** cả nhóm kiểm thử tích hợp và dùng khi thuyết trình.
- **Không làm:** không tự tính tổng tiền, không `json.load/json.dump`, không trực tiếp `deque.append/popleft` trong file giao diện.

### Definition of Done

`uv run python -m restaurant_pos.app` chạy từ root; luồng chính thao tác được; lỗi validation được hiển thị thân thiện; callback không chứa vòng lặp nghiệp vụ hoặc cập nhật file trực tiếp.

---

## 8. Quy trình phối hợp và quản lý phụ thuộc

### 8.1. Thứ tự triển khai bắt buộc

| Giai đoạn | Chủ trì | Kết quả bàn giao | Điều kiện bắt đầu giai đoạn tiếp |
|---|---|---|---|
| Phase 0 — Thống nhất hợp đồng | Cả nhóm, M1 điều phối | Tên Model, enum, file JSON, chữ ký Service/Repo | Mọi thành viên đồng ý mục 5–6 |
| Phase 1 — Foundation | M1 | Project `uv`, Models, JSON store, seed, exceptions | Tests nền tảng qua |
| Phase 2 — Repository | M2 | CRUD, index `dict`, state repo, tests | Service có thể chạy bằng repo thật/test tmp path |
| Phase 3A — Table service | M4 song song khi repo ổn định | API occupy/release bàn | Chữ ký TableService công bố trước khi M3 tích hợp |
| Phase 3B — Order/Kitchen | M3 | OrderService, Queue, KitchenService, tests | Dùng được contract từ M2 và TableService từ M4 |
| Phase 3C — Payment/Report | M4 | PaymentService, ReportService, tests | Nhận model Order thống nhất và repository API |
| Phase 4 — UI integration | M5 | Gradio pages/handlers, bootstrap, luồng end-to-end | Service contracts không đổi âm thầm |
| Phase 5 — Hardening | Cả nhóm | Regression tests, demo script, README, báo cáo | Checklist nghiệm thu hoàn tất |

Có thể làm song song khi API đã chốt. Không nên chờ tới cuối mới ghép code; cuối mỗi phase cần một buổi integration ngắn trên `develop`.

### 8.2. Quy định giao tiếp giữa thành viên

- Mỗi PR phải ghi rõ module/hàm được thêm hoặc đổi và tác động đến thành viên khác.
- Nếu phải thay đổi tên trường JSON, enum hoặc chữ ký hàm, cập nhật tài liệu và báo nhóm **trước khi merge**.
- Người phụ thuộc API có thể viết test với fake/mock hoặc fixture theo contract; không tạo lại một phiên bản model/repository riêng.
- Mỗi module chỉ có một người chịu trách nhiệm chính; sửa chéo chỉ qua PR có người sở hữu module review.
- Không merge PR nếu test của nhánh đó thất bại hoặc code làm `develop` không chạy được.

---

## 9. Git Flow Standard

### 9.1. Nhánh chuẩn

```text
main        : phiên bản ổn định dùng để nộp/demo release
  └── develop: nhánh tích hợp đang phát triển
        ├── feature/models-json-store
        ├── feature/menu-table-repositories
        ├── feature/order-kitchen-queue
        ├── feature/payment-table-report
        └── feature/gradio-ui
```

Mỗi thành viên tạo feature branch từ `develop`, làm việc và push lên remote, mở PR về `develop`. Khi hoàn tất và kiểm thử tích hợp, trưởng nhóm tạo PR `develop` → `main` để đóng mốc release. Không commit trực tiếp vào `main`/`develop` trừ trường hợp khẩn cấp đã được cả nhóm thống nhất.

### 9.2. Quy ước đặt tên branch

Mẫu: `<type>/<short-description>`.

| Type | Dùng cho | Ví dụ |
|---|---|---|
| `feature/` | Tính năng mới | `feature/order-kitchen-queue` |
| `fix/` | Sửa lỗi | `fix/queue-rebuild-order` |
| `test/` | Bổ sung/sửa tests | `test/payment-service` |
| `docs/` | Tài liệu | `docs/system-architecture` |
| `refactor/` | Cải thiện cấu trúc không đổi hành vi | `refactor/json-repository` |

Branch ngắn, chữ thường, dùng dấu gạch ngang; không đưa tên cá nhân hoặc tên môn học vào mọi branch.

### 9.3. Quy ước commit

Dùng Conventional Commit đơn giản:

```text
feat(order): create order and enqueue items
feat(kitchen): restore FIFO queue from JSON
fix(payment): reject duplicate checkout
test(repository): cover hash-map index updates
docs(architecture): define service contracts
refactor(ui): move callbacks into handlers
chore(uv): update locked dependencies
```

- Một commit nên thể hiện một thay đổi logic rõ ràng.
- Không dùng message chung chung như `update`, `final`, `fix bug`, `abc`.
- Không commit file tạm, dữ liệu runtime, `.venv`, cache, log hoặc bí mật/token.
- `uv.lock` phải được commit khi dependencies thay đổi để cả nhóm có môi trường nhất quán.

### 9.4. Quy trình làm việc hằng ngày

```bash
# Lần đầu
uv sync

# Bắt đầu task mới
 git switch develop
 git pull origin develop
 git switch -c feature/order-kitchen-queue

# Chạy kiểm tra trước khi commit
uv run pytest
uv run ruff check .
uv run ruff format --check .
git status

# Commit và push
git add src/ tests/ docs/
git commit -m "feat(kitchen): implement FIFO queue"
git push -u origin feature/order-kitchen-queue
```

Lưu ý: loại bỏ khoảng trắng trước `git switch` nếu copy lệnh từ nơi định dạng lại. Chỉ `git add` các file có chủ đích; không dùng `git add .` khi chưa kiểm tra `git status`.

Khi `develop` có thay đổi mới, cập nhật feature branch theo chính sách nhóm (merge `develop` vào feature branch hoặc rebase theo hướng dẫn trưởng nhóm). Không rebase/force-push nhánh đang có người khác cùng dùng nếu chưa thống nhất.

### 9.5. Pull Request checklist

Mỗi PR phải có:

- [ ] Mô tả vấn đề, phạm vi thay đổi, ảnh hưởng module khác.
- [ ] Liên kết task ID trong task matrix.
- [ ] Test mới hoặc giải thích vì sao không cần test.
- [ ] `uv run pytest` thành công.
- [ ] `uv run ruff check .` và `uv run ruff format --check .` thành công (nếu nhóm bật Ruff).
- [ ] Không có file `.venv`, cache, dữ liệu `data/runtime`, log, secret/token.
- [ ] Không đổi API/schema âm thầm; nếu có, tài liệu/hợp đồng đã cập nhật.
- [ ] Có người review khác tác giả; không tự approve PR của mình.
- [ ] `develop` vẫn launch được sau merge.

### 9.6. `.gitignore` tối thiểu

```gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
.DS_Store
Thumbs.db
.env

# Dữ liệu được sinh khi chạy; giữ file .gitkeep
/data/runtime/*
!/data/runtime/.gitkeep
```

Không ignore `uv.lock`, `pyproject.toml`, tests, seed data hoặc tài liệu. Không để credentials trong repository.

---

## 10. Quy trình quản lý môi trường bằng `uv`

### 10.1. Khởi tạo và cài dependencies

Trưởng nhóm khởi tạo project và commit `pyproject.toml`, `.python-version`, `uv.lock`. Ví dụ quy trình:

```bash
uv init --package
uv add gradio
uv add --dev pytest ruff
uv sync
```

Nếu skeleton đã được tạo thì không chạy `uv init` lần nữa; chỉ dùng các lệnh cần thiết để bổ sung dependency. Sau đó nhóm chạy:

```bash
uv run python -m restaurant_pos.app
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

### 10.2. Quy tắc dependency

- Thêm/gỡ package bằng `uv add` / `uv remove`, không cài thủ công rồi quên khai báo.
- Commit thay đổi đồng thời ở `pyproject.toml` và `uv.lock`.
- Khi review PR có đổi dependency, kiểm tra package đó thật sự cần thiết.
- Thành viên mới clone project chạy `uv sync`, không tự tạo requirements khác nếu chưa có quyết định của nhóm.
- Không commit thư mục `.venv/`.

---

## 11. Kiểm thử và nghiệm thu theo rubric 100 điểm

### 11.1. Ma trận kiểm thử tối thiểu

| Nhóm | Kịch bản cần test | Kết quả đúng |
|---|---|---|
| Models/Schema | Đọc JSON đúng; thiếu trường; enum sai; ID trùng | Parse hợp lệ hoặc báo lỗi có ý nghĩa |
| JSON storage | File chưa tồn tại; JSON hỏng; ghi và đọc lại; lỗi quyền ghi | Khởi tạo đúng hoặc ném `PersistenceError`; không nuốt lỗi |
| Hash Map | Lookup ID tồn tại/không tồn tại; upsert/delete | Kết quả đúng và index được cập nhật ngay |
| Queue | FIFO; Queue rỗng; bỏ ticket theo order; rebuild sau restart | Ticket được xử lý theo `queue_seq`, không phục hồi món đã PREPARING |
| Tạo đơn | Bàn trống; bàn bận; món không tồn tại; quantity 0/âm; món ngừng bán | Chỉ tạo khi input hợp lệ; lỗi không làm lệch bàn/đơn |
| Bếp | QUEUED→PREPARING→READY→SERVED; chuyển sai trạng thái | Chuyển hợp lệ; từ chối chuyển sai |
| Thanh toán | Tổng tiền; discount hợp lệ/không hợp lệ; checkout lặp; món chưa sẵn sàng | Tổng tiền đúng; không thanh toán hai lần |
| Bàn | Occupy/release đúng order; giải phóng sai order ID | Trạng thái và `current_order_id` nhất quán |
| Báo cáo | Nhiều ngày; đơn OPEN/CANCELLED/PAID | Chỉ tính đơn PAID trong ngày được chọn |
| UI | Luồng đầy đủ từ tạo đơn đến báo cáo | Không crash; thông báo rõ; bảng được refresh |
| Git/uv | Clone sạch, `uv sync`, test, launch | Người khác trong nhóm tái tạo được môi trường |

### 11.2. Mapping theo rubric

| Rubric | Minh chứng nên chuẩn bị | Người phụ trách chính |
|---|---|---|
| Git & `uv` — 20% | Lịch sử commit có nội dung; feature branch/PR; `pyproject.toml` + `uv.lock`; README setup | M1 + cả nhóm |
| OOP & Clean Code — 20% | Models/dataclasses, service/repository riêng, type hints, `app.py` mỏng, exception rõ | M1–M5 theo module |
| Queue, Hash Map, JSON — 20% | Demo FIFO; restart vẫn khôi phục Queue; code `deque`; `dict` lookup; JSON ghi/đọc đúng | M2 + M3 |
| Gradio & UX — 20% | Các tab/luồng thao tác hoàn chỉnh; validation; thông báo lỗi/thành công; refresh đúng | M5 |
| Trình bày — 20% | Sơ đồ kiến trúc, use case, giải thích độ phức tạp, test evidence, kịch bản demo và Q&A | M1 điều phối, cả nhóm trình bày |

### 11.3. Tiêu chí nghiệm thu toàn hệ thống

- [ ] Thành viên mới clone repo và làm theo README để chạy được bằng `uv`.
- [ ] Mọi tính năng gọi qua UI hoạt động bằng dữ liệu runtime JSON.
- [ ] Tạo đơn cập nhật đồng nhất `orders.json`, `tables.json` và Queue trong bộ nhớ.
- [ ] Queue FIFO và được khôi phục từ JSON theo `queue_seq` sau khi restart.
- [ ] Tra cứu menu/bàn qua Hash Map `dict`, không dò danh sách tuyến tính cho mọi lookup theo ID.
- [ ] Thanh toán không cho phép double checkout; báo cáo không mất đơn cũ.
- [ ] `app.py` chỉ là entry point; không chứa business logic.
- [ ] Tests chính chạy pass; dữ liệu runtime và file rác không nằm trong PR.
- [ ] Có README, sơ đồ kiến trúc, task/commit history và kịch bản demo.

---

## 12. Kịch bản demo gợi ý (5–7 phút)

1. **Khởi động:** chạy `uv sync`, sau đó `uv run python -m restaurant_pos.app`; chỉ nhanh cấu trúc N-tier.
2. **Menu/Hash Map:** tra cứu một mã menu và giải thích repository dùng `dict` để tra cứu trung bình O(1).
3. **Tạo đơn:** chọn bàn trống, thêm 2 dòng món; cho thấy bàn đổi thành `OCCUPIED`, đơn được lưu JSON và ticket xuất hiện trong Queue.
4. **Queue:** tạo thêm món/đơn thứ hai, cho thấy FIFO; bấm “Bắt đầu món tiếp theo”, đổi `QUEUED` sang `PREPARING`, sau đó `READY` và `SERVED`.
5. **Persistence:** dừng và mở lại app; chứng minh dữ liệu đơn/bàn được nạp từ JSON và Queue còn các ticket chưa chế biến theo đúng thứ tự.
6. **Thanh toán:** xem preview, xác nhận phương thức thanh toán; hóa đơn chuyển `PAID`, bàn được giải phóng.
7. **Báo cáo:** lọc theo ngày có thanh toán và đối chiếu doanh thu với hóa đơn đã demo.
8. **Kết thúc:** mở `git log --oneline --graph`, cho thấy feature branch/commit/PR và chạy tests.

### Câu hỏi vấn đáp nhóm nên chuẩn bị

- Vì sao dùng `deque` cho Queue, FIFO có ý nghĩa gì trong nghiệp vụ bếp?
- Hash Map nằm ở module nào? Vì sao lookup trung bình O(1), khi nào phải cập nhật index?
- Vì sao lưu snapshot giá món trong OrderItem thay vì luôn lấy giá mới từ menu?
- Vì sao `app.py` không chứa nghiệp vụ? Khác nhau giữa UI, Service và Repository là gì?
- Khi JSON ghi dở hoặc app khởi động lại thì dữ liệu được xử lý thế nào?
- Vì sao không hard-delete đơn PAID? Báo cáo doanh thu lọc theo điều kiện nào?
- Nhóm kiểm thử FIFO, thanh toán lặp và trạng thái bàn bằng cách nào?
- `uv.lock` có vai trò gì và vì sao cần commit file này?

---

## 13. Checklist khởi động nhóm — làm trước khi viết nghiệp vụ

- [ ] Chọn phiên bản Python chung (khuyến nghị từ 3.11 trở lên để dùng `StrEnum`; có thể chọn bản khác nếu phòng máy yêu cầu).
- [ ] Chốt các trường JSON ở mục 5, không tự đổi tên ở từng module.
- [ ] Chốt exception types, enums và chữ ký hàm ở mục 6.
- [ ] Tạo repo Git từ xa, bảo vệ `main` và `develop` nếu nền tảng cho phép.
- [ ] M1 merge nền tảng tối thiểu trước; M2 viết tests repo dựa trên Model thật.
- [ ] M4 công bố `TableService` interface sớm để M3 không phụ thuộc implementation chưa tồn tại.
- [ ] M3/M4 tạo service độc lập với Gradio; có thể test trong terminal trước.
- [ ] M5 dùng fake/context tối thiểu trong lúc đợi Service, rồi thay bằng container thật khi tích hợp.
- [ ] Mỗi PR gắn task ID và người review; cuối mỗi giai đoạn hợp nhất lên `develop` và chạy regression tests.

---

## Tài liệu tham khảo chính thức

- uv — Working on projects: https://docs.astral.sh/uv/guides/projects/
- uv — Configuring projects: https://docs.astral.sh/uv/concepts/projects/config/
- uv — Locking and syncing: https://docs.astral.sh/uv/concepts/projects/sync/
- Gradio — State / event listeners: https://gradio.app/docs/gradio/state
- Git — Documentation: https://git-scm.com/docs

