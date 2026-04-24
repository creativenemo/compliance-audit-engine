from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AWS
    aws_region: str = "us-east-1"
    jobs_table_name: str = "compliance-jobs"
    audit_queue_url: str = ""
    indexes_bucket: str = "compliance-indexes"
    reports_bucket: str = "compliance-reports"
    pdfs_bucket: str = "compliance-pdfs"

    # Auth — Sprint 1 dev key; replace with DynamoDB lookup in Sprint 5
    dev_api_key: str = "dev-key-001"
    from_email: str = "noreply@complianceaudit.ai"
    admin_api_key: str = "admin-key-001"
    api_keys_table_name: str = "compliance-api-keys"

    # Bedrock
    bedrock_region: str = "us-east-1"
    nova_model_id: str = "amazon.nova-lite-v1:0"
    nova_pro_model_id: str = "amazon.nova-pro-v1:0"

    # App
    environment: str = "development"


settings = Settings()
