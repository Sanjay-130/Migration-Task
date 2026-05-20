
import os
import json
import re
from backend.models import DocumentMetrics, AIAnalysis, ParsedDocument

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def analyze_with_gemini(parsed_doc: ParsedDocument, metrics: DocumentMetrics) -> AIAnalysis:
    text = parsed_doc.full_text
    api_key = os.environ.get("GEMINI_API_KEY", "")
    
    if not api_key or not GEMINI_AVAILABLE:
        return analyze_with_rules(parsed_doc, metrics)
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Truncate text to avoid token limits (max ~4000 words for analysis)
        words = text.split()
        if len(words) > 4000:
            truncated_text = " ".join(words[:2000]) + "\n\n[...TRUNCATED...]\n\n" + " ".join(words[-2000:])
        else:
            truncated_text = text
        
        prompt = f"""You are a document migration specialist analyzing a document for migration to Document360.

DOCUMENT TEXT:
---
{truncated_text}
---

DOCUMENT METRICS:
- Word count: {metrics.word_count}
- Paragraphs: {metrics.paragraph_count}
- Headings: {metrics.heading_count}
- Avg words per paragraph: {metrics.avg_words_per_paragraph}
- Has tables: {metrics.has_tables}
- Has images: {metrics.has_images}

Analyze this document and respond with ONLY a valid JSON object (no markdown, no code blocks):
{
    "readability_level": "Easy" or "Medium" or "Complex",
    "readability_explanation": "Brief explanation why",
    "content_clarity_score": 1-10 integer,
    "content_clarity_explanation": "Brief explanation",
    "structural_quality": "Well-organized" or "Moderate" or "Fragmented",
    "structural_quality_explanation": "Brief explanation",
    "migration_readiness": "Clean" or "Needs Review" or "Requires Restructuring",
    "migration_readiness_explanation": "Brief explanation",
    "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
    "overall_score": 1-10 integer,
    "tone_active_voice_pct": 0-100 integer representing percentage of active voice sentences,
    "tone_assessment_label": "Excellent (Highly Active)" or "Good (Moderately Active)" or "Review Needed (Too Passive)",
    "tone_passive_sentences": ["example passive sentence 1", "example passive sentence 2"]
}"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response - remove markdown code blocks if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        
        result = json.loads(response_text)
        
        # Post-process tone_passive_sentences to find page numbers
        if "tone_passive_sentences" in result and isinstance(result["tone_passive_sentences"], list):
            resolved_passives = []
            for sentence in result["tone_passive_sentences"]:
                clean_s = sentence.strip('"\' ')
                loc = _find_sentence_location(clean_s, parsed_doc.paragraph_metadata)
                if not re.search(r'\[Page \d+\]$', clean_s):
                    resolved_passives.append(clean_s + loc)
                else:
                    resolved_passives.append(clean_s)
            result["tone_passive_sentences"] = resolved_passives

        return AIAnalysis(**result)
        
    except Exception as e:
        print(f"Gemini API error: {e}. Falling back to rule-based analysis.")
        return analyze_with_rules(parsed_doc, metrics)


def _find_sentence_location(sentence: str, paragraph_metadata: list) -> str:
    """
    Looks up a sentence in paragraph metadata and returns a formatted Page string.
    Uses normalized alphanumeric fuzzy matching for robust matching.
    """
    clean_s = re.sub(r'[^a-zA-Z0-9]', '', sentence.lower())
    if not clean_s:
        return ""
    
    # Match the first 35 alphanumeric characters
    target_part = clean_s[:35]
    for meta in paragraph_metadata:
        clean_meta = re.sub(r'[^a-zA-Z0-9]', '', meta.text.lower())
        if target_part in clean_meta:
            return f" [Page {meta.page}]"
            
    # Fallback to plain substring check on original text
    for meta in paragraph_metadata:
        if sentence.lower()[:20] in meta.text.lower():
            return f" [Page {meta.page}]"
            
    return ""


        
def _calculate_tone_metrics(parsed_doc: ParsedDocument) -> tuple[int, int, str, list[str]]:
    """
    Scans document text to estimate active vs. passive voice structures.
    Uses lightweight NLP heuristic matching for technical verbs.
    """
    text = parsed_doc.full_text
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
    total_sentences = len(sentences)
    if total_sentences == 0:
        return 100, 0, "Excellent (Highly Active)", []
        
    be_verbs = {"is", "am", "are", "was", "were", "be", "been", "being"}
    common_participles = {
        "done", "sent", "given", "made", "seen", "run", "taken", "written", 
        "built", "found", "read", "shown", "chosen", "drawn", "driven", 
        "known", "begun", "broken", "cut", "set", "spent", "left", "kept"
    }
    
    passive_count = 0
    passive_examples = []
    
    for sentence in sentences:
        words = re.findall(r'\b\w+\b', sentence.lower())
        is_passive = False
        
        for i in range(len(words) - 1):
            if words[i] in be_verbs:
                next_word = words[i+1]
                if next_word.endswith("ed") or next_word in common_participles:
                    is_passive = True
                    if len(passive_examples) < 5:
                        loc = _find_sentence_location(sentence, parsed_doc.paragraph_metadata)
                        passive_examples.append(sentence[:80] + ("..." if len(sentence) > 80 else "") + loc)
                    break
        if is_passive:
            passive_count += 1
            
    active_voice_pct = round(((total_sentences - passive_count) / total_sentences) * 100)
    
    if active_voice_pct >= 85:
        label = "Excellent (Highly Active)"
    elif active_voice_pct >= 60:
        label = "Good (Moderately Active)"
    else:
        label = "Review Needed (Too Passive)"
        
    return active_voice_pct, passive_count, label, passive_examples


def analyze_with_rules(parsed_doc: ParsedDocument, metrics: DocumentMetrics) -> AIAnalysis:
    """
    Rule-based document analysis fallback.
    
    Uses heuristic rules based on document metrics to assess quality.
    This runs when Gemini API is unavailable.
    
    The rules are based on industry standards for technical documentation:
    - Optimal paragraph length: 40-150 words
    - Minimum heading ratio: 1 heading per 300 words
    - Readability based on word complexity and sentence length
    """
    suggestions = []
    overall_score = 5
    text = parsed_doc.full_text
    
    # --- READABILITY ANALYSIS ---
    # Based on average words per paragraph and unique word ratio
    avg_words = metrics.avg_words_per_paragraph
    
    if avg_words <= 50:
        readability = "Easy"
        readability_exp = "Short paragraphs make this document easy to read and scan."
        overall_score += 1
    elif avg_words <= 120:
        readability = "Medium"
        readability_exp = "Paragraph length is moderate, suitable for most readers."
    else:
        readability = "Complex"
        readability_exp = f"Average paragraph length is {avg_words:.0f} words, which is quite dense. Consider breaking long paragraphs into smaller chunks."
        suggestions.append("Break long paragraphs into shorter ones (aim for 40-100 words each)")
        for meta in parsed_doc.paragraph_metadata:
            w_count = len(meta.text.split())
            if w_count > 120:
                loc = f" [Page {meta.page}]"
                suggestions.append(f"Break up dense paragraph at{loc} ({w_count} words; aim for 40-100 words)")
        overall_score -= 1
    
    # --- CONTENT CLARITY ---
    # Based on vocabulary richness and content consistency
    clarity_score = 5
    
    if metrics.word_count < 50:
        clarity_score = 3
        clarity_exp = "Document has very little content, making clarity assessment difficult."
        suggestions.append("Add more content to make the document substantive")
    elif metrics.unique_word_ratio > 0.7:
        clarity_score = 7
        clarity_exp = "High vocabulary diversity suggests well-crafted, non-repetitive content."
        overall_score += 1
    elif metrics.unique_word_ratio > 0.4:
        clarity_score = 6
        clarity_exp = "Good balance of vocabulary, content appears clear and consistent."
    else:
        clarity_score = 4
        clarity_exp = "Low vocabulary diversity may indicate repetitive content or filler text."
        suggestions.append("Review content for unnecessary repetition")
    
    # --- STRUCTURAL QUALITY ---
    # Based on heading count relative to content
    if metrics.heading_count == 0:
        structural = "Fragmented"
        structural_exp = "No headings found. The document lacks structural organization, which is critical for migration."
        suggestions.append("Add clear headings (H1, H2, H3) to organize content into sections")
        overall_score -= 2
    elif metrics.word_count > 0 and metrics.heading_count / (metrics.word_count / 300) >= 0.8:
        structural = "Well-organized"
        structural_exp = f"Document has {metrics.heading_count} headings providing good structural organization."
        overall_score += 1
    else:
        structural = "Moderate"
        structural_exp = f"Document has {metrics.heading_count} headings. Consider adding more headings to improve navigation."
        suggestions.append("Add more sub-headings to break content into scannable sections")
    
    # --- TONE ANALYSIS (Active vs. Passive Voice) ---
    active_pct, passive_cnt, tone_label, passive_ex = _calculate_tone_metrics(parsed_doc)
    if active_pct < 60:
        suggestions.append("Improve tone: Convert identified passive sentences to active voice for clearer instructions.")
        overall_score -= 1
        
    # --- MIGRATION READINESS ---
    # Composite assessment based on all factors
    if overall_score >= 7 and metrics.heading_count > 0:
        migration = "Clean"
        migration_exp = "Document is well-structured, clear, and clean/reusable for migration."
    elif overall_score >= 4:
        migration = "Needs Review"
        migration_exp = "Document needs some improvements before migration. Review the suggestions below."
    else:
        migration = "Requires Restructuring"
        migration_exp = "Document has significant structural or content issues that must be addressed before migration."
    
    # Additional suggestions based on content
    if metrics.has_images:
        suggestions.append("Verify all images have alt text for accessibility")
    if metrics.has_tables:
        suggestions.append("Ensure tables are properly formatted for the target platform")
    if metrics.estimated_reading_time_min > 15:
        suggestions.append("Consider splitting this into multiple smaller documents for better navigation")
    if not suggestions:
        suggestions.append("Document appears to be in good shape for migration")
    
    # Clamp score
    overall_score = max(1, min(10, overall_score))
    clarity_score = max(1, min(10, clarity_score))
    
    return AIAnalysis(
        readability_level=readability,
        readability_explanation=readability_exp,
        content_clarity_score=clarity_score,
        content_clarity_explanation=clarity_exp,
        structural_quality=structural,
        structural_quality_explanation=structural_exp,
        migration_readiness=migration,
        migration_readiness_explanation=migration_exp,
        suggestions=suggestions,
        overall_score=overall_score,
        tone_active_voice_pct=active_pct,
        tone_assessment_label=tone_label,
        tone_passive_sentences=passive_ex,
    )


def analyze_document(parsed_doc: ParsedDocument, metrics: DocumentMetrics) -> tuple[AIAnalysis, str]:
    """
    Main entry point for document analysis.
    Tries Gemini first, falls back to rules.
    
    Returns:
        Tuple of (AIAnalysis, method_used)
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    
    if api_key and GEMINI_AVAILABLE:
        analysis = analyze_with_gemini(parsed_doc, metrics)
        return analysis, "Google Gemini 1.5 Flash"
    else:
        analysis = analyze_with_rules(parsed_doc, metrics)
        return analysis, "Rule-based heuristic analysis"
