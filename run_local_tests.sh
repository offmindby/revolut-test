#!/bin/bash -e

echo "Running local tests..."

# Install required packages
echo "Installing required packages..."
pip install -r requirements.txt
pip install -r requirements-test.txt

# Function to check if a port is in use
check_port() {
    local port=$1
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        return 0  # Port is in use
    elif ss -tuln 2>/dev/null | grep -q ":$port "; then
        return 0  # Port is in use (alternative method)
    else
        return 1  # Port is not in use
    fi
}

# Function to check if FastAPI app is running
check_fastapi_running() {
    # Get API_PORT from environment or default to 8001
    local api_port=${API_PORT:-8001}
    if check_port $api_port; then
        # Try to make a request to the FastAPI app
        if curl -s http://localhost:$api_port/docs >/dev/null 2>&1; then
            return 0  # FastAPI is running and responding
        fi
    fi
    return 1  # FastAPI is not running
}

# Check if DynamoDB container is already running
DYNAMODB_RUNNING=false
if docker ps -q -f name=dynamodb-local | grep -q .; then
    DYNAMODB_RUNNING=true
fi

# Check if FastAPI application is running
FASTAPI_RUNNING=false
if check_fastapi_running; then
    FASTAPI_RUNNING=true
fi

# Display current status
echo "Current environment status:"
echo "  DynamoDB container: $([ "$DYNAMODB_RUNNING" = true ] && echo "RUNNING" || echo "NOT RUNNING")"
echo "  FastAPI application: $([ "$FASTAPI_RUNNING" = true ] && echo "RUNNING" || echo "NOT RUNNING")"
echo ""

# If both are running, ask user what to do
if [ "$DYNAMODB_RUNNING" = true ] && [ "$FASTAPI_RUNNING" = true ]; then
    echo "Both DynamoDB and FastAPI are already running!"
    echo ""
    echo "What would you like to do?"
    echo "1) Run tests against existing environment"
    echo "2) Stop FastAPI and run tests (keep DynamoDB)"
    echo "3) Destroy and re-create entire environment"
    echo "4) Exit"
    echo ""
    read -p "Enter your choice (1-4): " choice
    
    case $choice in
        1)
            echo "Running tests against existing environment..."
            # Set environment variables for existing environment
            export DYNAMODB_ENDPOINT_URL="http://localhost:8000"
            export DYNAMODB_TABLE="users_birthdays"
            export AWS_REGION="eu-central-1"
            export API_PORT=${API_PORT:-8001}
            
            # Run tests
            echo "Running tests..."
            python -m pytest test_main.py -v --tb=short
            TEST_EXIT_CODE=$?
            
            # Exit with test result
            if [ $TEST_EXIT_CODE -eq 0 ]; then
                echo "All tests passed!"
                exit 0
            else
                echo "Some tests failed!"
                exit $TEST_EXIT_CODE
            fi
            ;;
        2)
            echo "Stopping FastAPI application..."
            # Find and kill the Python process running main.py
            pkill -f "python.*main.py" || echo "No FastAPI process found to stop"
            sleep 2
            echo "FastAPI stopped. Running tests..."
            ;;
        3)
            echo "Destroying existing environment..."
            ./stop_local.sh
            echo "Re-creating environment..."
            ;;
        4)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting..."
            exit 1
            ;;
    esac
# If only DynamoDB is running
elif [ "$DYNAMODB_RUNNING" = true ] && [ "$FASTAPI_RUNNING" = false ]; then
    echo "DynamoDB is running but FastAPI is not!"
    echo ""
    echo "What would you like to do?"
    echo "1) Run tests (DynamoDB only, no FastAPI needed for tests)"
    echo "2) Start FastAPI and run tests"
    echo "3) Destroy and re-create environment"
    echo "4) Exit"
    echo ""
    read -p "Enter your choice (1-4): " choice
    
    case $choice in
        1)
            echo "Running tests with existing DynamoDB..."
            # Set environment variables for existing environment
            export DYNAMODB_ENDPOINT_URL="http://localhost:8000"
            export DYNAMODB_TABLE="users_birthdays"
            export AWS_REGION="eu-central-1"
            export API_PORT=${API_PORT:-8001}
            
            # Run tests
            echo "Running tests..."
            python -m pytest test_main.py -v --tb=short
            TEST_EXIT_CODE=$?
            
            # Exit with test result
            if [ $TEST_EXIT_CODE -eq 0 ]; then
                echo "All tests passed!"
                exit 0
            else
                echo "Some tests failed!"
                exit $TEST_EXIT_CODE
            fi
            ;;
        2)
            echo "Starting FastAPI application..."
            # Start FastAPI in background
            python main.py &
            FASTAPI_PID=$!
            echo "FastAPI started with PID: $FASTAPI_PID"
            
            # Wait for FastAPI to be ready
            echo "Waiting for FastAPI to be ready..."
            sleep 5
            
            # Set environment variables
            export DYNAMODB_ENDPOINT_URL="http://localhost:8000"
            export DYNAMODB_TABLE="users_birthdays"
            export AWS_REGION="eu-central-1"
            export API_PORT=${API_PORT:-8001}
            
            # Run tests
            echo "Running tests..."
            python -m pytest test_main.py -v --tb=short
            TEST_EXIT_CODE=$?
            
            # Stop FastAPI
            echo "Stopping FastAPI..."
            kill $FASTAPI_PID 2>/dev/null || true
            
            # Exit with test result
            if [ $TEST_EXIT_CODE -eq 0 ]; then
                echo "All tests passed!"
                exit 0
            else
                echo "Some tests failed!"
                exit $TEST_EXIT_CODE
            fi
            ;;
        3)
            echo "Destroying existing environment..."
            ./stop_local.sh
            echo "Re-creating environment..."
            ;;
        4)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting..."
            exit 1
            ;;
    esac
# If only FastAPI is running (unlikely but possible)
elif [ "$DYNAMODB_RUNNING" = false ] && [ "$FASTAPI_RUNNING" = true ]; then
    echo "FastAPI is running but DynamoDB is not!"
    echo "This is an unusual state. Starting fresh environment..."
    # Kill FastAPI
    pkill -f "python.*main.py" || echo "No FastAPI process found to stop"
    sleep 2
# If neither is running, start fresh
else
    echo "No environment is running. Starting fresh..."
fi

# Start local DynamoDB
echo "Starting local DynamoDB..."
docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local

# Wait for DynamoDB to be ready
echo "Waiting for DynamoDB to be ready..."
sleep 5

# Set environment variables
export DYNAMODB_ENDPOINT_URL="http://localhost:8000"
export DYNAMODB_TABLE="users_birthdays"
export AWS_REGION="eu-central-1"
export API_PORT=${API_PORT:-8001}

# Create the table using Python migration script
echo "Creating DynamoDB table using migration script..."
export AWS_ACCESS_KEY_ID="dummy"
export AWS_SECRET_ACCESS_KEY="dummy"
python migrations.py --env local --endpoint http://localhost:8000

# Run tests
echo "Running tests..."
python -m pytest test_main.py -v --tb=short
TEST_EXIT_CODE=$?

# Stop local environment
echo "Stopping local environment..."
./stop_local.sh

# Exit with test result
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "All tests passed!"
    exit 0
else
    echo "Some tests failed!"
    exit $TEST_EXIT_CODE
fi 