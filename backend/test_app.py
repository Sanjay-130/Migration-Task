"""
FastAPI Integration Tests

=== INTERVIEW EXPLANATION ===
We use FastAPI's built-in TestClient to test our API endpoints.
This allows us to test the backend logic (parsing, metrics, rule validation)
without having to run a live web server process.

Running this script verifies that all components are integrated and working correctly.
"""

from fastapi.testclient import TestClient
from backend.main import app
import os


def test_analyze_endpoint():
    client = TestClient(app)
    
    # Verify health endpoint
    print("Testing GET /health...")
    response = client.get("/health")
    assert response.status_code == 200
    print(f"Health check passed: {response.json()}\n")
    
    # Path to sample files
    good_sample_path = os.path.join("samples", "sample_structure_good.docx")
    poor_sample_path = os.path.join("samples", "sample_structure_poor.docx")
    
    # Verify parsing good sample
    print(f"Testing POST /analyze with {good_sample_path}...")
    if os.path.exists(good_sample_path):
        with open(good_sample_path, "rb") as f:
            response = client.post("/analyze", files={"file": f})
        
        assert response.status_code == 200
        data = response.json()
        print("Good sample parsed successfully!")
        print(f"File: {data['document_metrics']['file_name']}")
        print(f"Word count: {data['document_metrics']['word_count']}")
        print(f"Headings found: {len(data['document_metrics']['heading_list'])}")
        print(f"Migration Readiness: {data['ai_analysis']['migration_readiness']}")
        print(f"Overall Quality Score: {data['ai_analysis']['overall_score']}/10\n")
    else:
        print("Good sample file not found. Make sure to run generate_samples.py first.")
        
    # Verify parsing poor sample
    print(f"Testing POST /analyze with {poor_sample_path}...")
    if os.path.exists(poor_sample_path):
        with open(poor_sample_path, "rb") as f:
            response = client.post("/analyze", files={"file": f})
            
        assert response.status_code == 200
        data = response.json()
        print("Poor sample parsed successfully!")
        print(f"File: {data['document_metrics']['file_name']}")
        print(f"Word count: {data['document_metrics']['word_count']}")
        print(f"Headings found: {len(data['document_metrics']['heading_list'])}")
        print(f"Migration Readiness: {data['ai_analysis']['migration_readiness']}")
        print(f"Overall Quality Score: {data['ai_analysis']['overall_score']}/10\n")
        print("AI Suggestions:")
        for sug in data['ai_analysis']['suggestions']:
            print(f" - {sug}")
    else:
        print("Poor sample file not found.")


if __name__ == "__main__":
    test_analyze_endpoint()
