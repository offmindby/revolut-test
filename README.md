# Revolut Birthday API

A FastAPI web application that manages user birthdays with DynamoDB storage.

## Features

- **PUT /hello/{username}**: Set a date of birth for a username
- **GET /hello/{username}**: Get birthday information and days until next birthday
- **DynamoDB Integration**: Stores user birthday data in DynamoDB
- **Local Development**: Includes Docker-based local DynamoDB setup
- **Comprehensive Testing**: Full test suite with pytest



## System Requirements

The application was developed and tested in the following environment:

- **Operating System**: Ubuntu 22.04 LTS
- **Python Version**: Python 3.10
- **Packages installed**: Docker, python-pip, git

> It is recommended to use the specified Python version and a Linux-based system (or Docker) for compatibility with local setup and testing scripts.

## Environment Configuration

Make sure all the requirements are met. See [System Requirements](System Requirements) section
The application uses environment variables for configuration. You can set these up in the file .env.
See file env.example

### Quick Setup

```bash
# Copy the example environment file
cp env.example .env

# Edit .env file to configure your environment
# See the sections below for specific configurations
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | `8001` | Port for the FastAPI application |
| `DYNAMODB_TABLE` | `users_birthdays` | DynamoDB table name |
| `AWS_REGION` | `eu-central-1` | AWS region |
| `DYNAMODB_ENDPOINT_URL` | `http://localhost:8000` | DynamoDB endpoint URL |
| `IAM_ROLE` | (optional) | IAM role ARN for AWS authentication, should only be used with real AWS endpoints |

### Environment Configuration for Different Deployments

#### Local Development Environment

For local development with Docker DynamoDB:

```env
# FastAPI Configuration - the port to listen to
API_PORT=8001

# DynamoDB Configuration
DYNAMODB_TABLE=users_birthdays
AWS_REGION=eu-central-1
DYNAMODB_ENDPOINT_URL=http://localhost:8000
```

**Local Environment Setup:**
- **Set `DYNAMODB_ENDPOINT_URL=http://localhost:8000`** - Points to local Docker DynamoDB
- **Do NOT set `IAM_ROLE`** - Local development uses default AWS credentials or no authentication
- **Set `AWS_REGION`** - Can be any region for local development
- **Set `DYNAMODB_TABLE`** - Table name for local DynamoDB

#### AWS Environment

For AWS deployment with real DynamoDB:

```env
# FastAPI Configuration - the port to listen to
API_PORT=8001

# DynamoDB Configuration
DYNAMODB_TABLE=users_birthdays
AWS_REGION=eu-central-1

# For AWS deployment, either:
# Option 1: Use IAM Role (if you have a pre-configured role with appropriate permissions)
IAM_ROLE=arn:aws:iam::123456789012:role/your-dynamodb-role

# Option 2: Use default AWS credentials (for Lambda, etc.)
# IAM_ROLE=

# DYNAMODB_ENDPOINT_URL should NOT be set for AWS
# DYNAMODB_ENDPOINT_URL=
```

**AWS Environment Setup:**
- **Do NOT set `DYNAMODB_ENDPOINT_URL`** - Uses AWS DynamoDB service automatically
- **Set `IAM_ROLE`** (if using EC2/ECS and you have a pre-configured role) - Role must have needed permissions
- **Set `AWS_REGION`** - Must match your DynamoDB table region
- **Set `DYNAMODB_TABLE`** - Must match your AWS DynamoDB table name

### Required IAM Permissions

For AWS deployments, your IAM execution role needs the following DynamoDB permissions:

**Note:** If you plan to use `IAM_ROLE` environment variable, you must create and configure the IAM role beforehand with the permissions listed below.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:DescribeTable"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/users_birthdays"
        }
    ]
}
```

### DynamoDB Table Structure

The application expects a DynamoDB table with the following structure:

- **Table Name**: `users_birthdays` (or value of `DYNAMODB_TABLE`)
- **Primary Key**: `username` (String)
- **Attributes**:
  - `username` (String) - Primary key
  - `dateOfBirth` (String) - Date in YYYY-MM-DD format

**Example table creation (AWS CLI):**
```bash
aws dynamodb create-table \
    --table-name users_birthdays \
    --attribute-definitions AttributeName=username,AttributeType=S \
    --key-schema AttributeName=username,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region eu-central-1
