"""Điểm vào khi chạy ứng dụng bằng `uv run python -m fnb.main`."""

from fnb.bootstrap import build_context
from fnb.ui.app import create_app


def main() -> None:
    context = build_context()
    app = create_app(context)
    app.launch()


if __name__ == "__main__":
    main()
