"""
Utilities for risk analysis and document processing
"""

import os
import re
import json
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
import openai


def build_risk_prompt(clause_text: str, policy_rules: Dict[str, Any] | None = None) -> str:
    """Construct the LLM prompt used for clause risk analysis."""
    if policy_rules:
        try:
            policy_context = json.dumps(policy_rules, indent=2)
        except (TypeError, ValueError):
            policy_context = str(policy_rules)
    else:
        policy_context = "No specific policy rules provided"

    return (
        "Analyze the following contract clause for legal and business risks according to these policy rules.\n"
        "POLICY RULES:\n"
        f"{policy_context}\n\n"
        "CLAUSE TO ANALYZE:\n"
        f"{clause_text}\n\n"
        "Respond in JSON with keys risk_level, rationale, policy_refs."
    )


_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_DIR = os.path.join(_BASE_DIR, "logs")
LOG_FILE_PATH = os.path.join(LOG_DIR, "risk_payloads.log")
_log_lock = threading.Lock()


def _safe_for_logging(value: Any) -> Any:
    """Best-effort JSON serialisation for logging purposes."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _safe_for_logging(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_safe_for_logging(item) for item in value]
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


def _append_risk_log(entry: Dict[str, Any]) -> None:
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        serialised = json.dumps(entry, ensure_ascii=False)
        with _log_lock:
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(serialised + "\n")
    except Exception as logging_error:
        print(f"Failed to write risk payload log: {logging_error}")


def _collect_policy_tokens(value: Any) -> List[str]:
    tokens: List[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            tokens.append(str(key))
            tokens.extend(_collect_policy_tokens(nested))
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            tokens.extend(_collect_policy_tokens(item))
    elif isinstance(value, str):
        tokens.append(value)
    return tokens


def _infer_policy_refs(
    clause_text: str,
    policy_rules: Optional[Dict[str, Any]],
    *,
    risk_level: str,
) -> List[str]:
    if not policy_rules:
        return []

    text_lower = (clause_text or "").lower()
    matched: List[str] = []

    for top_key, config in policy_rules.items():
        candidates = [top_key]
        candidates.extend(_collect_policy_tokens(config))

        for candidate in candidates:
            normalized = str(candidate).replace("_", " ").lower()
            if not normalized or normalized in {"true", "false", "yes", "no"}:
                continue
            tokens = [normalized]
            if " " in normalized:
                tokens.extend(normalized.split())
            if any(token and token in text_lower for token in tokens):
                matched.append(top_key)
                break

    if matched:
        return sorted({key.replace("_", " ") for key in matched})

    if risk_level.strip().upper() != "LOW":
        return [key.replace("_", " ") for key in list(policy_rules.keys())[:3]]

    return []


def _mock_risk_analysis(
    prompt: str,
    clause_text: str,
    policy_rules: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # Simple heuristic for mock risk assessment
    high_risk_keywords = [
        "unlimited",
        "without limitation",
        "sole discretion",
        "indemnify",
        "hold harmless",
    ]
    medium_risk_keywords = [
        "not to exceed",
        "reasonably",
        "mutual",
        "standard",
    ]

    text_lower = (clause_text or "").lower()
    high_risk_count = sum(1 for keyword in high_risk_keywords if keyword in text_lower)
    medium_risk_count = sum(1 for keyword in medium_risk_keywords if keyword in text_lower)

    if high_risk_count > 0:
        risk_level = "High"
        rationale = (
            "Contains high-risk language: "
            + ", ".join([kw for kw in high_risk_keywords if kw in text_lower][:2])
        )
    elif medium_risk_count > 0:
        risk_level = "Medium"
        rationale = (
            "Contains medium-risk language: "
            + ", ".join([kw for kw in medium_risk_keywords if kw in text_lower][:2])
        )
    else:
        risk_level = "Low"
        rationale = "Standard legal language with no obvious risk indicators"

    policy_refs = _infer_policy_refs(clause_text, policy_rules, risk_level=risk_level)

    return {
        "risk_level": risk_level,
        "rationale": rationale,
        "policy_refs": policy_refs,
        "prompt": prompt,
    }


def analyze_risk_with_openai(
    clause_text: str,
    policy_rules: Dict[str, Any] | None = None,
    *,
    prompt_override: Optional[str] = None,
    log_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Analyze risk level of a clause using OpenAI or mock analysis
    """
    prompt = prompt_override or build_risk_prompt(clause_text, policy_rules)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": _safe_for_logging(log_metadata or {}),
        "prompt": prompt,
        "prompt_override_used": prompt_override is not None,
        "prompt_length": len(prompt or ""),
        "clause_text": clause_text,
        "clause_length": len(clause_text or ""),
        "policy_rules": _safe_for_logging(policy_rules or {}),
    }
    _append_risk_log(log_entry)

    # Determine whether OpenAI-backed analysis is enabled
    api_key = os.getenv("OPENAI_API_KEY")
    openai_flag = os.getenv("ENABLE_OPENAI_ANALYSIS", "").strip().lower()
    openai_enabled = bool(api_key) and openai_flag in {"1", "true", "yes", "on"}

    if not openai_enabled:
        if api_key and openai_flag not in {"1", "true", "yes", "on"}:
            print(
                "Using mock risk analysis (ENABLE_OPENAI_ANALYSIS not set to true)"
            )
        else:
            print("Using mock risk analysis (no OpenAI API key)")
        return _mock_risk_analysis(prompt, clause_text, policy_rules)

    # Real OpenAI analysis
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content.strip())

        risk_level = result.get("risk_level", "Medium")
        rationale = result.get("rationale", "AI analysis completed")
        policy_refs = result.get("policy_refs")
        if not isinstance(policy_refs, list) or not policy_refs:
            policy_refs = _infer_policy_refs(clause_text, policy_rules, risk_level=risk_level)

        return {
            "risk_level": risk_level,
            "rationale": rationale,
            "policy_refs": policy_refs,
            "prompt": prompt,
        }
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return _mock_risk_analysis(prompt, clause_text, policy_rules)


