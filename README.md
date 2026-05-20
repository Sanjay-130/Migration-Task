# DocMigrate: Document Analysis and Migration Readiness Tool

DocMigrate is a developer tool designed to analyze Microsoft Word (docx) and PDF documents for structure, readability, technical tone, and migration readiness before publishing them to knowledge base platforms like Document360. 

It parses unstructured formatting, converts it into clean Markdown, calculates document metrics, and highlights specific paragraphs or sentences that need revision before migration.

---

## Core Capabilities

1. **Document Parsing and Markdown Conversion**
   * Docx Parser: Uses python-docx to traverse document elements, preserve document structure, and convert paragraphs, lists, styles, and tables directly into standard Markdown.
   * PDF Parser: Uses pdfplumber to extract text page-by-page. It resolves double-strike bold text and font ligatures (such as CID characters) to clean the document body.

2. **Quantitative Metrics Engine**
   * Measures document statistics including word count, paragraph count, heading count, unique word ratio, and reading time.
   * Word Page Estimation: Features a cumulative word-count page estimator (based on 350 words per page) that aligns paragraph page locations with the overall document length.
   * PDF Native Pages: Uses the native, physical page layout of PDF files to map elements accurately.

3. **Technical Tone and Readability Audit**
   * Uses regular expression heuristics to analyze sentence structure and identify passive voice verb usage (auxiliary verbs followed by past participles).
   * Identifies overly dense paragraphs (more than 120 words) that are hard to read on web screens.
   * Formats alerts with estimated page numbers to locate issues easily in the source file.

4. **Document Outline and Structural Health Audit**
   * Analyzes document heading levels (H1, H2, H3, H4) and builds a visual document tree.
   * Validates structural health by flagging hierarchical jumps (e.g., jumping from H1 directly to H3), missing H1 titles, duplicate heading text, and overly long headers.

5. **Interactive Web Workspace**
   * High-contrast design displaying quality scores and metrics.
   * Converted Markdown Exporter: Includes a side-by-side live editor that allows authors to copy pre-formatted content.
   * Click-to-Locate Navigation: Clicking a passive voice alert or a heading node in the outline tree instantly scrolls, focuses, and highlights the target line in the markdown preview.

---

## Technical Stack

* **Backend**: FastAPI (Python), python-docx (Word parsing), pdfplumber (PDF parsing), Pydantic (data validation and contract schemas), and Google Generative AI (optional integration for Gemini 1.5 Flash).
* **Frontend**: HTML5, Vanilla CSS3 (custom layouts and theme variables), and ES6 Javascript.

---

## Setup and Installation

### 1. Prerequisites
Ensure you have Python 3.10 or higher installed.

### 2. Install Dependencies
Install all required Python libraries using pip:
```bash
pip install -r requirements.txt
```

### 3. Configure Gemini API Key (Optional)
DocMigrate implements a dual-mode analysis layer. By default, it uses a local rule-based heuristics engine. To enable advanced AI-powered assessments, set your Gemini API key:

* **Windows (PowerShell)**:
  ```powershell
  $env:GEMINI_API_KEY="your-api-key"
  ```
* **Linux/macOS**:
  ```bash
  export GEMINI_API_KEY="your-api-key"
  ```

---

## Running the Application

### 1. Start the Server
Run the FastAPI development server using uvicorn:
```bash
uvicorn backend.main:app --reload --port 8000
```

### 2. Access the Web Dashboard
Open your browser and navigate to:
```
http://localhost:8000
```
Drag and drop any docx or pdf file into the upload zone to run the analysis.

### 3. Run Backend Verification
Verify the backend parsing, metrics, and quality analysis logic directly:
```bash
python -m backend.test_logic
```

---

## API Response Schema

The POST `/analyze` endpoint returns a structured JSON payload containing the following properties:

```json
{
  "document_metrics": {
    "file_name": "deployment_guide.docx",
    "file_type": ".docx",
    "file_size_kb": 45.2,
    "total_pages": 3,
    "word_count": 850,
    "character_count": 4820,
    "paragraph_count": 22,
    "heading_count": 6,
    "avg_words_per_paragraph": 38.6,
    "has_tables": true,
    "has_images": false,
    "estimated_reading_time_min": 3.8,
    "unique_word_ratio": 0.582,
    "heading_list": [
      "H1: Deployment Guide",
      "H2: Prerequisites",
      "H2: Running the Server",
      "H3: Environment Configuration"
    ]
  },
  "ai_analysis": {
    "readability_level": "Medium",
    "readability_explanation": "Paragraph length is moderate and suitable for technical audiences.",
    "content_clarity_score": 8,
    "content_clarity_explanation": "Vocabulary diversity is high, showing consistent naming conventions.",
    "structural_quality": "Well-organized",
    "structural_quality_explanation": "The headings follow a clear structure with no hierarchy jumps.",
    "migration_readiness": "Clean",
    "migration_readiness_explanation": "Document structure is valid and formatting maps well to target Markdown layout.",
    "suggestions": [
      "Review 'Environment Configuration' on Page 2 for passive phrasing",
      "Verify tables align correctly when rendered in rich-text containers"
    ],
    "overall_score": 8,
    "tone_active_voice_pct": 82,
    "tone_assessment_label": "Good (Moderately Active)",
    "tone_passive_sentences": [
      "The server is started by running the launch command [Page 2]",
      "Configuration variables are loaded from the environment file [Page 2]"
    ]
  },
  "summary": "Document 'deployment_guide.docx' contains 850 words across 22 paragraphs with 6 headings. Score: 8/10.",
  "analysis_method": "Rule-based heuristic analysis",
  "markdown_content": "# Deployment Guide\n\n## Prerequisites..."
}
```
