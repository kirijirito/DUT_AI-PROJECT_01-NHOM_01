"""Đọc/ghi danh sách bản ghi JSON, không chứa luật nghiệp vụ nhà hàng."""

import json
from pathlib import Path
from typing import Any

from fnb.exceptions import StorageError


class JsonStore:
    """Lớp mỏng thao tác một file JSON có nội dung là list[dict]."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load_records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"Không đọc được JSON tại {self.path}: {exc}") from exc
        if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
            raise StorageError(f"File {self.path} phải chứa một danh sách các object JSON.")
        return data

    def save_records(self, records: list[dict[str, Any]]) -> None:
        """Ghi vào file tạm trước, sau đó thay file chính để giảm nguy cơ file ghi dở."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_name(self.path.name + ".tmp")
        try:
            temp_path.write_text(
                json.dumps(records, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temp_path.replace(self.path)
        except OSError as exc:
            raise StorageError(f"Không ghi được JSON tại {self.path}: {exc}") from exc
