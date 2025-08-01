#!/bin/bash -e

# Check if DynamoDB container is already running
if docker ps -q -f name=dynamodb-local | grep -q .; then
    echo "Local DynamoDB environment is already running!"
    echo ""
    echo "What would you like to do?"
    echo "1) Destroy and re-create environment"
    echo "2) Re-use existing environment"
    echo "3) Exit"
    echo ""
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            echo "Destroying existing environment..."
            ./stop_local.sh
            echo "Re-creating environment..."
            ;;
        2)
            echo "Re-using existing environment..."
            # Set environment variables for existing environment
            export DYNAMODB_ENDPOINT_URL="http://localhost:8000"
            export DYNAMODB_TABLE="users_birthdays"
            export AWS_REGION="eu-central-1"
            export API_PORT=${API_PORT:-8001}
            
            echo "Starting FastAPI application..."
            echo "Application will be available at: http://localhost:${API_PORT:-8001}"
            echo "Press Ctrl+C to stop the application"
            
            # Start the Python application
            python main.py
            exit 0
            ;;
        3)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting..."
            exit 1
            ;;
    esac
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
python migrations.py --env local --endpoint http://localhost:8000

echo "Starting FastAPI application..."
echo "Application will be available at: http://localhost:${API_PORT:-8001}"
echo "Press Ctrl+C to stop the application"

# Start the Python application
python main.py 

