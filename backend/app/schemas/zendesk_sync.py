from pydantic import BaseModel, field_validator
from datetime import date

class ZendeskSyncRequest(BaseModel):
    org_id: int
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def check_order(cls, v, info):
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be >= start_date")
        return v