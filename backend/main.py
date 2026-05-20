
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import tempfile
import os
import json
from datetime import datetime

from backend.parsers.docx_parser import parse_docx
from backend.parsers.pdf_parser import parse_pdf
from backend.metrics import extract_metrics
from backend.ai_analyzer import analyze_document
from backend.models import AnalysisReport

# Initialize FastAPI app
app = FastAPI(
    title="Document Analysis & Migration Readiness Tool",
    description="Analyze .docx and .pdf documents for migration readiness to Document360",
    version="1.0.0",
)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def root():
    """Serve the frontend dashboard."""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Document Analysis & Migration Readiness Tool API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.post("/analyze")
async def analyze_files(files: list[UploadFile] = File(...)):
    """
    Upload and analyze multiple documents.
    
    Accepts .docx and .pdf files.
    Returns an array of comprehensive analysis reports with metrics and AI insights.
    """
    reports = []
    
    for file in files:
        file_name = file.filename or "unknown"
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if file_ext not in [".docx", ".pdf"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type in batch: {file_ext} for file '{file_name}'. Please upload only .docx or .pdf files."
            )
        
        # Save uploaded file to a temporary location
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")
        
        try:
            # Step 1: Parse the document
            if file_ext == ".docx":
                parsed_doc = parse_docx(tmp_path)
            else:
                parsed_doc = parse_pdf(tmp_path)
            
            # Override file name with original name
            parsed_doc.file_name = file_name
            
            # Step 2: Extract metrics
            metrics = extract_metrics(parsed_doc)
            
            # Step 3: AI analysis
            ai_analysis, method = analyze_document(parsed_doc, metrics)
            
            # Step 4: Generate summary
            summary = _generate_summary(metrics, ai_analysis)
            
            # Step 5: Build report
            report = AnalysisReport(
                document_metrics=metrics,
                ai_analysis=ai_analysis,
                summary=summary,
                analysis_method=method,
                markdown_content=parsed_doc.markdown_content,
            )
            
            # Step 6: Save report as JSON
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            report_filename = f"report_{file_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = os.path.join(reports_dir, report_filename)
            
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)
            
            reports.append(report.model_dump())
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed for file '{file_name}': {str(e)}")
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    return reports
def _generate_summary(metrics, ai_analysis) -> str:
    """Generate a human-readable summary of the analysis."""
    return (
        f"Document '{metrics.file_name}' ({metrics.file_type}) contains {metrics.word_count} words "
        f"across {metrics.paragraph_count} paragraphs with {metrics.heading_count} headings. "
        f"Readability: {ai_analysis.readability_level}. "
        f"Structural Quality: {ai_analysis.structural_quality}. "
        f"Migration Readiness: {ai_analysis.migration_readiness}. "
        f"Overall Score: {ai_analysis.overall_score}/10."
    )
