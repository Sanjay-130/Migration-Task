# 📝 DocMigrate Developer & Interview Cheat Sheet

This document breaks down the codebase flow and key architectural details into simple talking points you can use during your panel interview.

---

## 🏗️ 1. Architecture Flow (How It Works Under the Hood)

Whenever a user drops a file, the application processes it in **6 simple steps**:

```
[Web UI (app.js)] -> [FastAPI (main.py)] -> [Parsers (.docx/.pdf)]
                                                  |
[Markdown Preview] <- [AI / Rule Heuristics] <- [Metrics Engine]
```

1. **Upload**: User drags-and-drops a file onto the UI. `app.js` builds a `FormData` object and POSTs it to `/analyze`.
2. **FastAPI Router**: `/analyze` accepts the file, writes it to a temporary file path, and chooses the correct parser based on file extension (`.docx` vs `.pdf`).
3. **Parsing & Markdown Conversion**:
   - **`docx_parser.py`**: Uses `python-docx` to read structure blocks. During traversal, it automatically converts paragraph styles (like `Heading 1`, `Heading 2`, `Normal`) into standard **Markdown syntax** (adding `#`, `##` prefix tags to text).
   - **`pdf_parser.py`**: Uses `pdfplumber` to extract text page-by-page and applies line heuristics to classify text as a heading or paragraph, converting it into markdown formatting.
4. **Metrics Calculation (`metrics.py`)**: Computes statistics: words, characters, unique word ratio, reading time, and headings.
5. **Quality Analysis (`ai_analyzer.py`)**:
   - Tries to invoke the **Google Gemini API** (`gemini-1.5-flash`) using a JSON format prompt.
   - If no API key exists, it automatically triggers the **Heuristics Rules Engine** to evaluate document structure and assign scores (1 to 10).
6. **Delivery & Live Copy**: FastAPI returns the JSON response (including the converted Markdown text). The UI displays the raw stats, calculates readiness, renders the markdown text in the **Document360 Markdown Exporter** text area, and exposes a one-click **"Copy to Clipboard"** button.

---

## 🧮 2. Key Heuristic Algorithms (The Rules Engine)

If the panel asks: *"How does your rule-based engine decide if a document is ready or needs restructuring without AI?"*

Here are the formulas we wrote in `backend/ai_analyzer.py`:

### A. Readability Level
* **Formula**: Calculated using `avg_words_per_paragraph`.
  - **Easy**: <= 50 words per paragraph (Highly scannable).
  - **Medium**: 51 - 120 words per paragraph (Standard document).
  - **Complex**: > 120 words per paragraph (Too dense; needs to be split).

### B. Structural Quality
* **Formula**: Calculated using the ratio of headings to word count: `heading_count / (word_count / 300)`.
  - **Fragmented**: 0 headings found.
  - **Well-organized**: Heading density is >= 0.8 headings per 300 words.
  - **Moderate**: Has headings, but density is low (< 0.8).

### C. Content Clarity Score
* **Formula**: Calculated using the `unique_word_ratio` (Number of unique words / Total words).
  - **Score 7/10**: Ratio > 0.7 (Rich vocabulary diversity).
  - **Score 6/10**: Ratio 0.4 - 0.7 (Clear, standard text).
  - **Score 4/10**: Ratio < 0.4 (Filler content or repetitive phrases).

### D. Overall Score & Migration Readiness
* Starts with a default score of **`5`**.
* Points are added/subtracted based on the readability, clarity, and headings check.
* **Readiness Decider**:
  - **`Clean`** (Score >= 7 and headings count > 0). Displays as **`Clean / Reusable`** in the UI.
  - **`Needs Review`** (Score 4 - 6).
  - **`Requires Restructuring`** (Score < 4 or 0 headings).