```

## Infrastructure Setup with Terraform

The `terraform/` directory contains infrastructure as code to set up the required AWS resources:

- **IAM Role**: Application role for AWS resource access
- **IAM Policy**: Grants access to AWS resources for the application

### Terraform Configuration

The Terraform configuration creates:
- An application IAM role that can be assumed by EC2 or Lambda services
- An IAM policy allowing full DynamoDB access to tables matching a prefix
- Configurable variables for AWS region, table prefix, and role name

### Quick Setup

1. **Initialize Terraform:**
   ```bash
   cd terraform
   terraform init
   ```

2. **Plan the deployment:**
   ```bash
   terraform plan
   ```

3. **Apply the configuration:**
   ```bash
   terraform apply
   ```

4. **Get the IAM Role ARN:**
   ```bash
   terraform output iam_role_arn
   ```

### Using the IAM Role ARN

After deploying with Terraform, use the `iam_role_arn` output in your `.env` file:

```env
# Use the ARN from terraform output
IAM_ROLE=arn:aws:iam::123456789012:role/application_role
```

### Terraform Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | `eu-central-1` | AWS region for resources |
| `dynamodb_table_prefix` | `users_` | Prefix for DynamoDB tables the role can access |
| `iam_role_name` | `application_role` | Name of the IAM role |

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

2. Set up environment configuration:
```bash
cp env.example .env
# Edit .env file according to your deployment environment
```

## Usage

### Local Development

Start the local environment (DynamoDB + FastAPI):
```bash
./start_local.sh
```

The application will be available at `http://localhost:8001` (or the port specified in `API_PORT`).

### Running Tests

Run the test suite:
```bash
./run_local_tests.sh
```

The test script will:
- Detect if DynamoDB and/or FastAPI are already running
- Provide options to reuse existing environment or start fresh
- Run comprehensive tests against the API

### Stopping the Environment

Stop the local environment:
```bash
./stop_local.sh
```

## API Endpoints

### PUT /hello/{username}

Set a user's date of birth.

**Request:**
```json
{
  "dateOfBirth": "1990-05-15"
}
```

**Response:** 204 No Content

### GET /hello/{username}

Get birthday information for a user.

**Response:**
```json
{
  "message": "Hello, john! Your birthday is in 5 days"
}
```

Or if birthday is today:
```json
{
  "message": "Hello, john! Happy birthday!"
}
```

Or if user not found:
```json
{
  "message": "user not found"
}
```

## Development

### Project Structure

- `main.py` - FastAPI application
- `test_main.py` - Comprehensive test suite
- `migrations.py` - DynamoDB table creation script. See [README_migrations.md](README_migrations.md) for details.
- `start_local.sh` - Start local development environment
- `run_local_tests.sh` - Run tests with environment management
- `stop_local.sh` - Stop local environment
- `setup_env.sh` - Set up environment configuration

## Testing

The test suite includes:
- Input validation tests
- Edge case testing
- Error scenario testing
- Birthday calculation logic
- API endpoint testing

### Running Tests

**Option 1: Using the bash script (recommended)**
```bash
./run_local_tests.sh
```

The `run_local_tests.sh` script:
- Automatically detects if DynamoDB container and/or FastAPI application are running
- Provides options to reuse existing environment or start fresh
- Sets up the test environment (DynamoDB + table creation)
- Runs comprehensive tests against the API
- Cleans up the environment after tests complete

**Option 2: Manual testing**
```bash
python -m pytest test_main.py -v
```

*Note: Manual testing requires DynamoDB to be running and properly configured.*
