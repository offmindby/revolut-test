#!/bin/bash

echo "Stopping local DynamoDB environment..."

# Stop and remove the DynamoDB container
if docker ps -q -f name=dynamodb-local | grep -q .; then
    echo "Stopping DynamoDB container..."
    docker stop dynamodb-local
    docker rm dynamodb-local
    echo "DynamoDB container stopped and removed"
else
    echo "DynamoDB container not running"
fi

# Remove any dangling containers with similar names
if docker ps -a -q -f name=dynamodb | grep -q .; then
    echo "Cleaning up any other DynamoDB containers..."
    docker ps -a -q -f name=dynamodb | xargs -r docker rm -f
fi

# Unset environment variables
unset DYNAMODB_ENDPOINT_URL
unset DYNAMODB_TABLE
unset AWS_REGION
unset API_PORT

echo "Local environment stopped successfully!"
echo "Environment variables cleared:"
echo "  - DYNAMODB_ENDPOINT_URL"
echo "  - DYNAMODB_TABLE" 
echo "  - AWS_REGION"
echo "  - API_PORT" 