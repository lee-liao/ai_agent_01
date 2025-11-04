"""
Billing Ledger Module
Tracks token usage and costs per turn/request.
"""

import json
import csv
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal

# Configuration
# Typical token estimates (4 characters ≈ 1 token, but varies)
CHARS_PER_TOKEN = 4.0

# Cost per 1M tokens (example pricing - adjust based on your model)
# Using approximate OpenAI GPT-4 pricing as reference
INPUT_COST_PER_MILLION = 30.0   # $30 per 1M input tokens
OUTPUT_COST_PER_MILLION = 60.0  # $60 per 1M output tokens


@dataclass
class TurnRecord:
    """Record of a single turn/request."""
    turn_id: str
    session_id: str
    timestamp: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    model_mode: str  # 'full' or 'lite'
    was_over_budget: bool


class BillingLedger:
    """
    Ledger for tracking token usage and costs.
    Stores records in memory (production would use a database).
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize billing ledger.
        
        Args:
            storage_dir: Directory for storing CSV reports (default: billing/reports/)
        """
        if storage_dir is None:
            # Default to billing/reports/ relative to this file
            base_dir = Path(__file__).parent
            storage_dir = base_dir / "reports"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage (in production, use a database)
        self.turns: List[TurnRecord] = []
        
        # Budget configuration (per day)
        self.daily_budget_usd = 100.0  # $100/day default
        
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from text length.
        
        Args:
            text: Input or output text
            
        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token
        # This is approximate; actual tokenization varies by model
        return max(1, int(len(text) / CHARS_PER_TOKEN))
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost in USD for given token counts.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_MILLION
        output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_MILLION
        return input_cost + output_cost
    
    def record_turn(
        self,
        session_id: str,
        input_text: str,
        output_text: str,
        model_mode: str = "full",
        was_over_budget: bool = False
    ) -> TurnRecord:
        """
        Record a turn/request with token usage and cost.
        
        Args:
            session_id: Session identifier
            input_text: User input text
            output_text: Generated output text
            model_mode: 'full' or 'lite'
            was_over_budget: Whether request was over budget
            
        Returns:
            TurnRecord with recorded data
        """
        turn_id = f"turn_{datetime.utcnow().isoformat().replace(':', '-')}_{len(self.turns)}"
        
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(output_text)
        cost_usd = self.calculate_cost(input_tokens, output_tokens)
        
        record = TurnRecord(
            turn_id=turn_id,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            model_mode=model_mode,
            was_over_budget=was_over_budget
        )
        
        self.turns.append(record)
        
        return record
    
    def get_daily_cost(self, target_date: Optional[date] = None) -> float:
        """
        Get total cost for a specific day.
        
        Args:
            target_date: Date to check (default: today)
            
        Returns:
            Total cost in USD for that day
        """
        if target_date is None:
            target_date = date.today()
        
        target_date_str = target_date.isoformat()
        
        daily_cost = sum(
            record.cost_usd
            for record in self.turns
            if record.timestamp.startswith(target_date_str)
        )
        
        return daily_cost
    
    def is_over_budget(self, target_date: Optional[date] = None) -> Tuple[bool, float, float]:
        """
        Check if daily budget is exceeded.
        
        Args:
            target_date: Date to check (default: today)
            
        Returns:
            Tuple of (is_over_budget, current_cost, budget_limit)
        """
        current_cost = self.get_daily_cost(target_date)
        is_over = current_cost >= self.daily_budget_usd
        
        return is_over, current_cost, self.daily_budget_usd
    
    def get_daily_stats(self, target_date: Optional[date] = None) -> Dict:
        """
        Get statistics for a specific day.
        
        Args:
            target_date: Date to check (default: today)
            
        Returns:
            Dictionary with daily statistics
        """
        if target_date is None:
            target_date = date.today()
        
        target_date_str = target_date.isoformat()
        
        day_records = [
            record for record in self.turns
            if record.timestamp.startswith(target_date_str)
        ]
        
        if not day_records:
            return {
                "date": target_date_str,
                "total_turns": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0.0,
                "full_mode_turns": 0,
                "lite_mode_turns": 0,
                "over_budget_turns": 0,
                "budget_limit_usd": self.daily_budget_usd,
                "budget_remaining_usd": round(self.daily_budget_usd, 4)
            }
        
        total_input = sum(r.input_tokens for r in day_records)
        total_output = sum(r.output_tokens for r in day_records)
        total_cost = sum(r.cost_usd for r in day_records)
        
        return {
            "date": target_date_str,
            "total_turns": len(day_records),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost_usd": round(total_cost, 4),
            "full_mode_turns": sum(1 for r in day_records if r.model_mode == "full"),
            "lite_mode_turns": sum(1 for r in day_records if r.model_mode == "lite"),
            "over_budget_turns": sum(1 for r in day_records if r.was_over_budget),
            "budget_limit_usd": self.daily_budget_usd,
            "budget_remaining_usd": round(self.daily_budget_usd - total_cost, 4)
        }
    
    def generate_daily_csv(self, target_date: Optional[date] = None) -> Path:
        """
        Generate CSV report for a specific day.
        
        Args:
            target_date: Date to generate report for (default: today)
            
        Returns:
            Path to generated CSV file
        """
        if target_date is None:
            target_date = date.today()
        
        target_date_str = target_date.isoformat()
        filename = f"billing_report_{target_date_str}.csv"
        csv_path = self.storage_dir / filename
        
        # Get day's records
        day_records = [
            record for record in self.turns
            if record.timestamp.startswith(target_date_str)
        ]
        
        # Write CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if day_records:
                writer = csv.DictWriter(f, fieldnames=[
                    'turn_id', 'session_id', 'timestamp',
                    'input_tokens', 'output_tokens', 'total_tokens',
                    'cost_usd', 'model_mode', 'was_over_budget'
                ])
                writer.writeheader()
                
                for record in day_records:
                    writer.writerow({
                        'turn_id': record.turn_id,
                        'session_id': record.session_id,
                        'timestamp': record.timestamp,
                        'input_tokens': record.input_tokens,
                        'output_tokens': record.output_tokens,
                        'total_tokens': record.input_tokens + record.output_tokens,
                        'cost_usd': f"{record.cost_usd:.6f}",
                        'model_mode': record.model_mode,
                        'was_over_budget': 'true' if record.was_over_budget else 'false'
                    })
            else:
                # Empty file with headers
                writer = csv.DictWriter(f, fieldnames=[
                    'turn_id', 'session_id', 'timestamp',
                    'input_tokens', 'output_tokens', 'total_tokens',
                    'cost_usd', 'model_mode', 'was_over_budget'
                ])
                writer.writeheader()
        
        return csv_path
    
    def generate_summary_report(self, days: int = 7) -> Dict:
        """
        Generate summary report for last N days.
        
        Args:
            days: Number of days to include in report
            
        Returns:
            Dictionary with summary statistics and sparkline data
        """
        today = date.today()
        dates = [today - timedelta(days=i) for i in range(days)]
        dates.reverse()  # Oldest to newest
        
        daily_stats = []
        sparkline_data = []
        
        for day in dates:
            stats = self.get_daily_stats(day)
            daily_stats.append(stats)
            sparkline_data.append(stats["total_cost_usd"])
        
        total_cost = sum(s["total_cost_usd"] for s in daily_stats)
        total_turns = sum(s["total_turns"] for s in daily_stats)
        avg_daily_cost = total_cost / len(daily_stats) if daily_stats else 0
        
        return {
            "period_days": days,
            "start_date": dates[0].isoformat(),
            "end_date": dates[-1].isoformat(),
            "total_cost_usd": round(total_cost, 4),
            "total_turns": total_turns,
            "avg_daily_cost_usd": round(avg_daily_cost, 4),
            "daily_stats": daily_stats,
            "sparkline_data": sparkline_data  # For visualization
        }
    
    def set_daily_budget(self, budget_usd: float):
        """Set daily budget limit."""
        self.daily_budget_usd = budget_usd


