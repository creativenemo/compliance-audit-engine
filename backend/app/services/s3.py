import boto3
from botocore.exceptions import ClientError

from app.config import settings


def get_pdf_signed_url(job_id: str, expiry_seconds: int = 3600) -> str | None:
    s3 = boto3.client("s3", region_name=settings.aws_region)
    key = f"pdfs/{job_id}.pdf"
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.pdfs_bucket, "Key": key},
            ExpiresIn=expiry_seconds,
        )
        return url
    except ClientError:
        return None


def get_index_json(key: str) -> bytes | None:
    s3 = boto3.client("s3", region_name=settings.aws_region)
    try:
        response = s3.get_object(Bucket=settings.indexes_bucket, Key=key)
        return response["Body"].read()
    except ClientError:
        return None


def put_index_json(key: str, data: bytes) -> None:
    s3 = boto3.client("s3", region_name=settings.aws_region)
    s3.put_object(Bucket=settings.indexes_bucket, Key=key, Body=data, ContentType="application/json")
