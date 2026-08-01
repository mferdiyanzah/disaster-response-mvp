"""Pure filter logic for mutual-aid reports — testable without Streamlit."""


def filter_reports(
    reports: list[dict],
    statuses: list[str],
    report_types: list[str],
) -> list[dict]:
    """Return reports matching selected status and report_type values."""
    return [
        r
        for r in reports
        if r.get("status") in statuses and r.get("report_type") in report_types
    ]