# Global ledger instance
_ledger_instance: Optional[BillingLedger] = None


def get_ledger() -> BillingLedger:
    """Get or create global ledger instance."""
    global _ledger_instance
    if _ledger_instance is None:
        _ledger_instance = BillingLedger()
    return _ledger_instance


def reset_ledger():
    """Reset ledger (useful for testing)."""
    global _ledger_instance
    _ledger_instance = None


# Compatibility wrapper for CostTracker interface
class CostTracker:
    """
    Compatibility wrapper for BillingLedger that provides CostTracker interface.
    Provides log_usage() method for tracking OpenAI API usage.
    """
    
    def __init__(self, daily_budget: float = 5.0):
        """Initialize with daily budget."""
        self.ledger = BillingLedger()
        self.ledger.set_daily_budget(daily_budget)
        self.daily_budget = daily_budget
        
        # Cost per 1K tokens for gpt-3.5-turbo (approximate)
        self.COST_PER_1K_INPUT = 0.0015   # $0.0015 per 1K input tokens
        self.COST_PER_1K_OUTPUT = 0.002   # $0.002 per 1K output tokens
    
    def log_usage(
        self,
        session_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Dict:
        """
        Log API usage and calculate cost.
        
        Args:
            session_id: Session identifier
            model: Model name (e.g., "gpt-3.5-turbo")
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Dict with usage details
        """
        # Try to import observability for spans
        try:
            import sys
            from pathlib import Path
            # Add backend directory to path if not already there
            backend_dir = Path(__file__).parent.parent / "backend"
            if str(backend_dir) not in sys.path:
                sys.path.insert(0, str(backend_dir))
            from app.observability import get_tracer
            import time
            tracer = get_tracer()
            start_time = time.time()
        except ImportError:
            tracer = None
            start_time = None
        
        # Create span for cost tracking if observability is available
        if tracer:
            with tracer.start_as_current_span("billing.log_usage") as span:
                # Set initial attributes
                span.set_attribute("billing.session_id", session_id)
                span.set_attribute("billing.model", model)
                span.set_attribute("billing.prompt_tokens", prompt_tokens)
                span.set_attribute("billing.completion_tokens", completion_tokens)
                
                # Calculate cost
                total_tokens = prompt_tokens + completion_tokens
                cost = (prompt_tokens / 1000 * self.COST_PER_1K_INPUT) + \
                       (completion_tokens / 1000 * self.COST_PER_1K_OUTPUT)
                
                # Check budget status
                daily_cost = self.ledger.get_daily_cost()
                is_over_budget = daily_cost + cost >= self.daily_budget
                
                # Record in ledger
                # Create dummy input/output text for record_turn (it uses estimate_tokens)
                input_text = "x" * (prompt_tokens * 4)  # Rough estimate
                output_text = "x" * (completion_tokens * 4)
                
                record = self.ledger.record_turn(
                    session_id=session_id,
                    input_text=input_text,
                    output_text=output_text,
                    model_mode="full",
                    was_over_budget=is_over_budget
                )
                
                # Log to console (with emoji)
                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    f"💰 Cost: ${cost:.4f} | Tokens: {total_tokens} "
                    f"(prompt: {prompt_tokens}, completion: {completion_tokens}) | Session: {session_id}"
                )
                
                # Calculate latency and set final attributes
                latency_ms = (time.time() - start_time) * 1000 if start_time else 0
                span.set_attribute("billing.total_tokens", total_tokens)
                span.set_attribute("billing.cost_usd", cost)
                span.set_attribute("billing.daily_cost_usd", daily_cost + cost)
                span.set_attribute("billing.daily_budget_usd", self.daily_budget)
                span.set_attribute("billing.is_over_budget", is_over_budget)
                span.set_attribute("billing.latency_ms", latency_ms)
                
                return {
                    "session_id": session_id,
                    "model": model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                    "daily_cost": daily_cost + cost,
                    "is_over_budget": is_over_budget
                }
        else:
            # No observability - just do the work
            total_tokens = prompt_tokens + completion_tokens
            cost = (prompt_tokens / 1000 * self.COST_PER_1K_INPUT) + \
                   (completion_tokens / 1000 * self.COST_PER_1K_OUTPUT)
            
            daily_cost = self.ledger.get_daily_cost()
            is_over_budget = daily_cost + cost >= self.daily_budget
            
            input_text = "x" * (prompt_tokens * 4)
            output_text = "x" * (completion_tokens * 4)
            
            record = self.ledger.record_turn(
                session_id=session_id,
                input_text=input_text,
                output_text=output_text,
                model_mode="full",
                was_over_budget=is_over_budget
            )
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"💰 Cost: ${cost:.4f} | Tokens: {total_tokens} "
                f"(prompt: {prompt_tokens}, completion: {completion_tokens}) | Session: {session_id}"
            )
            
            return {
                "session_id": session_id,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "daily_cost": daily_cost + cost,
                "is_over_budget": is_over_budget
            }
    
    def get_budget_status(self) -> Dict:
        """Get current budget status."""
        return self.ledger.get_daily_stats()
    
    def print_summary(self):
        """Print summary of usage (for debugging)."""
        stats = self.get_budget_status()
        print(f"Total cost today: ${stats['total_cost_usd']:.4f}")
        print(f"Total turns: {stats['total_turns']}")
        print(f"Budget: ${stats['budget_limit_usd']:.2f}")


# Global tracker instance
_tracker_instance: Optional[CostTracker] = None


# Alias for compatibility
def get_tracker(daily_budget: float = 5.0) -> CostTracker:
    """
    Get or create CostTracker instance.
    
    Args:
        daily_budget: Daily budget in USD (default: $5.00)
        Note: Budget is only set on first creation, subsequent calls use existing instance.
        
    Returns:
        CostTracker instance
    """
    global _tracker_instance
    
    if _tracker_instance is None:
        _tracker_instance = CostTracker(daily_budget=daily_budget)
    
    return _tracker_instance

