"""Lỗi ứng dụng dùng chung để UI có thể đưa ra thông báo thân thiện."""


class FNBError(Exception):
    """Lỗi cơ sở của ứng dụng F&B."""


class ValidationError(FNBError):
    """Dữ liệu đầu vào không hợp lệ."""


class NotFoundError(FNBError):
    """Không tìm thấy mã món hoặc đơn hàng."""


class ConflictError(FNBError):
    """Xung đột với dữ liệu hiện tại."""


class InvalidStateError(FNBError):
    """Trạng thái hiện tại không cho phép thực hiện hành động."""


class StorageError(FNBError):
    """Không thể đọc hoặc ghi dữ liệu JSON."""
