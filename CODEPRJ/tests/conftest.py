from pathlib import Path

import pytest

from fnb.bootstrap import build_context


@pytest.fixture
def context(tmp_path: Path):
    """Mỗi test dùng data directory riêng, không sửa JSON mẫu của project."""
    return build_context(tmp_path / "data")
