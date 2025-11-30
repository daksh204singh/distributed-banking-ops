#!/bin/bash
# Load testing script for distributed banking operations
# Uses locust.conf for default settings, with optional command-line overrides
#
# Usage:
#   ./run_load_test.sh                    # Uses all settings from locust.conf
#   ./run_load_test.sh --users 50         # Override users, use other settings from config
#   ./run_load_test.sh --users 50 --duration 300  # Override multiple settings
#
# Options (override locust.conf settings):
#   --users N          Number of concurrent users
#   --spawn-rate N     Users to spawn per second
#   --duration N        Test duration in seconds (e.g., 120 or 2m)
#   --host URL         Target host URL
#   --html FILE        HTML report file
#   --help             Show this help message

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONFIG_FILE="locust.conf"
LOCUSTFILE="locustfile.py"
LOCUST_ARGS=()

# Parse command line arguments (these will override config file settings)
while [[ $# -gt 0 ]]; do
    case $1 in
        --users)
            LOCUST_ARGS+=("--users" "$2")
            shift 2
            ;;
        --spawn-rate)
            LOCUST_ARGS+=("--spawn-rate" "$2")
            shift 2
            ;;
        --duration)
            LOCUST_ARGS+=("--run-time" "$2")
            shift 2
            ;;
        --host)
            LOCUST_ARGS+=("--host" "$2")
            shift 2
            ;;
        --html)
            LOCUST_ARGS+=("--html" "$2")
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "This script uses locust.conf for default settings."
            echo "Command-line options override config file values."
            echo ""
            echo "Options (override locust.conf):"
            echo "  --users N          Number of concurrent users"
            echo "  --spawn-rate N     Users to spawn per second"
            echo "  --duration N       Test duration (e.g., 120 or 2m)"
            echo "  --host URL         Target host URL"
            echo "  --html FILE        HTML report file"
            echo "  --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Use all settings from locust.conf"
            echo "  $0 --users 50                        # Override users only"
            echo "  $0 --users 50 --duration 300         # Override users and duration"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    echo "❌ Error: locust is not installed"
    echo "   Install it with: pip install locust"
    exit 1
fi

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Config file not found: $CONFIG_FILE"
    exit 1
fi

# Extract host for health check
# Note: We use multiple hosts (account service on 8000, transaction service on 8001)
# Each HttpUser class sets its own host, so we don't pass --host globally
HOST_FOR_CHECK="http://localhost:8000"
for i in "${!LOCUST_ARGS[@]}"; do
    if [ "${LOCUST_ARGS[$i]}" = "--host" ] && [ -n "${LOCUST_ARGS[$i+1]:-}" ]; then
        HOST_FOR_CHECK="${LOCUST_ARGS[$i+1]}"
        echo "⚠️  Warning: --host override detected. This may override class-level host settings."
        echo "   For multi-host tests, each HttpUser class should set its own host attribute."
        break
    fi
done

# Check if services are running
echo "🔍 Checking if services are running..."
if ! curl -s -f "${HOST_FOR_CHECK}/health" > /dev/null; then
    echo "❌ Error: Account service is not responding at ${HOST_FOR_CHECK}"
    echo "   Make sure services are running: docker-compose up"
    exit 1
fi

# Transaction service runs on port 8001
TRANSACTION_HOST="http://localhost:8001"
if ! curl -s -f "${TRANSACTION_HOST}/health" > /dev/null; then
    echo "⚠️  Warning: Transaction service is not responding at ${TRANSACTION_HOST}"
    echo "   Some tests may fail"
fi

# Run load test using config file with optional overrides
echo "🚀 Starting load test..."
echo "   Using config file: $CONFIG_FILE"
if [ ${#LOCUST_ARGS[@]} -gt 0 ]; then
    echo "   Overrides: ${LOCUST_ARGS[*]}"
fi
echo ""

# Build locust command - only add LOCUST_ARGS if array has elements
if [ ${#LOCUST_ARGS[@]} -gt 0 ]; then
    locust \
        -f "$LOCUSTFILE" \
        --config="$CONFIG_FILE" \
        "${LOCUST_ARGS[@]}"
else
    locust \
        -f "$LOCUSTFILE" \
        --config="$CONFIG_FILE"
fi

echo ""
echo "✅ Load test completed!"
echo "   Check locust.conf for report file locations"
echo "   Default: HTML report: load_test_report.html"
echo "   Default: CSV results: load_test_results_*.csv"


