"""Các lỗi nghiệp vụ dùng chung trong ứng dụng."""


class FNBError(Exception):
    """Lỗi cơ sở để UI có thể bắt và hiển thị thông báo thân thiện."""


class ValidationError(FNBError):
    """Dữ liệu đầu vào không hợp lệ."""


class NotFoundError(FNBError):
    """Không tìm thấy menu item, table hoặc order theo ID."""


class ConflictError(FNBError):
    """Hành động xung đột với dữ liệu hiện tại, ví dụ bàn đã có đơn."""


class InvalidStateError(FNBError):
    """Không thể thực hiện hành động vì trạng thái hiện tại không phù hợp."""


class StorageError(FNBError):
    """Không thể đọc hoặc ghi dữ liệu JSON."""
