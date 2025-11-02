"""
Cost tracking and budget management for OpenAI API usage.
Tracks tokens and calculates costs per request.
"""

from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, asdict
import json


# OpenAI pricing (as of Nov 2024)
PRICING = {
    "gpt-3.5-turbo": {
        "prompt": 0.0005 / 1000,      # $0.0005 per 1K prompt tokens
        "completion": 0.0015 / 1000,  # $0.0015 per 1K completion tokens
    },
    "gpt-4": {
        "prompt": 0.03 / 1000,        # $0.03 per 1K prompt tokens
        "completion": 0.06 / 1000,    # $0.06 per 1K completion tokens
    }
}


@dataclass
class UsageRecord:
    """Record of a single API call's token usage and cost."""
    session_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


class CostTracker:
    """Tracks token usage and costs for OpenAI API calls."""
    
    def __init__(self, daily_budget: float = 5.00):
        """
        Initialize cost tracker.
        
        Args:
            daily_budget: Maximum daily budget in USD (default: $5.00)
        """
        self.usage_records: List[UsageRecord] = []
        self.daily_budget = daily_budget
    
    def log_usage(
        self,
        session_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> UsageRecord:
        """
        Log token usage and calculate cost.
        
        Args:
            session_id: Session identifier
            model: OpenAI model name (e.g., 'gpt-3.5-turbo')
            prompt_tokens: Number of prompt tokens used
            completion_tokens: Number of completion tokens used
            
        Returns:
            UsageRecord with calculated cost
        """
        total_tokens = prompt_tokens + completion_tokens
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)
        
        record = UsageRecord(
            session_id=session_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            timestamp=datetime.now().isoformat()
        )
        
        self.usage_records.append(record)
        
        # Console logging for visibility
        print(f"💰 Cost: ${cost:.4f} | Tokens: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens}) | Session: {session_id[:12]}")
        
        return record
    
    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate cost for a request.
        
        Args:
            model: OpenAI model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Cost in USD
        """
        pricing = PRICING.get(model, PRICING["gpt-3.5-turbo"])
        
        prompt_cost = prompt_tokens * pricing["prompt"]
        completion_cost = completion_tokens * pricing["completion"]
        
        return prompt_cost + completion_cost
    
    def get_total_cost(self) -> float:
        """Get total cost of all logged usage."""
        return sum(record.cost for record in self.usage_records)
    
    def get_total_tokens(self) -> int:
        """Get total tokens used across all requests."""
        return sum(record.total_tokens for record in self.usage_records)
    
    def get_session_cost(self, session_id: str) -> float:
        """Get total cost for a specific session."""
        return sum(
            record.cost 
            for record in self.usage_records 
            if record.session_id == session_id
        )
    
    def is_over_budget(self) -> bool:
        """Check if daily budget has been exceeded."""
        return self.get_total_cost() > self.daily_budget
    
    def get_budget_status(self) -> Dict:
        """
        Get current budget utilization status.
        
        Returns:
            Dict with total_cost, budget, percentage, over_budget
        """
        total_cost = self.get_total_cost()
        percentage = (total_cost / self.daily_budget) * 100 if self.daily_budget > 0 else 0
        
        return {
            "total_cost": round(total_cost, 4),
            "daily_budget": self.daily_budget,
            "percentage": round(percentage, 1),
            "over_budget": self.is_over_budget(),
            "remaining": round(self.daily_budget - total_cost, 4)
        }
    
    def print_summary(self):
        """Print cost summary to console."""
        status = self.get_budget_status()
        total_tokens = self.get_total_tokens()
        num_requests = len(self.usage_records)
        
        print("\n" + "="*60)
        print("💰 COST TRACKER SUMMARY")
        print("="*60)
        print(f"Total Requests:    {num_requests}")
        print(f"Total Tokens:      {total_tokens:,}")
        print(f"Total Cost:        ${status['total_cost']:.4f}")
        print(f"Daily Budget:      ${status['daily_budget']:.2f}")
        print(f"Budget Used:       {status['percentage']:.1f}%")
        print(f"Remaining:         ${status['remaining']:.4f}")
        print(f"Status:            {'⚠️ OVER BUDGET' if status['over_budget'] else '✅ Under budget'}")
        print("="*60 + "\n")
    
    def export_csv(self, filepath: str = "billing/usage_report.csv"):
        """
        Export usage records to CSV.
        
        Args:
            filepath: Path to save CSV file
        """
        import csv
        from pathlib import Path
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            if self.usage_records:
                fieldnames = self.usage_records[0].to_dict().keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for record in self.usage_records:
                    writer.writerow(record.to_dict())
        
        print(f"📊 Exported {len(self.usage_records)} records to {filepath}")


# Global tracker instance
_tracker_instance = None


def get_tracker(daily_budget: float = 5.00) -> CostTracker:
    """Get or create the global CostTracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = CostTracker(daily_budget=daily_budget)
    return _tracker_instance

