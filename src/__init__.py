from src.file_naming import FileNameFormatter
from src.naming_policy import resolve as _resolve_naming


# Keep legacy callers compatible while making the new naming policy authoritative.
FileNameFormatter.resolve_source_metadata = classmethod(
    lambda cls, source, extract_root: _resolve_naming(source, extract_root)
)
