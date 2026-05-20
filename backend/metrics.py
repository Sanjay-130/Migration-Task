"""
Metrics Extraction Module
Calculates quantitative document metrics from parsed documents.

=== INTERVIEW EXPLANATION ===
Why do we calculate these specific metrics?
- Word count: Gives us the volume of content.
- Heading count: Tells us if the document is structured or just a flat list.
- Paragraph count: Helps us look at content density.
- Average words per paragraph: A key readability metric. Paragraphs with > 120 words 
  are hard for users to read on screens (e.g. Document360 web pages).
- Unique word ratio: Measures lexical diversity (richness of vocabulary). 
  Higher numbers can indicate more complex technical language.
"""

from backend.models import ParsedDocument, DocumentMetrics


def extract_metrics(parsed_doc: ParsedDocument) -> DocumentMetrics:
    """
    Calculate document metrics from a parsed document.
    
    Args:
        parsed_doc: A ParsedDocument object with extracted content
        
    Returns:
        DocumentMetrics with all calculated metrics
    """
    # Split text by whitespace to count words
    words = parsed_doc.full_text.split()
    word_count = len(words)
    
    # Character count (excluding whitespace characters)
    character_count = sum(len(word) for word in words)
    
    # Count paragraphs and headings
    paragraph_count = len(parsed_doc.paragraphs)
    heading_count = len(parsed_doc.headings)
    
    # Average words per paragraph (prevent division by zero)
    if paragraph_count > 0:
        avg_words_per_paragraph = round(word_count / paragraph_count, 1)
    else:
        avg_words_per_paragraph = 0.0
    
    # Estimated reading time (average adult reading speed is ~225 words per minute)
    estimated_reading_time_min = round(word_count / 225, 1)
    
    # Unique word ratio (vocabulary richness)
    if word_count > 0:
        # Strip common punctuation from words for a cleaner count
        unique_words = set(word.lower().strip('.,!?;:()[]{}"\'-') for word in words)
        unique_word_ratio = round(len(unique_words) / word_count, 3)
    else:
        unique_word_ratio = 0.0
    
    return DocumentMetrics(
        file_name=parsed_doc.file_name,
        file_type=parsed_doc.file_type,
        file_size_kb=parsed_doc.file_size_kb,
        total_pages=parsed_doc.total_pages,
        word_count=word_count,
        character_count=character_count,
        paragraph_count=paragraph_count,
        heading_count=heading_count,
        avg_words_per_paragraph=avg_words_per_paragraph,
        has_tables=parsed_doc.has_tables,
        has_images=parsed_doc.has_images,
        estimated_reading_time_min=estimated_reading_time_min,
        unique_word_ratio=unique_word_ratio,
        heading_list=parsed_doc.headings,
    )
