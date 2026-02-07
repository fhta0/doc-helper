#!/bin/bash
#
# Script to run backend tests
#

set -e  # Exit on error

echo "========================================="
echo "Running Backend Test Suite"
echo "========================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "pytest not found. Installing test dependencies..."
    pip install -r requirements.txt
fi

# Parse command line arguments
TEST_PATH="tests/"
MARKERS=""
VERBOSE="-v"
COVERAGE="--cov=app --cov-report=html --cov-report=term-missing"

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            MARKERS="-m unit"
            shift
            ;;
        --integration)
            MARKERS="-m integration"
            shift
            ;;
        --service)
            MARKERS="-m service"
            shift
            ;;
        --api)
            MARKERS="-m api"
            shift
            ;;
        --model)
            MARKERS="-m model"
            shift
            ;;
        --no-cov)
            COVERAGE=""
            shift
            ;;
        --quick)
            COVERAGE=""
            VERBOSE=""
            shift
            ;;
        *)
            TEST_PATH="$1"
            shift
            ;;
    esac
done

echo "Running tests from: $TEST_PATH"
if [ -n "$MARKERS" ]; then
    echo "With markers: $MARKERS"
fi
echo ""

# Run tests
pytest $TEST_PATH $MARKERS $VERBOSE $COVERAGE

# Check exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "========================================="
    echo "All tests passed!"
    echo "========================================="
else
    echo "========================================="
    echo "Some tests failed. Exit code: $EXIT_CODE"
    echo "========================================="
fi

# Display coverage report location if generated
if [ -n "$COVERAGE" ] && [ -d "htmlcov" ]; then
    echo ""
    echo "Coverage report generated: htmlcov/index.html"
    echo "Open it with: xdg-open htmlcov/index.html"
fi

exit $EXIT_CODE
