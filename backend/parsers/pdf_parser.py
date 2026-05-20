"""
PDF Parser Module
Extracts text, structure, and metadata from PDF (.pdf) files.

=== INTERVIEW EXPLANATION ===
How PDF files work:
- Unlike Word files, PDFs do NOT store headings, paragraphs, or lists.
- PDFs are designed for print: they only know "put character 'X' at position (X, Y)".
- Because of this, extracting structured content is much harder!

How we solve it:
- We use pdfplumber, which extracts text page-by-page.
- To find headings, we use "heuristics" (smart rules):
  1. A heading is usually short (e.g. less than 10 words).
  2. It might be in ALL CAPS.
  3. It might start with section numbers (e.g. "1.1", "Chapter 2").
  4. It does NOT end with standard sentence punctuation like periods.

This is a very practical, real-world engineering solution to PDF layout parsing.
"""

import pdfplumber
from backend.models import ParsedDocument, ParagraphMetadata
import os
import re


def _clean_double_strike(text: str) -> str:
    """
    Cleans PDF double-strike bold text artifacts (e.g., 'PPllaannss' -> 'Plans').
    
    This occurs when a PDF generator prints characters twice with a very small 
    offset to make them bold.
    """
    words = text.split(" ")
    cleaned_words = []
    for word in words:
        n = len(word)
        # Doubled words are always even length, at least 2 characters
        if n >= 2 and n % 2 == 0:
            is_doubled = True
            for i in range(0, n, 2):
                if word[i] != word[i+1]:
                    is_doubled = False
                    break
            if is_doubled:
                cleaned_words.append(word[::2])
                continue
        cleaned_words.append(word)
    return " ".join(cleaned_words)


def _is_valid_heading(line: str) -> bool:
    """
    Validates if a line qualifies as a section heading in technical documentation.
    Filters out noise like page numbers, split sentences, and callout labels.
    """
    clean_line = line.strip()
    if len(clean_line) < 3:
        return False
        
    # Must start with uppercase letter, digit, or standard markdown headers
    if not (clean_line[0].isupper() or clean_line[0].isdigit() or clean_line[0] in ['#', '*']):
        return False
        
    # Filter list item markers starting with lowercase (e.g. "a. ", "b. ")
    if re.match(r'^[a-z]\.\s', clean_line):
        return False
        
    # Filter page numbering indicators (e.g., "Page 1 of 31", "Pg. 12")
    if re.match(r'^(page|pg\.?)\s*\d+|^\d+\s*of\s*\d+', clean_line, re.IGNORECASE):
        return False
        
    # Filter standalone callout labels (e.g., "NOTE", "CAUTION")
    callout_keywords = {"note", "caution", "warning", "tip", "important", "info", "attention"}
    words = re.findall(r'\b\w+\b', clean_line.lower())
    if len(words) == 1 and words[0] in callout_keywords:
        return False
    if clean_line.lower() in callout_keywords:
        return False
        
    return True


