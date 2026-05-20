"""
Data models for the Document Analysis & Migration Readiness Tool.

=== INTERVIEW EXPLANATION ===
We use Pydantic models to define the structure of our data.
Pydantic validates data types automatically - if someone passes a string 
where an integer is expected, it raises a clear error.

Think of these models as "contracts" - they define exactly what data 
flows through our system.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ReadabilityLevel(str, Enum):
    """Readability classification for documents."""
    EASY = "Easy"
    MEDIUM = "Medium"
    COMPLEX = "Complex"


class MigrationReadiness(str, Enum):
    """Migration readiness status."""
    READY = "Ready - Clean for migration"
    NEEDS_REVIEW = "Needs Review - Minor issues found"
    REQUIRES_RESTRUCTURING = "Requires Restructuring - Major issues found"


class DocumentMetrics(BaseModel):
    """
    Quantitative metrics extracted from a document.
    
    These are NUMBER-based measurements - things we can count.
    They help assess document complexity and migration effort.
    """
    file_name: str = Field(..., description="Original file name")
    file_type: str = Field(..., description="File extension (.docx or .pdf)")
    file_size_kb: float = Field(..., description="File size in kilobytes")
    total_pages: int = Field(default=0, description="Total number of pages")
    word_count: int = Field(default=0, description="Total word count")
    character_count: int = Field(default=0, description="Total character count")
    paragraph_count: int = Field(default=0, description="Number of paragraphs")
    heading_count: int = Field(default=0, description="Number of headings/sections")
    avg_words_per_paragraph: float = Field(default=0.0, description="Average words per paragraph")
    has_tables: bool = Field(default=False, description="Whether document contains tables")
    has_images: bool = Field(default=False, description="Whether document contains images")
    estimated_reading_time_min: float = Field(default=0.0, description="Estimated reading time in minutes")
    unique_word_ratio: float = Field(default=0.0, description="Ratio of unique words to total words")
    heading_list: list[str] = Field(default_factory=list, description="List of headings found")


class AIAnalysis(BaseModel):
    """
    AI-driven analysis results.
    
    These are QUALITATIVE assessments - things that require
    understanding of language and context.
    """
    readability_level: str = Field(default="Medium", description="Easy / Medium / Complex")
    readability_explanation: str = Field(default="", description="Explanation of readability assessment")
    content_clarity_score: int = Field(default=5, ge=1, le=10, description="Content clarity score 1-10")
    content_clarity_explanation: str = Field(default="", description="Explanation of clarity assessment")
    structural_quality: str = Field(default="Moderate", description="Well-organized / Moderate / Fragmented")
    structural_quality_explanation: str = Field(default="", description="Explanation of structural quality")
    migration_readiness: str = Field(default="Needs Review", description="Ready / Needs Review / Requires Restructuring")
    migration_readiness_explanation: str = Field(default="", description="Explanation of migration readiness")
    suggestions: list[str] = Field(default_factory=list, description="Actionable improvement suggestions")
    overall_score: int = Field(default=5, ge=1, le=10, description="Overall document quality score 1-10")
    tone_active_voice_pct: int = Field(default=100, description="Percentage of active voice sentences")
    tone_assessment_label: str = Field(default="Excellent", description="Overall active voice tone classification")
    tone_passive_sentences: list[str] = Field(default_factory=list, description="Examples of passive voice sentences detected")


class AnalysisReport(BaseModel):
    """
    Complete analysis report combining metrics and AI analysis.
    This is the final output returned to the frontend.
    """
    document_metrics: DocumentMetrics
    ai_analysis: AIAnalysis
    summary: str = Field(default="", description="Brief summary of the analysis")
    analysis_method: str = Field(default="rule-based", description="AI model used or 'rule-based'")
    markdown_content: str = Field(default="", description="Converted Document360 Markdown content")


class ParagraphMetadata(BaseModel):
    """
    Metadata tracking the location of text blocks for precise migration feedback.
    """
    text: str
    page: int = 1
    line: int = 1


class ParsedDocument(BaseModel):
    """
    Intermediate representation of a parsed document.
    This is the output of the parsers, before metrics are calculated.
    """
    file_name: str
    file_type: str
    file_size_kb: float
    full_text: str = ""
    markdown_content: str = ""
    paragraphs: list[str] = Field(default_factory=list)
    headings: list[str] = Field(default_factory=list)
    total_pages: int = 0
    has_tables: bool = False
    has_images: bool = False
    paragraph_metadata: list[ParagraphMetadata] = Field(default_factory=list)
