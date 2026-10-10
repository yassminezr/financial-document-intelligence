
import json
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


AWS_PROFILE = "financial-ai"
AWS_REGION = "eu-north-1"
S3_BUCKET = "financial-document-intelligence-bucket"


class S3Client:
    def __init__(self):
        session = boto3.Session(
            profile_name=AWS_PROFILE,
            region_name=AWS_REGION
        )

        self.client = session.client("s3")
        self.bucket = S3_BUCKET

    def upload_pdf(self, file_path: str | Path, s3_key: str):
        file_path = Path(file_path)

        if not file_path.is_file():
            raise FileNotFoundError(file_path)

        self.client.upload_file(
            str(file_path),
            self.bucket,
            s3_key,
            ExtraArgs={
                "ContentType": "application/pdf"
            }
        )

        return f"s3://{self.bucket}/{s3_key}"

    def upload_metadata(self, metadata: dict, s3_key: str):
        payload = json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False
        ).encode("utf-8")

        self.client.put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=payload,
            ContentType="application/json"
        )

        return f"s3://{self.bucket}/{s3_key}"

    def get_metadata(self, s3_key: str) -> dict | None:
        """Retrieve existing document metadata from S3."""
        from botocore.exceptions import ClientError

        try:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key=s3_key
            )
            return json.loads(
                response["Body"].read().decode("utf-8")
            )

        except ClientError as error:
            code = error.response["Error"]["Code"]
            if code in ("NoSuchKey", "404"):
                return None
            raise

    def object_exists(self, s3_key: str) -> bool:
        """Check whether an object exists in S3."""
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=s3_key
            )
            return True

        except ClientError as error:
            code = error.response["Error"]["Code"]
            if code in ("404", "NoSuchKey"):
                return False
            raise