def parse_pdf(file_path: str) -> ParsedDocument:
    """
    Parse a PDF file and extract structured content.
    
    Args:
        file_path: Path to the .pdf file
        
    Returns:
        ParsedDocument with extracted text, headings, paragraphs, etc.
    """
    file_size_kb = round(os.path.getsize(file_path) / 1024, 2)
    file_name = os.path.basename(file_path)
    
    try:
        pdf = pdfplumber.open(file_path)
    except Exception as e:
        return ParsedDocument(
            file_name=file_name,
            file_type=".pdf",
            file_size_kb=file_size_kb,
            full_text=f"[Error: Could not open PDF. {str(e)}]",
            paragraphs=[],
            headings=[],
            total_pages=0,
        )
    
    total_pages = len(pdf.pages)
    paragraphs = []
    headings = []
    full_text_parts = []
    markdown_parts = []
    current_paragraph_lines = []
    paragraph_metadata = []
    has_tables = False
    has_images = False
    
    # State tracking for start of paragraph blocks
    start_page_ref = 1
    start_line_ref = 1
    
    def flush_paragraph():
        if current_paragraph_lines:
            para_text = " ".join(current_paragraph_lines)
            paragraphs.append(para_text)
            markdown_parts.append(para_text)
            paragraph_metadata.append(ParagraphMetadata(
                text=para_text,
                page=start_page_ref,
                line=start_line_ref
            ))
            current_paragraph_lines.clear()
            
    for page_idx, page in enumerate(pdf.pages):
        page_num = page_idx + 1
        
        # Check for tables on the page
        if page.extract_tables():
            has_tables = True
        
        # Check for images on the page
        if page.images:
            has_images = True
            
        # Extract text from each page
        page_text = page.extract_text()
        if not page_text:
            continue
        
        # Split page text into lines for heading detection
        lines = page_text.split("\n")
        
        for line_idx, line in enumerate(lines):
            line_num = line_idx + 1
            line = line.strip()
            
            if not line:
                # Empty line marks paragraph boundary
                flush_paragraph()
                continue
            
            # Clean PDF-specific text artifacts
            # 1. Replace ligatures (e.g. (cid:37) -> fi)
            line = line.replace("(cid:37)", "fi")
            # 2. Clean double-strike bold characters
            line = _clean_double_strike(line)
            # 3. Clean private-use Unicode font icon artifacts (e.g. checkbox or bullet symbols)
            line = re.sub(r'[\ue000-\uf8ff]', '', line).strip()
            
            if not line:
                continue
            
            full_text_parts.append(line)
            
            # --- HEURISTICS FOR HEADING DETECTION ---
            word_count = len(line.split())
            
            # Check basic structure rules
            is_valid = _is_valid_heading(line)
            
            # Pattern matching for section numbering (e.g. 1.0, 1.1, Chapter 1, Section A)
            has_number_prefix = bool(re.match(r'^(\d+\.?\d*\.?\s|Chapter\s|Section\s|Part\s)', line, re.IGNORECASE))
            
            # Standard short header length check (regular title is max 8 words; numbered titles up to 12 words)
            is_short = word_count <= 8 or (has_number_prefix and word_count <= 12)
            is_all_caps = line.isupper() and word_count >= 2
            
            is_heading = is_valid and (
                (is_short and (is_all_caps or has_number_prefix)) or 
                (is_short and not line.endswith(('.', ',', ';', ':', '?', '!')))
            )
            
            if is_heading:
                # Flush the current paragraph before writing the heading
                flush_paragraph()
                
                # Determine PDF heading level based on numbers and formatting
                level = 2
                if re.match(r'^\d+\.\d+\.\d+\s', line):
                    level = 3
                elif re.match(r'^\d+\.\d+\.\d+\.\d+\s', line):
                    level = 4
                elif re.match(r'^\d+\s', line) or line.isupper():
                    level = 1
                
                headings.append(f"H{level}: {line}")
                markdown_parts.append(f"{'#' * level} {line}")
            else:
                # If starting a new paragraph block, record coordinates
                if not current_paragraph_lines:
                    start_page_ref = page_num
                    start_line_ref = line_num
                current_paragraph_lines.append(line)
                
    # Flush any remaining paragraph lines
    flush_paragraph()
    
    pdf.close()
    
    full_text = "\n\n".join(full_text_parts)
    markdown_content = "\n\n".join(markdown_parts)
    
    # Handle empty/scanned PDFs (image-only PDFs where extract_text() returns None)
    if not full_text.strip():
        full_text = "[No extractable text found. This may be a scanned/image-only PDF.]"
        markdown_content = full_text
    
    return ParsedDocument(
        file_name=file_name,
        file_type=".pdf",
        file_size_kb=file_size_kb,
        full_text=full_text,
        markdown_content=markdown_content,
        paragraphs=paragraphs,
        headings=headings,
        total_pages=total_pages,
        has_tables=has_tables,
        has_images=has_images,
        paragraph_metadata=paragraph_metadata,
    )
