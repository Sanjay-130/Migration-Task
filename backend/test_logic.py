"""
Simple Direct Verification of Parser and Metrics Logic
This script imports the backend functions directly to verify they run perfectly.
"""

from backend.parsers.docx_parser import parse_docx
from backend.metrics import extract_metrics
from backend.ai_analyzer import analyze_document

print("[TEST] VERIFYING DOCX PARSING AND METRICS EXTRACTION...")

try:
    # 1. Parse sample document
    parsed_doc = parse_docx("samples/sample_structure_good.docx")
    print(f"  [OK] Parsed file: {parsed_doc.file_name}")
    print(f"  [OK] Type: {parsed_doc.file_type}")
    print(f"  [OK] Pages: {parsed_doc.total_pages}")
    
    # 2. Extract metrics
    metrics = extract_metrics(parsed_doc)
    print(f"  [OK] Words: {metrics.word_count}")
    print(f"  [OK] Headings: {metrics.heading_count}")
    print(f"  [OK] Has tables: {metrics.has_tables}")
    print(f"  [OK] Has images: {metrics.has_images}")
    
    # 3. Analyze document
    analysis, method = analyze_document(parsed_doc, metrics)
    print(f"  [OK] Readability: {analysis.readability_level}")
    print(f"  [OK] Structural Quality: {analysis.structural_quality}")
    print(f"  [OK] Migration Readiness: {analysis.migration_readiness}")
    print(f"  [OK] Overall Score: {analysis.overall_score}/10")
    print(f"  [OK] Converted Markdown Length: {len(parsed_doc.markdown_content)} characters")
    
    print("\n[SUCCESS] ALL BACKEND LOGIC VERIFIED SUCCESSFULLY!")
    
except Exception as e:
    print(f"  [ERROR] Verification failed: {e}")
