from src.storage.uri import parse_storage_uri


def test_local_uri():
    uri = parse_storage_uri("local://storage/input")
    assert uri.scheme == "local"
    assert uri.value == "storage/input"


def test_gdrive_uri():
    uri = parse_storage_uri("gdrive://abc123")
    assert uri.scheme == "gdrive"
    assert uri.value == "abc123"


def test_reject_unknown_provider():
    try:
        parse_storage_uri("dropbox://abc")
    except ValueError as exc:
        assert "Unsupported storage URI" in str(exc)
    else:
        raise AssertionError("Unknown provider must be rejected")


def test_https_uri_is_preserved():
    uri = parse_storage_uri("https://example.test/video.mp4?download=1")
    assert uri.scheme == "https"
    assert uri.value == "https://example.test/video.mp4?download=1"


def test_bare_path_defaults_to_local():
    uri = parse_storage_uri("relative/input")
    assert uri.scheme == "local"
    assert uri.value == "relative/input"


def test_windows_drive_path_defaults_to_local():
    uri = parse_storage_uri(r"C:\media\input.zip")
    assert uri.scheme == "local"
    assert uri.value == r"C:\media\input.zip"


def test_file_url_is_rejected():
    with pytest.raises(ValueError, match="Unsupported storage URI"):
        parse_storage_uri("file:///etc/passwd")
