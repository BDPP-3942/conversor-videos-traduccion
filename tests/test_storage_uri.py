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
