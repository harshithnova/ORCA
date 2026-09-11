from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


def download_incois_file(source_url: str, output_path: str) -> dict:
    """Download an official INCOIS file in small chunks."""

    if not source_url.startswith("https://incois.gov.in/"):
        raise ValueError("Source URL must be an official INCOIS URL.")

    request = Request(
        source_url,
        headers={"User-Agent": "ORCA-Data-Provider/1.0"},
    )

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        with urlopen(request, timeout=60) as response:
            with open(destination, "wb") as output_file:
                while True:
                    chunk = response.read(1024 * 1024)

                    if not chunk:
                        break

                    output_file.write(chunk)

    except Exception as exc:
        if destination.exists():
            destination.unlink()

        raise RuntimeError(f"INCOIS download failed: {exc}") from exc

    return {
        "source": "INCOIS",
        "source_url": source_url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "data_mode": "CACHED_OFFICIAL",
        "file_path": str(destination),
        "size_bytes": destination.stat().st_size,
    }