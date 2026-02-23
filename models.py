"""Data models for the translation pipeline."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class TextBlock:
    """Base class for all text blocks extracted from documents."""
    block_id: str          # Unique ID used to map translation back to position
    text: str              # English source text
    page: int              # Page number (0-indexed for PPTX/DOCX, 1-indexed for PDF)
    bbox: tuple            # (x0, y0, x1, y1) bounding box — used by PDF reconstruction
    font_size: float       # Average font size of the block
    font_name: str         # Font name string
    is_header: bool        # True if this block is a title or heading


@dataclass
class DocxBlock(TextBlock):
    """Text block from a Word document."""
    style_name: str        # Word style, e.g. "Heading 1", "Normal"
    paragraph_index: int   # Index in doc.paragraphs list — used for reconstruction lookup
    is_table_cell: bool    # True if this block comes from a table cell
    table_index: int       # Table index (-1 if not a table cell)
    row_index: int
    col_index: int


@dataclass
class PptxBlock(TextBlock):
    """Text block from a PowerPoint presentation."""
    slide_index: int
    shape_index: int
    shape_name: str        # Shape name as defined in the presentation
    paragraph_index: int   # Paragraph index within the shape's text frame
    placeholder_type: str  # e.g. "PP_PLACEHOLDER.TITLE", "PP_PLACEHOLDER.BODY"


@dataclass
class AudioBlock(TextBlock):
    """Text block from an audio file (transcribed by Whisper)."""
    start_time: float      # Segment start in seconds (from Whisper)
    end_time: float        # Segment end in seconds
    confidence: float = 0.0  # Reserved for future use


@dataclass
class ExtractedDocument:
    """Document with extracted text blocks ready for translation."""
    source_path: str
    format: str                      # "pdf", "docx", "pptx", "audio"
    blocks: List[TextBlock]          # Ordered list of all translatable blocks
    metadata: Dict = field(default_factory=dict)  # Format-specific metadata


@dataclass
class JobRecord:
    """Job record for API layer job tracking."""
    job_id: str
    status: str            # "pending" | "running" | "done" | "failed"
    filename: str          # Original uploaded filename
    progress: int          # 0–100
    blocks_total: int
    blocks_done: int
    output_path: Optional[str] = None  # Path to the translated output file
    error: Optional[str] = None        # Error message if status == "failed"
    duration_seconds: float = 0.0

