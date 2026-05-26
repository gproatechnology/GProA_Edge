"""
Tests for async parser correctness.
"""
import pytest
import asyncio
import tempfile
import os

from app.services.parsers.excel_parser import ExcelParser
from app.services.parsers.docx_parser import DocxParser
from app.services.parsers.pdf_parser import PDFParser
from app.services.parsers.cad_parser import CADParser


@pytest.mark.asyncio
async def test_excel_parser_async():
    """Excel parser should run correctly in asyncio.to_thread."""
    parser = ExcelParser()
    
    # Create minimal test xlsx content
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        f.write(b"PK")  # Minimal zip header
        temp_path = f.name
    
    try:
        result = await asyncio.to_thread(parser.parse, temp_path)
        assert "error" in result or "sheets" in result
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_docx_parser_async():
    """DOCX parser should run correctly in asyncio.to_thread."""
    parser = DocxParser()
    
    # Create minimal test docx content (zip-based)
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        f.write(b"PK")
        temp_path = f.name
    
    try:
        result = await asyncio.to_thread(parser.parse, temp_path)
        assert "error" in result or "content_text" in result
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_pdf_parser_async():
    """PDF parser should run correctly in asyncio.to_thread."""
    parser = PDFParser()
    
    # Create minimal PDF content
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b"%PDF-1.4")
        temp_path = f.name
    
    try:
        result = await asyncio.to_thread(parser.parse, temp_path)
        assert "error" in result or "format" in result
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_cad_parser_async():
    """CAD parser should run correctly in asyncio.to_thread."""
    parser = CADParser()
    
    # Create minimal DXF content
    content = b"0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF"
    with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        result = await asyncio.to_thread(parser.parse, temp_path)
        assert "error" in result or "format" in result
    finally:
        os.unlink(temp_path)