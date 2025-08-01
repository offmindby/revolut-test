# Requirements: fastapi, uvicorn, boto3, python-dotenv
# Run with: python main.py
"""
FastAPI web application with two endpoints:
- PUT /hello/<username>: Set a date of birth for a username (body: {"dateOfBirth": "YYYY-MM-DD"})
- GET /hello/<username>: Get the date of birth for a username, or a default greeting if not set

Uses Pydantic for input validation. Stores data in DynamoDB.
"""
import os
import logging
from fastapi import FastAPI, Path, HTTPException, Response
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime
import boto3
from botocore.exceptions import ClientError
from fastapi.concurrency import run_in_threadpool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "users_birthdays")
IAM_ROLE = os.environ.get("IAM_ROLE")
AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")
DYNAMODB_ENDPOINT_URL = os.environ.get("DYNAMODB_ENDPOINT_URL")
API_PORT = int(os.environ.get("API_PORT", "8001"))

# Debug logging
logger.info(f"FastAPI Configuration:")
logger.info(f"  Port: {API_PORT}")
logger.info(f"DynamoDB Configuration:")
logger.info(f"  Table: {DYNAMODB_TABLE}")
logger.info(f"  Region: {AWS_REGION}")
logger.info(f"  Endpoint URL: {DYNAMODB_ENDPOINT_URL}")
logger.info(f"  IAM Role: {IAM_ROLE}")

# AWS authentication logic
boto3_resource_kwargs = {"region_name": AWS_REGION}
if DYNAMODB_ENDPOINT_URL:
    boto3_resource_kwargs["endpoint_url"] = DYNAMODB_ENDPOINT_URL
    logger.info(f"Using local DynamoDB endpoint: {DYNAMODB_ENDPOINT_URL}")

if IAM_ROLE:
    logger.info(f"Using IAM role: {IAM_ROLE}")
    sts_client = boto3.client("sts", region_name=AWS_REGION)
    assumed_role = sts_client.assume_role(
        RoleArn=IAM_ROLE,
        RoleSessionName="FastAPISession"
    )
    credentials = assumed_role["Credentials"]
    dynamodb = boto3.resource(
        "dynamodb",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        **boto3_resource_kwargs
    )
else:
    logger.info("Using default AWS credentials or local DynamoDB")
    dynamodb = boto3.resource("dynamodb", **boto3_resource_kwargs)

table = dynamodb.Table(DYNAMODB_TABLE)
logger.info(f"Initialized DynamoDB table: {DYNAMODB_TABLE}")

# Test table connection
try:
    table.load()
    logger.info("Successfully connected to DynamoDB table")
except ClientError as e:
    logger.error(f"Failed to connect to DynamoDB table: {e}")
    if e.response['Error']['Code'] == 'ResourceNotFoundException':
        logger.error(f"Table '{DYNAMODB_TABLE}' does not exist!")
    elif e.response['Error']['Code'] == 'UnrecognizedClientException':
        logger.error("Invalid endpoint URL or connection issue")
    else:
        logger.error(f"Unexpected error: {e}")
except Exception as e:
    logger.error(f"Connection error to DynamoDB: {e}")
    logger.warning("Application will continue but DynamoDB operations may fail")

app = FastAPI()

class HelloRequest(BaseModel):
    dateOfBirth: date

    @field_validator("dateOfBirth")
    def date_must_be_before_today(cls, v):
        if v >= date.today():
            raise ValueError("dateOfBirth must be a date before today.")
        return v

async def store_birthday(username: str, date_of_birth: str):
    logger.info(f"Storing birthday for user '{username}': {date_of_birth}")
    def _put():
        try:
            table.put_item(Item={"username": username, "dateOfBirth": date_of_birth})
            logger.info(f"Successfully stored birthday for '{username}'")
        except ClientError as e:
            logger.error(f"Failed to store birthday for '{username}': {e}")
            raise HTTPException(status_code=500, detail="Failed to store birthday")
        except Exception as e:
            logger.error(f"Connection error while storing birthday for '{username}': {e}")
            raise HTTPException(status_code=503, detail="Database connection error")
    await run_in_threadpool(_put)

async def get_birthday(username: str) -> Optional[str]:
    logger.info(f"Getting birthday for user '{username}'")
    def _get():
        try:
            response = table.get_item(Key={"username": username})
            item = response.get("Item", {})
            date_of_birth = item.get("dateOfBirth")
            if date_of_birth:
                logger.info(f"Found birthday for '{username}': {date_of_birth}")
            else:
                logger.info(f"No birthday found for '{username}'")
            return date_of_birth
        except ClientError as e:
            logger.error(f"Failed to get birthday for '{username}': {e}")
            return None
        except Exception as e:
            logger.error(f"Connection error while getting birthday for '{username}': {e}")
            return None
    return await run_in_threadpool(_get)

def calculate_days_until_birthday(birth_date_str: str) -> int:
    """Calculate days until next birthday."""
    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
    today = date.today()
    
    # Create this year's birthday
    this_year_birthday = birth_date.replace(year=today.year)
    
    # If this year's birthday has passed, calculate for next year
    if this_year_birthday < today:
        next_birthday = birth_date.replace(year=today.year + 1)
    else:
        next_birthday = this_year_birthday
    
    # Calculate days difference
    days_until = (next_birthday - today).days
    return days_until

@app.put("/hello/{username}")
async def put_hello(
    username: str = Path(..., min_length=1, max_length=50, pattern=r"^[A-Za-z]+$"),
    body: HelloRequest = None
):
    if not body:
        raise HTTPException(status_code=422, detail="Request body required.")
    await store_birthday(username, body.dateOfBirth.isoformat())
    return Response(status_code=204)

@app.get("/hello/{username}")
async def get_hello(username: str = Path(..., min_length=1, max_length=50, pattern=r"^[A-Za-z]+$")):
    date_of_birth = await get_birthday(username)
    if date_of_birth:
        days_until_birthday = calculate_days_until_birthday(date_of_birth)
        
        if days_until_birthday == 0:
            return {"message": f"Hello, {username}! Happy birthday!"}
        else:
            day_text = "day" if days_until_birthday == 1 else "days"
            return {"message": f"Hello, {username}! Your birthday is in {days_until_birthday} {day_text}"}
    
    return {"message": "user not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=API_PORT, reload=True)
