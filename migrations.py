#!/usr/bin/env python3
"""
DynamoDB Init Script

This script reads table configurations from tables_config.json and creates
DynamoDB tables in the specified environment (local or AWS).

Usage:
    python migrations.py [--env local|aws] [--config tables_config.json]
"""
import json
import os
import sys
import argparse
import logging
from typing import Dict, List, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DynamoDBMigrator:
    def __init__(self, endpoint_url: str = None, region: str = "eu-central-1", iam_role: str = None):
        """
        Initialize the migrator with DynamoDB connection settings.
        
        Args:
            endpoint_url: DynamoDB endpoint URL (for local development)
            region: AWS region
            iam_role: IAM role ARN for AWS authentication
        """
        self.endpoint_url = endpoint_url
        self.region = region
        self.iam_role = iam_role
        
        # Configure boto3 client
        client_kwargs = {"region_name": region}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
        
        # AWS authentication logic (same as main.py)
        if iam_role:
            logger.info(f"Using IAM role: {iam_role}")
            sts_client = boto3.client("sts", region_name=region)
            assumed_role = sts_client.assume_role(
                RoleArn=iam_role,
                RoleSessionName="MigrationSession"
            )
            credentials = assumed_role["Credentials"]
            self.dynamodb = boto3.resource(
                "dynamodb",
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                **client_kwargs
            )
            self.client = boto3.client(
                "dynamodb",
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                **client_kwargs
            )
        else:
            logger.info("Using default AWS credentials or local DynamoDB")
            self.dynamodb = boto3.resource("dynamodb", **client_kwargs)
            self.client = boto3.client("dynamodb", **client_kwargs)
        
        logger.info(f"Connected to DynamoDB at: {endpoint_url or 'AWS'}")

    def load_table_config(self, config_file: str) -> List[Dict[str, Any]]:
        """
        Load table configurations from JSON file.
        
        Args:
            config_file: Path to the JSON configuration file
            
        Returns:
            List of table configurations
        """
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            tables = config.get("tables", [])
            logger.info(f"Loaded {len(tables)} table configurations from {config_file}")
            return tables
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            table = self.dynamodb.Table(table_name)
            table.load()
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            else:
                logger.error(f"Error checking if table {table_name} exists: {e}")
                return False

    def create_table(self, table_config: Dict[str, Any]) -> bool:
        """
        Create a DynamoDB table based on configuration.
        
        Args:
            table_config: Table configuration dictionary
            
        Returns:
            True if table created successfully, False otherwise
        """
        table_name = table_config["name"]
        
        # Check if table already exists
        if self.table_exists(table_name):
            logger.info(f"Table '{table_name}' already exists, skipping creation")
            return True
        
        try:
            # Convert key schema to proper DynamoDB API format
            key_schema = []
            for key in table_config["key_schema"]:
                key_schema.append({
                    "AttributeName": key["attribute_name"],
                    "KeyType": key["key_type"]
                })
            
            # Convert attribute definitions to proper DynamoDB API format
            attribute_definitions = []
            for attr in table_config["attributes"]:
                attribute_definitions.append({
                    "AttributeName": attr["name"],
                    "AttributeType": attr["type"]
                })
            
            # Prepare create table parameters
            create_params = {
                "TableName": table_name,
                "KeySchema": key_schema,
                "AttributeDefinitions": attribute_definitions,
                "BillingMode": table_config["billing_mode"]
            }
            
            # Add optional parameters if present
            if "global_secondary_indexes" in table_config:
                create_params["GlobalSecondaryIndexes"] = table_config["global_secondary_indexes"]
            
            if "local_secondary_indexes" in table_config:
                create_params["LocalSecondaryIndexes"] = table_config["local_secondary_indexes"]
            
            # Create the table
            logger.info(f"Creating table '{table_name}'...")
            self.client.create_table(**create_params)
            
            # Wait for table to be created
            waiter = self.client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            logger.info(f"Successfully created table '{table_name}'")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceInUseException':
                logger.warning(f"Table '{table_name}' is being created by another process")
                return True
            else:
                logger.error(f"Failed to create table '{table_name}': {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error creating table '{table_name}': {e}")
            return False

    def list_tables(self) -> List[str]:
        """
        List all tables in the DynamoDB instance.
        
        Returns:
            List of table names
        """
        try:
            response = self.client.list_tables()
            return response.get("TableNames", [])
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return []

    def run_migrations(self, config_file: str) -> bool:
        """
        Run all migrations from the configuration file.
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            True if all migrations succeeded, False otherwise
        """
        try:
            # Load table configurations
            table_configs = self.load_table_config(config_file)
            
            if not table_configs:
                logger.warning("No table configurations found")
                return True
            
            # Create each table
            success_count = 0
            for table_config in table_configs:
                if self.create_table(table_config):
                    success_count += 1
            
            logger.info(f"Migration completed: {success_count}/{len(table_configs)} tables created successfully")
            return success_count == len(table_configs)
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

def main():
    """Main function to run migrations."""
    parser = argparse.ArgumentParser(description="DynamoDB Migration Script")
    parser.add_argument("--env", choices=["local", "aws"], default="aws",
                       help="Environment to run migrations in (default: aws)")
    parser.add_argument("--config", default="tables_config.json",
                       help="Path to table configuration file (default: tables_config.json)")
    parser.add_argument("--endpoint", default=None,
                       help="DynamoDB endpoint URL (default: AWS endpoint)")
    parser.add_argument("--region", default="eu-central-1",
                       help="AWS region (default: eu-central-1)")
    parser.add_argument("--iam-role", default=None,
                       help="IAM role ARN for AWS authentication")
    parser.add_argument("--list", action="store_true",
                       help="List existing tables and exit")
    
    args = parser.parse_args()
    
    # Load environment variables (same as main.py)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Get IAM role from environment if not provided
    iam_role = args.iam_role or os.environ.get("IAM_ROLE")
    
    try:
        # Initialize migrator
        endpoint_url = args.endpoint if args.env == "local" else None
        migrator = DynamoDBMigrator(endpoint_url=endpoint_url, region=args.region, iam_role=iam_role)
        
        # List tables if requested
        if args.list:
            tables = migrator.list_tables()
            if tables:
                logger.info("Existing tables:")
                for table in tables:
                    logger.info(f"  - {table}")
            else:
                logger.info("No tables found")
            return
        
        # Run migrations
        success = migrator.run_migrations(args.config)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Migration script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 