### E. Technical Tone (Active Voice Percentage)
* **Formula**: Splitting document into sentences and tokenizing words.
* Scans if any auxiliary `be` verbs (`is`, `am`, `are`, `was`, `were`, `be`, `been`, `being`) is immediately followed by a past participle ending in `-ed` or a common technical past participle (like `done`, `sent`, `given`, `made`, `run`, `taken`, `written`, `built`, `found`, `read`, `shown`, `set`, `kept`).
* **Active Voice %** = `((Total Sentences - Passive Sentences) / Total Sentences) * 100`.
  - **Excellent (Highly Active)**: >= 85% Active.
  - **Good (Moderately Active)**: 60% - 84% Active.
  - **Review Needed (Too Passive)**: < 60% Active (adds a suggestion to rewrite sentences).

---

## 💡 3. Innovative Exporter Feature (The Markdown Generator)
If the panel asks: *"What makes this tool actually helpful for document migration?"*
> **Answer**: "Document360 works natively with Markdown format. If you upload a standard Word or PDF document directly, formatting is often lost. Our tool parses the Word styles and reconstructs them into clean Markdown elements inside the browser, allowing authors to copy the formatted content with a single click and paste it directly into Document360 without manually redesigning headers."

---

## 💬 4. Perfect Answers to Common Panel Questions

### Q1: "Why did you build the frontend using pure Vanilla CSS instead of a framework like Tailwind or React?"
> **Answer**: "I wanted absolute control over the design layout to produce a highly structured, clean white-and-blue theme with precise sharp corners (zero border-radius). Doing it in Vanilla HTML/CSS/JS keeps the frontend extremely lightweight, load-efficient, and easy to review without compile-time build overhead, while demonstrating that I possess strong fundamental styling and DOM manipulation skills."

### Q2: "How does the PDF parser identify headings since PDFs don't store semantic heading tags?"
> **Answer**: "Unlike Word documents which store formatting metadata, PDFs only store coordinate streams. Our PDF parser analyzes font attributes and text lines. It detects line height, capital letters, numbering, and length to identify section headers."

### Q3: "What makes this tool production-grade?"
> **Answer**: "Three things: 
> 1. **Robust Failover**: It implements graceful degradation. If the Gemini API is offline, the local heuristics rules engine runs instead of crashing the app.
> 2. **Audit Logging**: Every single document processed is automatically logged and exported to a timestamped JSON file inside the `reports/` folder.
> 3. **Input Validation**: It uses Pydantic schemas in Python to enforce strong typing, check file sizes/formats, and reject invalid inputs."

### Q4: "Why did some PDF files extract text with repeated letters like 'PPllaannss' or codes like '(cid:37)'?"
> **Answer**: "This is a common PDF extraction artifact:
> 1. **Double-strike Bold**: Some PDF generators write text twice with a tiny offset to simulate a bold font. We wrote a stateful `_clean_double_strike` algorithm that splits text into words, checks if every adjacent pair of characters is identical (e.g. `P`==`P`, `l`==`l`), and slices the string by half (`word[::2]`) to deduplicate it.
> 2. **Font Ligatures**: Characters like `fi` or `ff` are combined into single glyphs by PDF generators, which extractors read as font CID codes (like `(cid:37)`). We added a text replace-map to restore them back to human-readable strings (e.g., `ef(cid:37)ciently` -> `efficiently`)."

### Q5: "How does your active voice tone calculator work without loading heavy NLP models like SpaCy?"
> **Answer**: "To keep the backend lightweight, fast, and dependency-free, I designed a deterministic regex-based scanner. It splits the document into sentences, tokenizes the words, and identifies grammar structures where an auxiliary 'be' verb is followed by a verb ending in 'ed' or common irregular technical past participles (e.g. 'is configured', 'be sent'). This successfully counts passive phrases and extracts example sentences to display to the user, providing immediate value with near-zero performance overhead."

### Q6: "How does your tool help technical writers easily locate issues in large documents?"
> **Answer**: "To make recommendations actionable, we built location-based diagnostics. The parsers keep track of the page and line numbers (or paragraph numbers for Word) of every block of text they extract in a `ParagraphMetadata` schema. If the heuristics engine finds a problem (like a passive sentence or an overly dense paragraph), it scans this metadata and appends the exact location coordinates—like `[Page 2, Line 14]` or `[Line 8]`—directly next to the recommendation. This allows authors to instantly jump to the exact spot in their source file to make fixes."
