import json

import boto3

from app.config import settings


def enqueue_audit_job(job_id: str, intake_data: dict) -> str:
    sqs = boto3.client("sqs", region_name=settings.aws_region)
    response = sqs.send_message(
        QueueUrl=settings.audit_queue_url,
        MessageBody=json.dumps({"job_id": job_id, "intake_data": intake_data}),
        MessageGroupId="audit-jobs",
        MessageDeduplicationId=job_id,
    )
    return response["MessageId"]