def resolve_clause_texts(
    clauses: List[Dict[str, Any]],
    document_text: Optional[str] = None,
) -> Dict[str, str]:
    """Return normalized clause texts suitable for risk prompts.

    Prefer clause bodies when available, fall back to original clause text, and
    guard against accidentally passing the entire document into clause-level
    analysis.
    """

    resolved: Dict[str, str] = {}
    doc_text = (document_text or "").strip()
    doc_len = len(doc_text)
    doc_lines: Optional[List[str]] = doc_text.splitlines() if doc_text else None

    for index, clause in enumerate(clauses):
        clause_id = (
            clause.get("clause_id")
            or clause.get("id")
            or f"clause_{index + 1}"
        )

        heading = (clause.get("heading") or "").strip()
        body = (clause.get("body") or "").strip()
        text = (clause.get("text") or "").strip()
        level = clause.get("level")
        start_line = clause.get("start_line")

        normalized = ""

        if doc_lines is not None and isinstance(start_line, int) and start_line > 0:
            start_index = min(max(start_line - 1, 0), len(doc_lines))
            end_index = len(doc_lines)
            for follower in clauses[index + 1 :]:
                follower_start = follower.get("start_line")
                if not isinstance(follower_start, int) or follower_start <= start_line:
                    continue
                follower_level = follower.get("level")
                if level is None or follower_level is None or follower_level <= level:
                    end_index = max(follower_start - 1, start_index)
                    break
                end_index = max(follower_start - 1, start_index)
                break

            snippet_lines = doc_lines[start_index:end_index]
            normalized = "\n".join(line.rstrip() for line in snippet_lines).strip()

        if not normalized:
            normalized = body or text

        normalized = (normalized or "").strip()

        if heading:
            if normalized:
                if not normalized.startswith(heading):
                    normalized = f"{heading}\n{normalized}"
            else:
                normalized = heading

        if doc_len and normalized and len(normalized) >= doc_len * 0.9:
            body_only = body.strip() if body else ""
            if body_only and len(body_only) < len(normalized):
                normalized = body_only
                if heading and not normalized.startswith(heading):
                    normalized = f"{heading}\n{normalized}"
            elif text and text != normalized and len(text) < len(normalized):
                normalized = text
            if doc_len and normalized and len(normalized) >= doc_len * 0.9:
                normalized = normalized[: min(len(normalized), 4000)].strip()

        resolved[clause_id] = normalized

    return resolved


