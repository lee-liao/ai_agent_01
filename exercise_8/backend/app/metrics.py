"""
Metrics and cost tracking functionality for Exercise 8
"""
import time
from typing import Dict, Any, List
from app.agents.base import Blackboard


class MetricsTracker:
    """Track metrics, costs, and quality indicators"""
    
    def __init__(self):
        self.metrics = {}
        self.costs = {}
        self.quality_indicators = {}
    
    def calculate_run_metrics(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for a specific run"""
        assessments = run_data.get("assessments", [])
        proposals = run_data.get("proposals", [])
        history = run_data.get("history", [])
        
        high_risk_count = sum(1 for a in assessments if a.get("risk_level", "").lower() == "high")
        medium_risk_count = sum(1 for a in assessments if a.get("risk_level", "").lower() == "medium")
        low_risk_count = sum(1 for a in assessments if a.get("risk_level", "").lower() == "low")
        
        metrics = {
            "total_clauses": len(run_data.get("clauses", [])),
            "assessed_clauses": len(assessments),
            "high_risk_clauses": high_risk_count,
            "medium_risk_clauses": medium_risk_count,
            "low_risk_clauses": low_risk_count,
            "proposals_generated": len(proposals),
            "total_steps": len(history),
            "run_score": run_data.get("score", 0),
            "processing_time": self._calculate_processing_time(history),
            "agent_path": run_data.get("agent_path"),
        }
        
        return metrics
    
    def _calculate_processing_time(self, history: List[Dict[str, Any]]) -> float:
        """Calculate total processing time from history"""
        if not history:
            return 0.0
        
        timestamps = [entry.get("timestamp", 0) for entry in history if "timestamp" in entry]
        if len(timestamps) < 2:
            return 0.0
        
        return max(timestamps) - min(timestamps)
    
    def calculate_cost(self, run_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate costs for a specific run (approximate)"""
        # In a real implementation, this would track actual API usage
        assessments = run_data.get("assessments", [])
        proposals = run_data.get("proposals", [])
        
        # Approximate cost calculation (these are placeholder values)
        cost_per_assessment = 0.0005  # $0.0005 per assessment
        cost_per_proposal = 0.001    # $0.001 per proposal
        
        total_cost = (
            len(assessments) * cost_per_assessment +
            len(proposals) * cost_per_proposal
        )
        
        costs = {
            "assessments_cost": round(len(assessments) * cost_per_assessment, 4),
            "proposals_cost": round(len(proposals) * cost_per_proposal, 4),
            "total_cost": round(total_cost, 4),
            "currency": "USD"
        }
        
        return costs
    
    def calculate_quality_indicators(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quality indicators for a run"""
        assessments = run_data.get("assessments", [])
        
        if not assessments:
            return {
                "pass_rate": 1.0,
                "precision": 0.0,
                "mitigation_rate": 0.0,
                "quality_score": 0.0
            }
        
        high_risk_count = sum(1 for a in assessments if a.get("risk_level", "").lower() == "high")
        total_assessments = len(assessments)
        
        # Simple quality metrics calculation
        quality_indicators = {
            "pass_rate": round((total_assessments - high_risk_count) / total_assessments, 3) if total_assessments > 0 else 1.0,
            "precision": 0.85,  # Placeholder - in real implementation, this would be calculated based on validation
            "mitigation_rate": round(high_risk_count / total_assessments, 3) if total_assessments > 0 else 0.0,
            "quality_score": run_data.get("score", 0) / 100  # Convert score to 0-1 scale
        }
        
        return quality_indicators
    
    def get_slo_metrics(self) -> Dict[str, Any]:
        """Get service level objective metrics"""
        # Placeholder values - in a real implementation, these would come from actual measurements
        return {
            "p50_ms": 1200,
            "p95_ms": 3200,
            "p99_ms": 5800,
            "reviewer_pass_rate": 0.9,
            "availability": 0.995,
            "error_rate": 0.002
        }


# Global metrics tracker instance
metrics_tracker = MetricsTracker()


def get_run_metrics(run_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get metrics for a specific run"""
    return metrics_tracker.calculate_run_metrics(run_data)


def get_run_costs(run_data: Dict[str, Any]) -> Dict[str, float]:
    """Get cost information for a specific run"""
    return metrics_tracker.calculate_cost(run_data)


def get_run_quality_indicators(run_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get quality indicators for a specific run"""
    return metrics_tracker.calculate_quality_indicators(run_data)


def get_slo_metrics() -> Dict[str, Any]:
    """Get service level objective metrics"""
    return metrics_tracker.get_slo_metrics()