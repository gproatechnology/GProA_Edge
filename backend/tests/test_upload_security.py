"""
Tests for upload security validation.
"""
import pytest
from app.api.endpoints.files import validate_file_upload, ALLOWED_EXTENSIONS, MAX_FILE_SIZE


def test_valid_pdf_extension():
    """Valid PDF extension should pass."""
    is_valid, _ = validate_file_upload("test.pdf", b"%PDF-1.4")
    assert is_valid is True


def test_valid_excel_extension():
    """Valid Excel extension should pass with zip MIME (common on Windows)."""
    is_valid, _ = validate_file_upload("test.xlsx", b"PK")
    assert is_valid is True


def test_invalid_extension():
    """Invalid extension should fail."""
    is_valid, msg = validate_file_upload("test.exe", b"MZ")
    assert is_valid is False
    assert "not allowed" in msg.lower()


def test_oversized_file():
    """File over 50MB should fail."""
    large_content = b"x" * (51 * 1024 * 1024)  # 51MB
    is_valid, msg = validate_file_upload("test.pdf", large_content)
    assert is_valid is False
    assert "exceeds" in msg.lower()


def test_dwg_octet_stream_accepted():
    """DWG files detected as octet-stream should pass."""
    is_valid, _ = validate_file_upload("test.dwg", b"\x00\x00\x00\x00")
    assert is_valid is True


def test_empty_file():
    """Empty file should still pass extension check."""
    is_valid, _ = validate_file_upload("test.pdf", b"")
    assert is_valid is True


def test_xlsx_mime_validation():
    """XLSX files should pass MIME validation (zip type is allowed)."""
    xlsx_sig = b"PK\x03\x04" + b"\x00" * 100
    is_valid, _ = validate_file_upload("test.xlsx", xlsx_sig)
    assert is_valid is True


def test_docx_mime_validation():
    """DOCX files should pass MIME validation (zip type is allowed)."""
    docx_sig = b"PK\x03\x04" + b"\x00" * 100
    is_valid, _ = validate_file_upload("test.docx", docx_sig)
    assert is_valid is True