def parse_document_content(content: str, filename: str) -> Dict[str, Any]:
    """Parse document content into structured clauses with hierarchy awareness."""

    lines = content.splitlines()
    clauses: List[Dict[str, Any]] = []
    heading_stack: List[Dict[str, Any]] = []
    preface_lines: List[str] = []
    used_ids: Set[str] = set()
    clause_counter = 1

    heading_patterns: List[Tuple[str, re.Pattern]] = [
        (
            "section_numeric",
            re.compile(
                r"^(?P<prefix>(?:Section|Article|Clause)\s+)?(?P<number>\d+(?:\.\d+)*)(?P<suffix>[\.\)])?\s*(?P<title>.*)$",
                re.IGNORECASE,
            ),
        ),
        (
            "numeric_decimal",
            re.compile(r"^(?P<number>\d+(?:\.\d+)+)(?P<suffix>[\.\)])?\s*(?P<title>.*)$"),
        ),
        (
            "numeric",
            re.compile(r"^(?P<number>\d+)(?P<suffix>[\.\)])?\s*(?P<title>.*)$"),
        ),
        (
            "upper_alpha",
            re.compile(r"^(?P<number>[A-Z])(?P<suffix>[\.\)])\s*(?P<title>.*)$"),
        ),
        (
            "lower_alpha",
            re.compile(r"^(?P<number>[a-z])(?P<suffix>[\.\)])\s*(?P<title>.*)$"),
        ),
        (
            "paren_upper",
            re.compile(r"^\((?P<number>[A-Z]+)\)\s*(?P<title>.*)$"),
        ),
        (
            "paren_lower",
            re.compile(r"^\((?P<number>[a-z]+)\)\s*(?P<title>.*)$"),
        ),
        (
            "roman",
            re.compile(r"^(?P<number>[ivxlcdm]+)(?P<suffix>[\.\)])\s*(?P<title>.*)$", re.IGNORECASE),
        ),
        (
            "paren_roman",
            re.compile(r"^\((?P<number>[ivxlcdm]+)\)\s*(?P<title>.*)$", re.IGNORECASE),
        ),
    ]

    def tokenize_numbering(raw: Optional[str]) -> List[str]:
        if not raw:
            return []
        cleaned = raw.strip()
        cleaned = cleaned.replace("(", "").replace(")", "")
        tokens = re.split(r"[\.\-]", cleaned)
        tokens = [t for t in tokens if t]
        return tokens

    def infer_level(pattern_name: str, tokens: List[str]) -> int:
        if pattern_name in {"section_numeric", "numeric_decimal"}:
            return max(1, len(tokens))
        if pattern_name == "numeric":
            return max(1, len(tokens))
        if not heading_stack:
            return 1

        parent = heading_stack[-1]

        if pattern_name in {"paren_lower", "paren_upper", "paren_roman", "lower_alpha"}:
            return parent["level"] + 1

        if pattern_name == "upper_alpha":
            if parent["pattern"] == "upper_alpha" and parent["level"] == 1:
                return 1
            if parent["pattern"] in {"numeric", "numeric_decimal", "section_numeric"}:
                return parent["level"] + 1
            return max(1, parent["level"])

        if pattern_name == "roman":
            if parent["pattern"] in {"upper_alpha", "numeric", "numeric_decimal", "section_numeric"}:
                return parent["level"] + 1
            if parent["pattern"] == "roman":
                return parent["level"]
            return 1

        if pattern_name == "paren_roman":
            return parent["level"] + 1

        return parent["level"]

    def close_levels(target_level: int) -> None:
        while heading_stack and heading_stack[-1]["level"] >= target_level:
            entry = heading_stack.pop()
            clause = entry["clause"]
            body = "\n".join(entry["lines"]).strip()
            clause["body"] = body
            clause["text"] = (f"{clause['heading']}\n{body}" if body else clause["heading"]).strip()
            clause.pop("_lines", None)

    def generate_clause_id(base: Optional[str]) -> str:
        nonlocal clause_counter
        cleaned = (base or f"clause_{clause_counter}").strip()
        cleaned = re.sub(r"[^0-9A-Za-z]+", "_", cleaned)
        cleaned = cleaned.strip("_") or f"clause_{clause_counter}"
        candidate = cleaned.lower()
        if candidate in used_ids:
            suffix = 2
            while f"{candidate}_{suffix}" in used_ids:
                suffix += 1
            candidate = f"{candidate}_{suffix}"
        used_ids.add(candidate)
        clause_counter += 1
        return candidate

    def match_heading(line: str) -> Optional[Dict[str, Any]]:
        stripped = line.strip()
        # Allow titles that follow a colon after numbering (e.g., "1 Confidentiality" or "1: Confidentiality")
        normalized = re.sub(r"\s{2,}", " ", stripped)

        for pattern_name, regex in heading_patterns:
            match = regex.match(normalized)
            if not match:
                continue

            number = match.groupdict().get("number")
            title = (match.groupdict().get("title") or "").strip()
            tokens = tokenize_numbering(number)
            level = infer_level(pattern_name, tokens)

            return {
                "raw": stripped,
                "number": number,
                "title": title,
                "tokens": tokens,
                "level": level,
                "pattern": pattern_name,
            }

        # Handle cases like "1 Confidentiality" without punctuation
        bare_numeric = re.match(r"^(?P<number>\d+(?:\.\d+)*)\s+[-:]?\s*(?P<title>.+)$", normalized)
        if bare_numeric:
            number = bare_numeric.group("number")
            title = bare_numeric.group("title").strip()
            tokens = tokenize_numbering(number)
            level = infer_level("section_numeric", tokens)
            return {
                "raw": stripped,
                "number": number,
                "title": title,
                "tokens": tokens,
                "level": level,
                "pattern": "section_numeric",
            }

        return None

    for index, raw_line in enumerate(lines):
        stripped_line = raw_line.strip()
        if not stripped_line:
            if heading_stack:
                heading_stack[-1]["lines"].append("")
            else:
                preface_lines.append("")
            continue

        heading_info = match_heading(stripped_line)

        if heading_info:
            close_levels(heading_info["level"])

            parent_entry: Optional[Dict[str, Any]] = None
            for entry in reversed(heading_stack):
                if entry["level"] < heading_info["level"]:
                    parent_entry = entry
                    break

            parent_clause = parent_entry["clause"] if parent_entry else None
            parent_path = parent_clause.get("section_path", []) if parent_clause else []

            candidate_id = heading_info["number"] or heading_info["title"] or f"clause_{clause_counter}"
            clause_id = generate_clause_id(candidate_id)

            section_key = heading_info["number"] or heading_info["title"] or clause_id

            clause_data = {
                "id": clause_id,
                "clause_id": clause_id,
                "heading": heading_info["raw"],
                "title": heading_info["title"],
                "numbering": heading_info["number"],
                "level": heading_info["level"],
                "parent_id": parent_clause.get("clause_id") if parent_clause else None,
                "section_path": parent_path + [section_key],
                "start_line": index + 1,
                "children": [],
                "_lines": [],
            }

            if parent_clause is not None:
                parent_clause.setdefault("children", []).append(clause_id)

            entry = {
                "clause": clause_data,
                "level": heading_info["level"],
                "pattern": heading_info["pattern"],
                "tokens": heading_info["tokens"],
                "lines": clause_data["_lines"],
            }

            clauses.append(clause_data)
            heading_stack.append(entry)
        else:
            target_entry = heading_stack[-1] if heading_stack else None
            if target_entry:
                target_entry["lines"].append(stripped_line)
            else:
                preface_lines.append(stripped_line)

    close_levels(0)

    preface_text = "\n".join(preface_lines).strip()
    if preface_text:
        preface_id = generate_clause_id("preface")
        preface_clause = {
            "id": preface_id,
            "clause_id": preface_id,
            "heading": f"Preface ({filename})",
            "title": "Preface",
            "numbering": None,
            "level": 0,
            "parent_id": None,
            "section_path": ["preface"],
            "start_line": 1,
            "children": [],
            "body": preface_text.strip(),
        }
        preface_clause["text"] = preface_clause["body"]
        clauses.insert(0, preface_clause)

    if not clauses:
        default_text = content[:500] + "..." if len(content) > 500 else content
        return {
            "name": filename,
            "content": content,
            "clauses": [
                {
                    "id": "clause_1",
                    "clause_id": "clause_1",
                    "heading": f"Document: {filename}",
                    "title": filename,
                    "numbering": None,
                    "level": 1,
                    "parent_id": None,
                    "section_path": [filename],
                    "start_line": 1,
                    "children": [],
                    "body": default_text,
                    "text": default_text,
                }
            ],
        }

    for clause in clauses:
        if "text" not in clause:
            body = clause.get("body", "")
            clause["text"] = (f"{clause['heading']}\n{body}" if body else clause["heading"]).strip()

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