"""PDF text extraction using pdfplumber."""
import pdfplumber
from typing import List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import TextBlock, ExtractedDocument


def extract_pdf(file_path: str) -> ExtractedDocument:
    """
    Extract text blocks from a PDF file.
    
    Groups words into lines by vertical proximity, then lines into paragraphs
    by vertical gap (gap > 15pt = new paragraph).
    """
    blocks: List[TextBlock] = []
    y_gap_threshold = 15  # Points - gap larger than this starts a new paragraph
    
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # Extract words with font metadata
            words = page.extract_words(extra_attrs=["fontname", "size"])
            
            if not words:
                continue
            
            # Group words into lines by vertical proximity
            lines = []
            current_line = []
            current_y = None
            
            for word in words:
                word_y = (word["top"] + word["bottom"]) / 2
                
                if current_y is None:
                    current_line = [word]
                    current_y = word_y
                elif abs(word_y - current_y) < 5:  # Same line if within 5pt
                    current_line.append(word)
                else:
                    # New line
                    if current_line:
                        lines.append(current_line)
                    current_line = [word]
                    current_y = word_y
            
            if current_line:
                lines.append(current_line)
            
            # Group lines into paragraphs
            paragraphs = []
            current_para = []
            prev_bottom = None
            
            for line in lines:
                if not line:
                    continue
                
                line_top = min(w["top"] for w in line)
                line_bottom = max(w["bottom"] for w in line)
                
                if prev_bottom is None:
                    current_para = [line]
                    prev_bottom = line_bottom
                elif (line_top - prev_bottom) > y_gap_threshold:
                    # New paragraph
                    if current_para:
                        paragraphs.append(current_para)
                    current_para = [line]
                    prev_bottom = line_bottom
                else:
                    # Continue current paragraph
                    current_para.append(line)
                    prev_bottom = line_bottom
            
            if current_para:
                paragraphs.append(current_para)
            
            # Create TextBlock for each paragraph
            for block_idx, para_lines in enumerate(paragraphs):
                # Collect all words from paragraph lines
                para_words = []
                for line in para_lines:
                    para_words.extend(line)
                
                if not para_words:
                    continue
                
                # Extract text
                text = " ".join(w["text"] for w in sorted(para_words, key=lambda w: w["x0"]))
                text = " ".join(text.split())  # Normalize whitespace
                
                if not text.strip():
                    continue
                
                # Calculate bounding box
                x0 = min(w["x0"] for w in para_words)
                y0 = min(w["top"] for w in para_words)
                x1 = max(w["x1"] for w in para_words)
                y1 = max(w["bottom"] for w in para_words)
                
                # Calculate average font size and name
                font_sizes = [w.get("size", 12) for w in para_words if w.get("size")]
                avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12.0
                
                font_names = [w.get("fontname", "Helvetica") for w in para_words if w.get("fontname")]
                most_common_font = max(set(font_names), key=font_names.count) if font_names else "Helvetica"
                
                # Mark as header if average font size > 14pt
                is_header = avg_font_size > 14
                
                block_id = f"p{page_num}_b{block_idx}"
                
                block = TextBlock(
                    block_id=block_id,
                    text=text,
                    page=page_num,
                    bbox=(x0, y0, x1, y1),
                    font_size=avg_font_size,
                    font_name=most_common_font,
                    is_header=is_header
                )
                blocks.append(block)
    
    # Extract PDF metadata
    metadata = {}
    with pdfplumber.open(file_path) as pdf:
        if pdf.metadata:
            metadata = pdf.metadata
    
    return ExtractedDocument(
        source_path=file_path,
        format="pdf",
        blocks=blocks,
        metadata=metadata
    )

