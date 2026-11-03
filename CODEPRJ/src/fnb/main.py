"""Điểm bắt đầu ứng dụng."""

from fnb.bootstrap import build_context
from fnb.ui.app import CUSTOM_CSS, FNB_THEME, create_app


def main() -> None:
    app = create_app(build_context())
    app.launch(theme=FNB_THEME, css=CUSTOM_CSS)


if __name__ == "__main__":
    main()
