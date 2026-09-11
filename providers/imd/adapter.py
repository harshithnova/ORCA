from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


IMD_KOCHI_URL = (
    "https://city.imd.gov.in/citywx/"
    "city_weather_test_try_warnings.php?id=43353"
)


def download_imd_kochi(output_path: str) -> dict:
    """Download the official IMD Kochi forecast page."""

    request = Request(
        IMD_KOCHI_URL,
        headers={"User-Agent": "ORCA-Data-Provider/1.0"},
    )

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        with urlopen(request, timeout=30) as response:
            content = response.read()

        with open(destination, "wb") as file:
            file.write(content)

    except Exception as exc:
        if destination.exists():
            destination.unlink()

        raise RuntimeError(
            f"IMD Kochi download failed: {exc}"
        ) from exc

    return {
        "source": "IMD",
        "source_url": IMD_KOCHI_URL,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "data_mode": "CACHED_OFFICIAL",
        "data_type": "FORECAST",
        "file_path": str(destination),
        "size_bytes": destination.stat().st_size,
    }