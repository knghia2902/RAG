"""Multi-format parsers and published source profile normalization."""
from app.rag.parsers.base import (
    FormatAdapter,
    MalformedSourceError,
    ParsedRecord,
    ParserDiagnostic,
    ParseResult,
    UnsupportedFormatError,
)
from app.rag.parsers.docling_adapter import DoclingAdapter
from app.rag.parsers.profiles import (
    PROFILES,
    ProfileDefinition,
    ProfileValidationResult,
    get_profile,
    normalize_timestamp,
    validate_records,
)
from app.rag.parsers.spreadsheet import SpreadsheetParser
from app.rag.parsers.structured import StructuredParser
from app.rag.parsers.text_log import TextLogParser

__all__ = [
    "DoclingAdapter",
    "FormatAdapter",
    "MalformedSourceError",
    "ParsedRecord",
    "ParserDiagnostic",
    "ParseResult",
    "SpreadsheetParser",
    "StructuredParser",
    "TextLogParser",
    "UnsupportedFormatError",
    "PROFILES",
    "ProfileDefinition",
    "ProfileValidationResult",
    "get_profile",
    "normalize_timestamp",
    "validate_records",
]
