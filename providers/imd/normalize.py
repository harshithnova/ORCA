import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from html.parser import HTMLParser


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_td = False
        self.current_row = []
        self.rows = []
        self.text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self.in_td = True
            self.text = ""

    def handle_endtag(self, tag):
        if tag == "td" and self.in_td:
            value = " ".join(self.text.split())
            self.current_row.append(value)
            self.in_td = False

        elif tag == "tr":
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = []

    def handle_data(self, data):
        if self.in_td:
            self.text += data


def normalize_kochi_weather(
    raw_file: str,
    output_file: str,
    source_url: str,
) -> dict:
    """Normalize the first official IMD Kochi forecast into ORCA schema."""

    with open(
        raw_file,
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as file:
        html = file.read()

    parser = TableParser()
    parser.feed(html)

    forecast_row = None

    for row in parser.rows:
        if row and re.match(r"^\d{1,2}-[A-Za-z]{3}$", row[0]):
            forecast_row = row
            break

    if forecast_row is None:
        raise RuntimeError("Could not find an IMD forecast row.")

    # The IMD table contains empty cells.
    # Remove empty cells before reading the useful values.
    cleaned_row = [value for value in forecast_row if value.strip()]

    if len(cleaned_row) < 4:
        raise RuntimeError(
            f"Unexpected IMD forecast row: {forecast_row}"
        )

    # After removing empty cells:
    # Date | Min Temp | Max Temp | Forecast | Warning | RH...
    forecast_date = cleaned_row[0]
    weather_condition = cleaned_row[3]

    # Warning may be absent for some days.
    warning_level = None

    if len(cleaned_row) > 4:
        possible_warning = cleaned_row[4]

        if possible_warning.lower() not in {
            "80",
            "75",
            "no warning",
            "nil",
        }:
            warning_level = possible_warning

    retrieved_at = datetime.now(timezone.utc)

    day, month_text = forecast_date.split("-")
    month_number = datetime.strptime(
        month_text,
        "%b",
    ).month

    forecast_datetime = datetime(
        retrieved_at.year,
        month_number,
        int(day),
        tzinfo=timezone.utc,
    )

    record = {
        "latitude": 9.90,
        "longitude": 76.10,

        "issued_at": None,

        "valid_from": forecast_datetime.isoformat(),

        "valid_to": (
            forecast_datetime + timedelta(days=1)
        ).isoformat(),

        "wave_height_m": None,
        "wave_period_s": None,

        "wind_speed_ms": None,
        "wind_direction_deg": None,

        "rainfall_mm": None,
        "visibility_km": None,

        "weather_condition": weather_condition,
        "warning_level": warning_level,

        "source": "IMD",

        "source_url": source_url,

        "retrieved_at": retrieved_at.isoformat(),

        "data_mode": "CACHED_OFFICIAL",
        "data_type": "FORECAST",
    }

    Path(output_file).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            record,
            file,
            indent=2,
        )

    return record