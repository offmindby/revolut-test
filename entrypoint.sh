#!/bin/bash

# Exit on any error
set -e

echo "Starting application initialization..."

# Detect environment based on ENVIRONMENT variable (default: aws)
# Use ENVIRONMENT=local for local development, ENVIRONMENT=aws for AWS
ENVIRONMENT=${ENVIRONMENT:-aws}

if [ "$ENVIRONMENT" = "local" ]; then
    echo "Running in local environment (ENVIRONMENT=local)"
    MIGRATION_ENV="local"
    MIGRATION_ARGS="--env local"
    
    # Add endpoint if specified
    if [ -n "$DYNAMODB_ENDPOINT_URL" ]; then
        MIGRATION_ARGS="$MIGRATION_ARGS --endpoint $DYNAMODB_ENDPOINT_URL"
        echo "Using custom DynamoDB endpoint: $DYNAMODB_ENDPOINT_URL"
    fi
    
    # Set dummy AWS credentials for local DynamoDB (boto3 requires them even for local endpoint)
    if [ -z "$AWS_ACCESS_KEY_ID" ]; then
        export AWS_ACCESS_KEY_ID="dummy"
        export AWS_SECRET_ACCESS_KEY="dummy"
        echo "Set dummy AWS credentials for local development"
    fi
else
    echo "Running in AWS environment (ENVIRONMENT=$ENVIRONMENT)"
    MIGRATION_ENV="aws"
    MIGRATION_ARGS="--env aws"
    
    # Add endpoint if specified (for custom AWS endpoints like VPC endpoints)
    if [ -n "$DYNAMODB_ENDPOINT_URL" ]; then
        MIGRATION_ARGS="$MIGRATION_ARGS --endpoint $DYNAMODB_ENDPOINT_URL"
        echo "Using custom DynamoDB endpoint: $DYNAMODB_ENDPOINT_URL"
    fi
fi

# Add region if specified
if [ -n "$AWS_REGION" ]; then
    MIGRATION_ARGS="$MIGRATION_ARGS --region $AWS_REGION"
fi

# Add IAM role if specified
if [ -n "$IAM_ROLE" ]; then
    MIGRATION_ARGS="$MIGRATION_ARGS --iam-role $IAM_ROLE"
fi

# Run DynamoDB migrations
echo "Running DynamoDB migrations for $MIGRATION_ENV environment..."
echo "Migration command: python migrations.py $MIGRATION_ARGS"
python migrations.py $MIGRATION_ARGS

# Check if migrations were successful
if [ $? -eq 0 ]; then
    echo "Migrations completed successfully!"
else
    echo "Migration failed! Exiting..."
    exit 1
fi

# Start the FastAPI application
echo "Starting FastAPI application..."
exec python main.py
