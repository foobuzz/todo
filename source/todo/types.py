from enum import Enum
from typing import Optional, TypedDict


class DoTaskReportType(Enum):
    OK = 'ok'
    NOT_FOUND = 'not_found'
    ALREADY_DONE = 'already_done'
    RECURRENCE_ALREADY_DONE = 'recurrence_already_done'


class DoTasksReport(TypedDict):
    task_id: str
    report_type: DoTaskReportType
    next_occurrence_datetime: Optional[str]
