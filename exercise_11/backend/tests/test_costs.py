"""
Simple tests for cost tracking functionality.
"""

from billing.ledger import CostTracker, get_tracker


def test_cost_calculation():
    """Test basic cost calculation for gpt-3.5-turbo."""
    tracker = CostTracker(daily_budget=5.00)
    
    # Log a typical usage
    record = tracker.log_usage(
        session_id="test_session",
        model="gpt-3.5-turbo",
        prompt_tokens=300,
        completion_tokens=150
    )
    
    # Verify tokens
    assert record.total_tokens == 450
    assert record.prompt_tokens == 300
    assert record.completion_tokens == 150
    
    # Verify cost calculation
    # gpt-3.5-turbo: $0.0005/1K prompt, $0.0015/1K completion
    expected_cost = (300 * 0.0005 / 1000) + (150 * 0.0015 / 1000)
    assert abs(record.cost - expected_cost) < 0.0001
    
    print(f"✅ Cost calculated correctly: ${record.cost:.6f}")


def test_budget_tracking():
    """Test budget status tracking."""
    tracker = CostTracker(daily_budget=1.00)
    
    # Log some usage
    tracker.log_usage("sess1", "gpt-3.5-turbo", 1000, 500)
    tracker.log_usage("sess2", "gpt-3.5-turbo", 500, 300)
    
    # Get status
    status = tracker.get_budget_status()
    
    assert "total_cost" in status
    assert "daily_budget" in status
    assert status["daily_budget"] == 1.00
    assert "percentage" in status
    assert "over_budget" in status
    
    print(f"✅ Budget status: ${status['total_cost']:.4f} / ${status['daily_budget']:.2f} ({status['percentage']:.1f}%)")


def test_session_cost():
    """Test per-session cost tracking."""
    tracker = CostTracker()
    
    # Log usage for different sessions
    tracker.log_usage("sess_abc", "gpt-3.5-turbo", 300, 200)
    tracker.log_usage("sess_xyz", "gpt-3.5-turbo", 400, 300)
    tracker.log_usage("sess_abc", "gpt-3.5-turbo", 200, 100)
    
    # Get session-specific cost
    sess_abc_cost = tracker.get_session_cost("sess_abc")
    sess_xyz_cost = tracker.get_session_cost("sess_xyz")
    
    # sess_abc should have 2 requests
    assert sess_abc_cost > 0
    assert sess_xyz_cost > 0
    assert sess_abc_cost > sess_xyz_cost  # More tokens
    
    print(f"✅ Session tracking works: sess_abc=${sess_abc_cost:.4f}, sess_xyz=${sess_xyz_cost:.4f}")


def test_over_budget_detection():
    """Test budget limit detection."""
    tracker = CostTracker(daily_budget=0.001)  # Very low budget
    
    # This should exceed budget
    tracker.log_usage("sess1", "gpt-3.5-turbo", 5000, 3000)
    
    assert tracker.is_over_budget() == True
    
    status = tracker.get_budget_status()
    assert status["over_budget"] == True
    
    print(f"✅ Over-budget detection works: ${status['total_cost']:.4f} > ${status['daily_budget']:.2f}")


if __name__ == "__main__":
    # Run tests manually
    print("\n🧪 Testing Cost Tracking System\n")
    test_cost_calculation()
    test_budget_tracking()
    test_session_cost()
    test_over_budget_detection()
    print("\n✅ All cost tracking tests passed!\n")

