# DocMigrate — Document Analysis & Migration Readiness Tool

DocMigrate is an automation tool designed to analyze Microsoft Word (`.docx`) and PDF (`.pdf`) documents for structure, content-level metrics, and migration readiness to knowledge base platforms like **Document360**.

---

## 🚀 Features

1. **Document Parsing**: Extracts content, headings, tables, and images from `.docx` and `.pdf` files.
2. **Metrics Extraction**: Calculates pages, word count, character count, paragraphs, headings, and average paragraph density.
3. **AI-Driven Assessment**: Evaluates readability, content clarity, structural quality, and migration readiness (Clean / Needs Review / Requires Restructuring).
4. **Resilient AI Layer**: Uses Google Gemini 1.5 Flash for deep language analysis; falls back automatically to a local rule-based heuristics engine if no API key is set.
5. **Interactive Dashboard**: Premium dark-theme web dashboard with live circular SVGs, score indicators, and a downloadable JSON report.

---

## 🛠️ Architecture & Technologies

### Backend (Python + FastAPI)
- **FastAPI**: Modern, async web framework for endpoints.
- **python-docx**: Parsing Word Document XML structures.
- **pdfplumber**: Extracting text blocks and checking formatting layout in PDF files.
- **pydantic**: Class data models and payload schema validation.
- **google-generativeai**: SDK for Gemini 1.5 Flash API.

### Frontend (Vanilla Web Tech)
- **HTML5**: Semantic web content layout.
- **CSS3**: Custom dark glassmorphism system with fluid responsive layouts and keyframe animations.
- **Vanilla ES6 JS**: Interactive file upload drop-zone, API integrations, and score widgets.

---

## 📦 Installation & Setup

### 1. Prerequisites
Ensure you have **Python 3.10+** and `pip` installed.

### 2. Install Dependencies
Run the following command to install the required libraries:
```bash
pip install -r requirements.txt
```

### 3. Configure API Key (Optional)
To enable real AI analysis, get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/) and set it as an environment variable:

**On Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-actual-api-key"
```

**On Linux/macOS:**
```bash
export GEMINI_API_KEY="your-actual-api-key"
```

*Note: If no API key is specified, the tool automatically uses the rule-based heuristics engine, so it remains fully functional.*

---

## 🏃 Running the Application

### 1. Generate Sample Files
Generate test files by running the sample creator:
```bash
python backend/generate_samples.py
```
This creates:
- `samples/sample_structure_good.docx` (Highly structured, H1/H2 styles, tables)
- `samples/sample_structure_poor.docx` (Dense, no heading styles)

### 2. Start the API Server
Start the FastAPI server:
```bash
uvicorn backend.main:app --reload --port 8000
```

### 3. Open the Dashboard
Open your web browser and navigate to:
```
http://localhost:8000
```
Drag and drop your files into the drop-zone to analyze them!

---

## 📊 Sample JSON Output Schema

When a document is uploaded, the backend returns the following structured JSON output:

```json
{
  "document_metrics": {
    "file_name": "sample_structure_good.docx",
    "file_type": ".docx",
    "file_size_kb": 36.4,
    "total_pages": 2,
    "word_count": 520,
    "character_count": 2840,
    "paragraph_count": 14,
    "heading_count": 5,
    "avg_words_per_paragraph": 37.1,
    "has_tables": true,
    "has_images": false,
    "estimated_reading_time_min": 2.3,
    "unique_word_ratio": 0.54,
    "heading_list": [
      "API Integration & Authentication Guide",
      "1. Introduction",
      "2. Authentication Protocol",
      "2.1 Bearer Token Header Example",
      "3. Supported Endpoints"
    ]
  },
  "ai_analysis": {
    "readability_level": "Easy",
    "readability_explanation": "Short paragraphs make this document easy to read and scan.",
    "content_clarity_score": 8,
    "content_clarity_explanation": "Highly consistent terminology and precise information schema.",
    "structural_quality": "Well-organized",
    "structural_quality_explanation": "Contains 5 distinct heading styles forming a logical content outline.",
    "migration_readiness": "Ready - Clean for migration",
    "migration_readiness_explanation": "The document structure is clean and mapped perfectly for Document360 imports.",
    "suggestions": [
      "Ensure table column headers map to target database attributes",
      "Verify all code snippets use standard syntax highlighting styles"
    ],
    "overall_score": 9
  },
  "summary": "Document 'sample_structure_good.docx' (.docx) contains 520 words across 14 paragraphs with 5 headings. Readability: Easy. Structural Quality: Well-organized. Migration Readiness: Ready. Overall Score: 9/10.",
  "analysis_method": "Rule-based heuristic analysis"
}
```
