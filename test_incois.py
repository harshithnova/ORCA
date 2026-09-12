from providers.incois.adapter import download_incois_file


class FakeResponse:
    def __init__(self):
        self.chunks = [b"ORCA", b"-INCOIS", b"-TEST"]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self, size=-1):
        if self.chunks:
            return self.chunks.pop(0)
        return b""


def test_download_incois_file(monkeypatch, tmp_path):
    def fake_urlopen(request, timeout=60):
        return FakeResponse()

    monkeypatch.setattr(
        "providers.incois.adapter.urlopen",
        fake_urlopen,
    )

    output_file = tmp_path / "incois_test.nc"

    result = download_incois_file(
        "https://incois.gov.in/test.nc",
        str(output_file),
    )

    assert output_file.exists()
    assert output_file.read_bytes() == b"ORCA-INCOIS-TEST"

    assert result["source"] == "INCOIS"
    assert result["data_mode"] == "CACHED_OFFICIAL"
    assert result["file_path"] == str(output_file)
    assert result["size_bytes"] == len(b"ORCA-INCOIS-TEST")