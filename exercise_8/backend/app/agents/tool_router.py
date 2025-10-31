"""
Tool Router implementation for dynamic tool selection
"""
import asyncio
from typing import Dict, Any, List, Callable
from app.agents.base import BaseAgent, Blackboard, Tool


class ToolRouterAgent(BaseAgent):
    """Agent that routes requests to appropriate tools based on context"""
    
    def __init__(self, agent_id: str, blackboard: Blackboard):
        super().__init__(agent_id, blackboard)
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self) -> Dict[str, Tool]:
        """Initialize available tools"""
        tools = {}
        
        # Policy lookup tool
        tools["policy_lookup"] = Tool(
            name="policy_lookup",
            description="Look up policy rules for comparison",
            execute=self._policy_lookup
        )
        
        # Risk analysis tool
        tools["risk_analyzer"] = Tool(
            name="risk_analyzer", 
            description="Analyze risk using AI or heuristics",
            execute=self._risk_analysis
        )
        
        # Redline generation tool
        tools["redline_generator"] = Tool(
            name="redline_generator",
            description="Generate redline proposals",
            execute=self._generate_redline
        )
        
        # Document parsing tool
        tools["document_parser"] = Tool(
            name="document_parser",
            description="Parse document into clauses",
            execute=self._parse_document
        )
        
        return tools
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route the task to appropriate tool based on context"""
        task_type = task.get("type", "general")
        context = task.get("context", {})
        
        self.blackboard.add_history({
            "step": "tool_routing",
            "agent": self.agent_id,
            "status": "started",
            "task_type": task_type,
            "context": context
        })
        
        # Determine which tool to use based on task type and context
        tool_name = await self._determine_tool(task)
        
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            result = await tool.execute(context)
            
            # Update history with tool execution
            self.blackboard.add_history({
                "step": f"tool_execution_{tool_name}",
                "agent": self.agent_id,
                "status": "completed",
                "tool_used": tool_name,
                "result": result
            })
            
            return {
                "tool_used": tool_name,
                "result": result,
                "status": "success"
            }
        else:
            error_result = {
                "tool_used": None,
                "result": None,
                "status": "error",
                "error": f"Unknown or unavailable tool: {tool_name}"
            }
            
            self.blackboard.add_history({
                "step": "tool_routing",
                "agent": self.agent_id,
                "status": "error",
                "error": error_result["error"]
            })
            
            return error_result
    
    async def _determine_tool(self, task: Dict[str, Any]) -> str:
        """Determine which tool to use based on task and context"""
        task_type = task.get("type", "general")
        context = task.get("context", {})
        
        # Rule-based tool selection
        if task_type == "policy_check":
            return "policy_lookup"
        elif task_type == "risk_assessment":
            # If we have policy rules, try policy lookup first; otherwise use AI analysis
            if context.get("policy_rules"):
                # For demo purposes, randomly select based on a configured probability
                import random
                if random.random() > 0.7:  # 30% of the time use policy lookup, 70% use AI
                    return "policy_lookup"
                else:
                    return "risk_analyzer"
            else:
                return "risk_analyzer"
        elif task_type == "redline_generation":
            return "redline_generator"
        elif task_type == "document_parsing":
            return "document_parser"
        else:
            # Default to risk analyzer for general tasks
            return "risk_analyzer"
    
    async def _policy_lookup(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute policy lookup tool"""
        try:
            policy_rules = context.get("policy_rules", {})
            clause_text = context.get("clause_text", "")
            
            # Simple policy matching for demo
            matched_rules = []
            for rule_name, rule_value in policy_rules.items():
                if isinstance(rule_value, str) and rule_value.lower() in clause_text.lower():
                    matched_rules.append({
                        "rule": rule_name,
                        "value": rule_value,
                        "matched_in": clause_text[:100]  # First 100 chars for demo
                    })
            
            return {
                "matched_rules": matched_rules,
                "rule_count": len(matched_rules),
                "status": "completed"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _risk_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk analysis tool (using the existing function)"""
        try:
            from app.main import analyze_risk_with_openai
            clause_text = context.get("clause_text", "")
            policy_rules = context.get("policy_rules", {})
            
            # Use the existing risk analysis function
            analysis_result = analyze_risk_with_openai(clause_text, policy_rules)
            
            return {
                "risk_level": analysis_result["risk_level"],
                "rationale": analysis_result["rationale"],
                "policy_refs": analysis_result["policy_refs"],
                "status": "completed"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _generate_redline(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute redline generation tool"""
        try:
            clause_id = context.get("clause_id", "")
            original_text = context.get("original_text", "")
            risk_level = context.get("risk_level", "Low")
            
            # Simple redline generation for demo
            redline_text = f"[REDACTED: Clause {clause_id} requires review - Risk Level: {risk_level}]"
            
            return {
                "clause_id": clause_id,
                "original_text": original_text,
                "redline_text": redline_text,
                "risk_level": risk_level,
                "status": "completed"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _parse_document(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document parsing tool"""
        try:
            document_content = context.get("document_content", "")
            filename = context.get("filename", "unknown")
            
            # Use existing parse function if available, otherwise simple parsing
            from app.main import parse_document_content
            parsed_result = parse_document_content(document_content, filename)
            
            return {
                "clauses_count": len(parsed_result["clauses"]),
                "clauses": parsed_result["clauses"],
                "filename": filename,
                "status": "completed"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


async def route_to_tool(blackboard: Blackboard, task: Dict[str, Any]) -> Dict[str, Any]:
    """Route a task to the appropriate tool"""
    router = ToolRouterAgent("tool-router-agent-1", blackboard)
    return await router.execute(task)