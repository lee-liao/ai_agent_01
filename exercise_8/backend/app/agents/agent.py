"""
Agent Base Class

An Agent represents an individual worker with specific capabilities.
Each agent can:
- Execute tasks independently
- Read from and write to the shared Blackboard
- Report its status and results
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    WAITING = "waiting"


class AgentResult(BaseModel):
    """Result of agent execution"""
    agent_name: str
    status: AgentStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


class Agent:
    """
    Base Agent class for multi-agent orchestration.
    
    Students should inherit from this class to create specialized agents:
    - ParserAgent: Extracts clauses from documents
    - RiskAnalyzerAgent: Assesses risk levels
    - RedlineGeneratorAgent: Creates redline proposals
    - ReviewerAgent: Validates against checklists
    - RefereeAgent: Arbitrates contested decisions
    
    Example:
        class ParserAgent(Agent):
            def __init__(self):
                super().__init__(
                    name="parser",
                    role="document_parser",
                    capabilities=["parse_clauses", "extract_headings"]
                )
            
            def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
                # Parse document into clauses
                doc_text = task.get("document_text")
                clauses = self._parse_clauses(doc_text)
                
                # Write to blackboard
                blackboard["clauses"] = clauses
                
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.SUCCESS,
                    output={"clause_count": len(clauses)}
                )
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        capabilities: List[str],
        description: Optional[str] = None
    ):
        """
        Initialize an Agent.
        
        Args:
            name: Unique identifier for this agent
            role: The agent's role (e.g., "parser", "risk_analyzer")
            capabilities: List of capabilities this agent has
            description: Optional description of what this agent does
        """
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.description = description or f"Agent: {name}"
        self.status = AgentStatus.IDLE
    
    def can_handle(self, task_type: str) -> bool:
        """
        Check if this agent can handle a specific task type.
        
        Args:
            task_type: The type of task to check
            
        Returns:
            True if this agent has the capability to handle this task
        """
        return task_type in self.capabilities
    
    def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
        """
        Execute a task. This method should be overridden by subclasses.
        
        Args:
            task: Task specification with parameters
            blackboard: Shared state/memory accessible to all agents
            
        Returns:
            AgentResult with execution status and output
            
        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError(
            f"Agent {self.name} must implement the execute() method"
        )
    
    def validate_task(self, task: Dict[str, Any]) -> bool:
        """
        Validate that a task has all required parameters.
        Override this method to add custom validation.
        
        Args:
            task: Task specification to validate
            
        Returns:
            True if task is valid, False otherwise
        """
        return "type" in task
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get agent information for debugging/monitoring.
        
        Returns:
            Dictionary with agent metadata
        """
        return {
            "name": self.name,
            "role": self.role,
            "capabilities": self.capabilities,
            "description": self.description,
            "status": self.status.value
        }


# Example Agent Implementations (Students should complete these)

