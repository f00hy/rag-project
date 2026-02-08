from os import getenv
from boto3 import client

obj_store_client = client(
    service_name="s3",
    endpoint_url=f"https://{getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
    aws_access_key_id=getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto",
)
