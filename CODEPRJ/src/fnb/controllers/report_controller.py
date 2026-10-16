from fnb.services.report_service import ReportService


class ReportController:
    def __init__(self, report_service: ReportService) -> None:
        self._report_service = report_service

    def daily_summary(self, day: str | None = None) -> dict:
        return self._report_service.daily_summary(day)
