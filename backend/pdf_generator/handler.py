"""
PDF Generator Lambda — Sprint 5

Triggered via SQS or direct invocation after a job reaches COMPLETE status.
Uses Playwright (Chromium) to render the report page as a PDF and uploads
to S3: pdfs/{job_id}.pdf

Environment variables:
  FRONTEND_BASE_URL  — base URL of the deployed frontend (e.g. https://app.example.com)
  PDFS_BUCKET        — S3 bucket for generated PDFs
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import tempfile
from typing import Any

import boto3
from playwright.async_api import async_playwright

from app.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--single-process",
]
_FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "http://localhost:3000")


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda entry point. Accepts direct invocation or SQS record."""
    records = event.get("Records", [])
    if records:
        import json
        for record in records:
            body = json.loads(record["body"])
            job_id = body["job_id"]
            asyncio.run(_generate_pdf(job_id))
    elif "job_id" in event:
        asyncio.run(_generate_pdf(event["job_id"]))
    else:
        logger.error("No job_id in event: %s", event)
        return {"statusCode": 400, "body": "Missing job_id"}

    return {"statusCode": 200}


async def _generate_pdf(job_id: str) -> None:
    report_url = f"{_FRONTEND_BASE_URL}/audit/{job_id}/report"
    logger.info("[%s] Generating PDF from %s", job_id, report_url)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=_BROWSER_ARGS)
        try:
            page = await browser.new_page()
            # Set viewport to standard letter width
            await page.set_viewport_size({"width": 1280, "height": 1024})

            # Navigate and wait for report content to render
            await page.goto(report_url, wait_until="networkidle", timeout=45_000)

            # Wait for the main report container if present
            with contextlib.suppress(Exception):
                await page.wait_for_selector("[data-testid='report-content'], main, #report-root", timeout=15_000)

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = tmp.name

            await page.pdf(
                path=tmp_path,
                format="Letter",
                print_background=True,
                margin={"top": "0.5in", "bottom": "0.5in", "left": "0.5in", "right": "0.5in"},
            )

            with open(tmp_path, "rb") as f:
                pdf_bytes = f.read()

        finally:
            await browser.close()

    _upload_to_s3(job_id, pdf_bytes)
    logger.info("[%s] PDF uploaded (%d bytes)", job_id, len(pdf_bytes))


def _upload_to_s3(job_id: str, pdf_bytes: bytes) -> None:
    s3 = boto3.client("s3", region_name=settings.aws_region)
    key = f"pdfs/{job_id}.pdf"
    s3.put_object(
        Bucket=settings.pdfs_bucket,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
        # 90-day retention via S3 lifecycle rule on the pdfs bucket
    )
    logger.info("Uploaded s3://%s/%s", settings.pdfs_bucket, key)
