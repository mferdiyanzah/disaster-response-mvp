"""F-01: dashboard report filter."""
from dashboard.services.report_filter import filter_reports

REPORTS = [
    {"status": "OPEN", "report_type": "NEED_HELP"},
    {"status": "RESOLVED", "report_type": "OFFER_HELP"},
    {"status": "OPEN", "report_type": "OFFER_HELP"},
]


def test_filter_reports_open_need_help_only():
    result = filter_reports(REPORTS, ["OPEN"], ["NEED_HELP"])
    assert len(result) == 1
    assert result[0]["report_type"] == "NEED_HELP"


def test_filter_reports_multiple_statuses():
    result = filter_reports(REPORTS, ["OPEN"], ["NEED_HELP", "OFFER_HELP"])
    assert len(result) == 2
