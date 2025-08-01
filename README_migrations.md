# DynamoDB Init Script

This script is supposed to create DynamoDB tables if absent. As a key-value DB DynamoDB do not need classic migratiopns, however, we need to create neede tables.
Also, some specific indices and attributes may be initiated by the script. 

## Files

- `migrations.py` - Main migration script
- `tables_config.json` - Table configuration file
- `README_migrations.md` - This documentation

## Table Configuration

The `tables_config.json` file defines the structure of DynamoDB tables:

```json
{
  "tables": [
    {
      "name": "users_birthdays",
      "billing_mode": "PAY_PER_REQUEST",
      "attributes": [
        {
          "name": "username",
          "type": "S"
        }
      ],
      "key_schema": [
        {
          "attribute_name": "username",
          "key_type": "HASH"
        }
      ],
      "description": "Table to store user birthdays"
    }
  ]
}
```

### Configuration Fields

- `name`: Table name
- `billing_mode`: "PAY_PER_REQUEST" or "PROVISIONED"
- `attributes`: List of attribute definitions (name and type)
- `key_schema`: Primary key definition (HASH = partition key, RANGE = sort key)
- `description`: Optional description of the table

## Usage

### List Existing Tables

```bash
# List tables in local DynamoDB
python migrations.py --env local --list

# List tables in AWS
python migrations.py --env aws --list
```

### Create Tables

```bash
# Create tables in local DynamoDB
python migrations.py --env local

# Create tables in AWS
python migrations.py --env aws

# Use custom configuration file
python migrations.py --env local --config my_tables.json

# Use custom endpoint
python migrations.py --env local --endpoint http://localhost:8000
```

### Command Line Options

- `--env`: Environment (local|aws, default: local)
- `--config`: Configuration file path (default: tables_config.json)
- `--endpoint`: DynamoDB endpoint URL (default: http://localhost:8000)
- `--region`: AWS region (default: us-east-1)
- `--list`: List existing tables and exit

## Adding New Tables

To add a new table:

1. Add the table configuration to `tables_config.json`
2. Run the migration script

Example for a new table with composite key:

```json
{
  "name": "user_sessions",
  "billing_mode": "PAY_PER_REQUEST",
  "attributes": [
    {
      "name": "user_id",
      "type": "S"
    },
    {
      "name": "session_id",
      "type": "S"
    }
  ],
  "key_schema": [
    {
      "attribute_name": "user_id",
      "key_type": "HASH"
    },
    {
      "attribute_name": "session_id",
      "key_type": "RANGE"
    }
  ],
  "description": "Table to store user sessions"
}
```

## Error Handling

The migration script handles various error scenarios:

- **Table already exists**: Skips creation and logs info
- **Connection errors**: Logs error and continues
- **Invalid configuration**: Logs error and exits
- **AWS credential issues**: Provides helpful error messages

## Local Development

For local development, make sure your DynamoDB Local is running:

```bash
docker run -p 8000:8000 amazon/dynamodb-local
```

Then run migrations:

```bash
python migrations.py --env local
``` 