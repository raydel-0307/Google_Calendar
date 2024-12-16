from datetime import datetime, timezone
from typing import Union


def convert_to_rfc3339(date_str: str) -> str:
    try:
        if "T" in date_str:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")

        dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError(
            f"Invalid datetime format: {date_str}. Expected 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DDTHH:MM'"
        )
