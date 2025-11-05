#!/bin/bash
# Load Testing Automation Script
# Runs k6 load tests with different scenarios and generates reports
# This script automatically changes to the exercise_11 directory

set -e

# Change to exercise_11 directory (assuming script is in exercise_11/load/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.." || exit 1

if [ ! -f "load/k6/coach_scenario.js" ]; then
    echo "ERROR: Cannot find load test scripts. Please ensure script is in exercise_11/load/"
    echo "Current directory: $(pwd)"
    exit 1
fi

BASE_URL="${BASE_URL:-http://localhost:8011}"
REPORTS_DIR="load/reports"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Create reports directory if it doesn't exist
mkdir -p "$REPORTS_DIR"

echo "🚀 Starting Load Tests..."
echo "Working directory: $(pwd)"
echo "Base URL: $BASE_URL"
echo "Reports will be saved to: $REPORTS_DIR"
echo ""

# Test 1: Standard SLO Validation (10 VUs, 15 minutes)
echo "📊 Test 1: SLO Validation (10 VUs, 15 minutes)..."
k6 run \
  --env BASE_URL="$BASE_URL" \
  --env VUS=10 \
  --env DURATION=15m \
  --out json="$REPORTS_DIR/k6_slo_validation_${TIMESTAMP}.json" \
  load/k6/coach_scenario.js
echo "✅ SLO Validation complete"
echo ""

# Test 2: Ramp-up Test (0 → 100 users over 5 minutes)
echo "📊 Test 2: Ramp-up Test (0 → 100 users over 5 minutes)..."
k6 run \
  --env BASE_URL="$BASE_URL" \
  --out json="$REPORTS_DIR/k6_rampup_${TIMESTAMP}.json" \
  load/k6/ramp_up_scenario.js
echo "✅ Ramp-up test complete"
echo ""

# Test 3: Spike Test (Sudden 10x traffic)
echo "📊 Test 3: Spike Test (Sudden 10x traffic increase)..."
k6 run \
  --env BASE_URL="$BASE_URL" \
  --out json="$REPORTS_DIR/k6_spike_${TIMESTAMP}.json" \
  load/k6/spike_scenario.js
echo "✅ Spike test complete"
echo ""

# Test 4: Sustained Load (50 VUs, 10 minutes)
echo "📊 Test 4: Sustained Load (50 VUs, 10 minutes)..."
k6 run \
  --env BASE_URL="$BASE_URL" \
  --env VUS=50 \
  --env DURATION=10m \
  --out json="$REPORTS_DIR/k6_sustained_50vu_${TIMESTAMP}.json" \
  load/k6/coach_scenario.js
echo "✅ Sustained load test complete"
echo ""

# Test 5: Sustained Load (100 VUs, 15 minutes)
echo "📊 Test 5: Sustained Load (100 VUs, 15 minutes)..."
k6 run \
  --env BASE_URL="$BASE_URL" \
  --env VUS=100 \
  --env DURATION=15m \
  --out json="$REPORTS_DIR/k6_sustained_100vu_${TIMESTAMP}.json" \
  load/k6/coach_scenario.js
echo "✅ Sustained load test complete"
echo ""

echo "🎉 All load tests completed!"
echo "📁 Reports saved to: $REPORTS_DIR"
echo ""
echo "To view results, use:"
echo "  k6 stats $REPORTS_DIR/k6_*.json"
echo "  or"
echo "  k6 report $REPORTS_DIR/k6_*.json"