class ParserAgent(Agent):
    """
    Parses legal documents into structured clauses.
    
    TODO for students:
    - Implement clause extraction logic
    - Handle different document formats (PDF, DOCX, MD)
    - Extract clause headings and IDs
    """
    
    def __init__(self):
        super().__init__(
            name="parser",
            role="document_parser",
            capabilities=["parse_clauses", "extract_headings"],
            description="Extracts clauses from legal documents"
        )
    
    def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
        """
        Parse document into clauses.
        
        Expected task format:
        {
            "type": "parse_clauses",
            "document_text": "...",
            "document_id": "doc_001"
        }
        """
        self.status = AgentStatus.RUNNING
        
        try:
            # Get document text from task or from blackboard if not in task
            doc_text = task.get("document_text")
            if not doc_text:
                doc_text = blackboard.get("document_text", "")
            
            if not doc_text:
                raise ValueError("No document text provided to parse")
            
            # Improved parsing logic with better clause identification
            clauses = self._parse_clauses_advanced(doc_text)
            
            # Write to blackboard
            blackboard["clauses"] = clauses
            blackboard["document_id"] = task.get("document_id") or blackboard.get("doc_id")
            
            # Record execution in history
            if "history" not in blackboard:
                blackboard["history"] = []
            blackboard["history"].append({
                "step": "parsing_complete",
                "agent": self.name,
                "status": "success",
                "timestamp": task.get("timestamp", "unknown"),
                "output": {"clause_count": len(clauses)}
            })
            
            self.status = AgentStatus.SUCCESS
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output={"clause_count": len(clauses)}
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            # Record error in history
            if "history" not in blackboard:
                blackboard["history"] = []
            blackboard["history"].append({
                "step": "parsing_failed",
                "agent": self.name,
                "status": "error",
                "timestamp": task.get("timestamp", "unknown"),
                "error": str(e)
            })
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e)
            )
    
    def _parse_clauses_advanced(self, text: str) -> List[Dict[str, Any]]:
        """
        Advanced clause parsing using pattern recognition
        """
        import re
        
        # Pattern to identify clause headings (numbered sections, Roman numerals, etc.)
        clause_patterns = [
            r'^(\\d+[\\.]?\\s+.*?)[\\r\\n]+((?:(?!\\d+[\\.]?\\s).*\\n?)*)',  # Matches "1. Heading" followed by content
            r'^([IVX]+[\\.]?\\s+.*?)[\\r\\n]+((?:(?![IVX]+[\\.]?\\s).*\\n?)*)',  # Roman numerals
            r'^([A-Z]\\d*[\\.]?\\s+.*?)[\\r\\n]+((?:(?![A-Z]\\d*[\\.]?\\s).*\\n?)*)',  # Letters
            r'^([A-Z][a-z]+\\s.*?)[\\r\\n]+((?:(?![A-Z][a-z]+\\s).*\\n?)*)',  # Word headings
        ]
        
        clauses = []
        clause_counter = 1
        lines = text.split('\\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Check if this line looks like a clause heading
            is_clause_heading = any(
                re.match(pattern.split('[')[0].rstrip() + r'\\s', line, re.IGNORECASE)
                for pattern in [r'^\\d+[\\.]?\\s', r'^[IVX]+[\\.]?\\s', r'^[A-Z]\\d*[\\.]?\\s', r'^[A-Z][a-z]+\\s']
            )
            
            if is_clause_heading:
                heading = line
                clause_text = line + "\\n"
                
                # Collect the rest of the clause content
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if not next_line:
                        clause_text += "\\n"
                        i += 1
                        continue
                    
                    # Check if next line is a new clause heading
                    is_next_clause = any(
                        re.match(pattern.split('[')[0].rstrip() + r'\\s', next_line, re.IGNORECASE)
                        for pattern in [r'^\\d+[\\.]?\\s', r'^[IVX]+[\\.]?\\s', r'^[A-Z]\\d*[\\.]?\\s', r'^[A-Z][a-z]+\\s']
                    )
                    
                    if is_next_clause:
                        break
                    else:
                        clause_text += next_line + "\\n"
                        i += 1
                
                clauses.append({
                    "clause_id": f"clause_{clause_counter}",
                    "heading": heading.strip(),
                    "text": clause_text.strip()
                })
                clause_counter += 1
            else:
                i += 1
        
        # If no clauses were found using advanced method, fall back to simple splitting
        if not clauses:
            # Try a different approach - split on common headings
            sections = re.split(r'\\n\\s*\\n', text)
            clauses = []
            clause_counter = 1
            for section in sections:
                section = section.strip()
                if section:
                    # Try to extract heading (first line if it looks like a heading)
                    lines = section.split('\\n', 1)
                    if len(lines) > 0:
                        heading = lines[0].strip() if len(lines[0].split()) <= 10 else f"Section {clause_counter}"  # If first line is very long, it's probably not a heading
                        content = section if len(lines) == 1 else f"{lines[0].strip()}\\n{lines[1].strip() if len(lines) > 1 else ''}"
                        clauses.append({
                            "clause_id": f"clause_{clause_counter}",
                            "heading": heading,
                            "text": content
                        })
                        clause_counter += 1
        
        return clauses


class RiskAnalyzerAgent(Agent):
    """
    Analyzes clauses for legal/business risks.
    
    TODO for students:
    - Implement risk assessment logic
    - Compare clauses against policy rules
    - Assign risk levels (HIGH/MEDIUM/LOW)
    - Generate rationale for each assessment
    """
    
    def __init__(self):
        super().__init__(
            name="risk_analyzer",
            role="risk_assessor",
            capabilities=["assess_risk", "policy_check"],
            description="Assesses legal and business risks in contract clauses"
        )
    
    def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
        """
        Assess risk levels for clauses.
        
        Expected task format:
        {
            "type": "assess_risk",
            "policy_rules": {...}
        }
        """
        self.status = AgentStatus.RUNNING
        
        try:
            clauses = blackboard.get("clauses", [])
            policy_rules = task.get("policy_rules", {})
            
            assessments = []
            for clause in clauses:
                # Perform comprehensive risk assessment
                assessment = self._assess_clause_risk_detailed(clause, policy_rules)
                assessments.append(assessment)
            
            # Write to blackboard
            blackboard["assessments"] = assessments
            
            # Record execution in history
            if "history" not in blackboard:
                blackboard["history"] = []
            blackboard["history"].append({
                "step": "risk_assessment_complete",
                "agent": self.name,
                "status": "success",
                "timestamp": task.get("timestamp", "unknown"),
                "output": {"assessment_count": len(assessments)}
            })
            
            self.status = AgentStatus.SUCCESS
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output={"assessment_count": len(assessments)}
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            # Record error in history
            if "history" not in blackboard:
                blackboard["history"] = []
            blackboard["history"].append({
                "step": "risk_assessment_failed",
                "agent": self.name,
                "status": "error",
                "timestamp": task.get("timestamp", "unknown"),
                "error": str(e)
            })
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e)
            )
    
    def _assess_clause_risk_detailed(self, clause: Dict[str, Any], policy_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform detailed risk assessment on a single clause with rationale and policy references
        """
        import re
        
        text = clause.get("text", "").lower()
        heading = clause.get("heading", "").lower()
        
        # Define risk indicators with severity levels
        risk_indicators = {
            "HIGH": [
                r"unlimited\s+(liability|damages|exposure|penalty)",
                r"all\s+damages",
                r"without\s+limitation",
                r"sole\s+discretion",
                r"indemnify\s+hold\s+harmless",
                r"not\s+liable\s+for",
                r"exceed\s+contract\s+value",
                r"no\s+cap",
                r"unlimited\s+access",
                r"irrevocable",
                r"perpetual",
                r"without\s+recourse",
                r"absolute\s+obligation",
                r"waive\s+rights",
                r"exclusive\s+jurisdiction"
            ],
            "MEDIUM": [
                r"indemnify",
                r"warranty",
                r"confidentiality\s+period",
                r"terminate\s+with.*notice",
                r"non-compete",
                r"audit.*rights",
                r"data.*retention",
                r"subprocessor",
                r"assignment.*without",
                r"exclusivity",
                r"minimum.*commitment",
                r"volume.*requirements",
                r"auto.*renew",
                r"change.*fees",
                r"service\s+level"
            ],
            "LOW": [
                r"standard.*terms",
                r"mutual",
                r"reasonable.*efforts",
                r"industry.*standard",
                r"best.*efforts",
                r"net.*90",
                r"payment.*terms",
                r"force\s+majeure"
            ]
        }
        
        # Check for policy rule violations
        policy_refs = []
        policy_violations = []
        
        # Check policy rules against the clause
        for rule_name, rule_value in policy_rules.items():
            if isinstance(rule_value, str):
                if rule_value.lower() in text or rule_value.lower() in heading:
                    policy_refs.append(rule_name)
                    policy_violations.append(f"Policy rule '{rule_name}' ({rule_value}) identified in clause")
        
        # Assess risk based on indicators in the text
        risk_level = "LOW"  # Default to low risk
        risk_reasons = []
        
        # Check for high risk indicators
        for indicator in risk_indicators["HIGH"]:
            if re.search(indicator, text, re.IGNORECASE):
                risk_level = "HIGH"
                risk_reasons.append(f"High risk pattern found: {indicator}")
        
        # If not high risk, check medium risk indicators
        if risk_level == "LOW":
            for indicator in risk_indicators["MEDIUM"]:
                if re.search(indicator, text, re.IGNORECASE):
                    risk_level = "MEDIUM"
                    risk_reasons.append(f"Medium risk pattern found: {indicator}")
        
        # Compile rationale
        rationale_parts = []
        if risk_reasons:
            rationale_parts.append("Risk patterns identified: " + "; ".join(risk_reasons))
        if policy_violations:
            rationale_parts.append("Policy violations: " + "; ".join(policy_violations))
        if not rationale_parts:
            rationale_parts.append("Standard clause with no identified risks")
        
        rationale = " | ".join(rationale_parts)
        
        return {
            "clause_id": clause["clause_id"],
            "risk_level": risk_level,
            "rationale": rationale,
            "policy_refs": policy_refs
        }


class RedlineGeneratorAgent(Agent):
    """
    Generates redline proposals for risky clauses.
    
    TODO for students:
    - Implement redline generation logic
    - Create before/after text versions
    - Generate rationale for each change
    - Reference applicable policies
    """
    
    def __init__(self):
        super().__init__(
            name="redline_generator",
            role="redline_creator",
            capabilities=["generate_redlines", "create_proposals"],
            description="Creates redline proposals for contract improvements"
        )
    
    def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
        """
        Generate redline proposals.
        
        Expected task format:
        {
            "type": "generate_redlines",
            "policy_rules": {...}
        }
        """
        self.status = AgentStatus.RUNNING
        
        try:
            # TODO: Implement redline generation logic
            clauses = blackboard.get("clauses", [])
            assessments = blackboard.get("assessments", [])
            
            # Only generate proposals for high and medium risk clauses
            risky_assessments = [
                assessment for assessment in assessments
                if assessment.get("risk_level") in ["HIGH", "MEDIUM"]
            ]
            
            proposals = []
            for assessment in risky_assessments:
                clause = next(
                    (c for c in clauses if c["clause_id"] == assessment["clause_id"]),
                    None
                )
                
                if clause:
                    proposal = self._generate_proposal_detailed(clause, assessment, blackboard.get("policy_rules", {}))
                    proposals.append(proposal)
            
            # Write to blackboard
            blackboard["proposals"] = proposals
            
            # Record execution in history
            if "history" not in blackboard:
                blackboard["history"] = []
            blackboard["history"].append({
                "step": "redline_generation_complete",
                "agent": self.name,
                "status": "success",
                "timestamp": task.get("timestamp", "unknown"),
                "output": {"proposal_count": len(proposals)}
            })
            
            self.status = AgentStatus.SUCCESS
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output={"proposal_count": len(proposals)}
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            # Record error in history
            if "history" not in blackboard:
                blackboard["history"] = []
            blackboard["history"].append({
                "step": "redline_generation_failed",
                "agent": self.name,
                "status": "error",
                "timestamp": task.get("timestamp", "unknown"),
                "error": str(e)
            })
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e)
            )
    
    def _generate_proposal_detailed(self, clause: Dict[str, Any], assessment: Dict[str, Any], policy_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a detailed redline proposal for a single clause based on risk assessment and policy rules
        """
        original_text = clause["text"]
        risk_level = assessment["risk_level"]
        rationale = assessment["rationale"]
        
        # Generate proposed text based on risk level and policy rules
        proposed_text = self._create_proposed_text(original_text, risk_level, policy_rules)
        
        # Determine the appropriate variant based on risk level
        variant = "conservative" if risk_level == "HIGH" else "moderate"
        
        return {
            "clause_id": clause["clause_id"],
            "original_text": original_text,
            "proposed_text": proposed_text,
            "rationale": f"Mitigating {risk_level.lower()} risk identified in assessment: {rationale}",
            "variant": variant,
            "policy_refs": assessment.get("policy_refs", [])
        }
    
    def _create_proposed_text(self, original_text: str, risk_level: str, policy_rules: Dict[str, Any]) -> str:
        """
        Create proposed text with appropriate modifications based on risk level and policy rules
        """
        import re
        
        modified_text = original_text
        
        # Apply policy-based modifications based on policy rules
        for rule_name, rule_value in policy_rules.items():
            if "liability" in rule_name.lower() and "cap" in str(rule_value).lower():
                # Replace unlimited liability language
                modified_text = re.sub(
                    r'(unlimited|all|any)\s+(liability|damages)',
                    f'liability limited to {rule_value}',
                    modified_text,
                    flags=re.IGNORECASE
                )
            
            if "confidentiality_period" in rule_name.lower():
                # Replace with policy-specified period
                modified_text = re.sub(
                    r'(confidentiality\s+period|term\s+of\s+confidentiality)',
                    f'confidentiality period of {rule_value}',
                    modified_text,
                    flags=re.IGNORECASE
                )
        
        # Apply risk-level-specific modifications
        if risk_level == "HIGH":
            # For high risk, more conservative changes
            modifications = [
                # Replace broad indemnification with limited scope
                (r'(each\s+party\s+shall\s+indemnify)', r'the disclosing party shall indemnify only for breaches of confidentiality obligations'),
                # Replace unlimited liability with specific caps
                (r'(unlimited\s+liability|no\s+limit)', r'liability limited to direct damages only'),
                # Replace broad audit rights with specific conditions
                (r'(right\s+to\s+audit)', r'right to audit upon reasonable request and with proper cause')
            ]
        elif risk_level == "MEDIUM":
            # For medium risk, moderate changes
            modifications = [
                (r'(reasonable\s+efforts)', r'reasonable commercial efforts'),
                (r'(upon\s+request)', r'upon written request with proper justification'),
                (r'(standard)', r'industry standard')
            ]
        else:
            # For low risk, minimal changes
            modifications = []
        
        # Apply modifications
        for pattern, replacement in modifications:
            modified_text = re.sub(pattern, replacement, modified_text, flags=re.IGNORECASE)
        
        # If no specific modifications were made, return original with annotation
        if modified_text == original_text:
            return f"[PROPOSED CHANGES NEEDED]\\nORIGINAL:\\n{original_text}\\n\\nCHANGES: Address {risk_level} risk items identified in assessment."
        else:
            return modified_text
    
    def _generate_proposal(self, clause: Dict[str, Any], assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a redline proposal for a single clause.
        
        TODO: Implement sophisticated redline generation
        """
        # Simple example - students should improve this
        return {
            "clause_id": clause["clause_id"],
            "original_text": clause["text"],
            "proposed_text": f"[REDLINED] {clause['text']}",
            "rationale": "Proposed change to mitigate risk",
            "variant": "conservative"
        }
