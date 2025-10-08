"""
Utilities for risk analysis and document processing
"""

import os
import re
from typing import Dict, Any
import openai


def analyze_risk_with_openai(clause_text: str, policy_rules: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Analyze risk level of a clause using OpenAI or mock analysis
    """
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Return mock analysis if OpenAI client not available
        print("Using mock risk analysis (no OpenAI API key)")
        # Simple heuristic for mock risk assessment
        high_risk_keywords = ["unlimited", "without limitation", "sole discretion", "indemnify", "hold harmless"]
        medium_risk_keywords = ["not to exceed", "reasonably", "mutual", "standard"]
        
        text_lower = clause_text.lower()
        high_risk_count = sum(1 for keyword in high_risk_keywords if keyword in text_lower)
        medium_risk_count = sum(1 for keyword in medium_risk_keywords if keyword in text_lower)
        
        if high_risk_count > 0:
            risk_level = "High"
            rationale = f"Contains high-risk language: {', '.join([kw for kw in high_risk_keywords if kw in text_lower][:2])}"
        elif medium_risk_count > 0:
            risk_level = "Medium"
            rationale = f"Contains medium-risk language: {', '.join([kw for kw in medium_risk_keywords if kw in text_lower][:2])}"
        else:
            risk_level = "Low"
            rationale = "Standard legal language with no obvious risk indicators"
        
        return {
            "risk_level": risk_level,
            "rationale": rationale,
            "policy_refs": []
        }
    
    # Real OpenAI analysis
    policy_context = str(policy_rules) if policy_rules else "No specific policy rules provided"
    
    prompt = f"""
    Analyze the following contract clause for legal and business risks according to these policy rules:
    
    POLICY RULES:
    {policy_context}
    
    CLAUSE TO ANALYZE:
    {clause_text}
    
    Please analyze and provide:
    1. Risk level: "High", "Medium", or "Low"
    2. Rationale for the risk assessment
    3. Specific policy rule references that apply
    
    Respond in JSON format with keys: "risk_level", "rationale", "policy_refs"
    """
    
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content.strip())
        
        return {
            "risk_level": result.get("risk_level", "Medium"),
            "rationale": result.get("rationale", "AI analysis completed"),
            "policy_refs": result.get("policy_refs", [])
        }
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        # Fallback to simple analysis
        return {
            "risk_level": "Medium", 
            "rationale": f"AI analysis failed: {str(e)}, defaulting to medium risk",
            "policy_refs": []
        }


def parse_document_content(content: str, filename: str) -> Dict[str, Any]:
    """
    Parse document content into structured clauses.
    """
    lines = content.split('\n')
    clauses = []
    clause_counter = 1
    
    # A simple heuristic to identify clauses based on numbering patterns
    clause_patterns = [
        r'^\d+[\.\)]',      # Matches "1.", "2)", etc.
        r'^\d+\.\d+',      # Matches "1.1", "2.3", etc.
        r'^[IVX]+[\.\)]',   # Roman numerals
        r'^[A-Z]\d*[\.\)]'  # Capital letters
    ]
    
    import re
    current_clause_text = ""
    current_heading = ""
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if this line looks like a clause heading
        is_clause_start = any(re.match(pattern, line, re.IGNORECASE) for pattern in clause_patterns)
        
        if is_clause_start:
            # If we were building a previous clause, save it
            if current_clause_text and current_heading:
                clauses.append({
                    "id": f"clause_{clause_counter - 1}",
                    "heading": current_heading,
                    "text": current_clause_text.strip(),
                    "start_line": 0  # Could track actual line number if needed
                })
            
            # Start a new clause
            current_heading = line
            current_clause_text = line + "\n"
            clause_counter += 1
        else:
            # If not a heading, add to current clause if one exists
            if current_heading:
                current_clause_text += line + "\n"
            # If no current heading, this could be a continuation of text before first heading
            # For now, let's not treat it as a clause until we find a proper heading
    
    # Don't forget the last clause
    if current_clause_text and current_heading:
        clauses.append({
            "id": f"clause_{clause_counter - 1}",
            "heading": current_heading,
            "text": current_clause_text.strip(),
            "start_line": 0
        })
    
    # If no clauses were found, create a single clause with the entire content
    if not clauses:
        clauses = [{
            "id": "clause_1",
            "heading": f"Document: {filename}",
            "text": content[:500] + "..." if len(content) > 500 else content,
            "start_line": 0
        }]
    
    return {"name": filename, "content": content, "clauses": clauses}


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file content"""
    import PyPDF2
    from io import BytesIO
    
    pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file content"""
    from docx import Document
    from io import BytesIO
    
    doc = Document(BytesIO(file_content))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text