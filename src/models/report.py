from datetime import datetime

from pydantic import BaseModel, Field


class HourlyReportOut(BaseModel):
    report_date: datetime
    total_events: int
    average_magnitude: float
    max_magnitude: float
    top_locations: list[str] = Field(default_factory=list)
