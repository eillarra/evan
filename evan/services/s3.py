import os

import boto3
import requests
from django.conf import settings
from storages.backends.s3 import S3Storage as BaseS3Storage


class S3Storage(BaseS3Storage):
    """Custom S3 storage backend."""

    def url(self, name, parameters=None, expire=None, http_method=None) -> str:
        """Return the URL of the object stored in S3."""
        try:
            url = super().url(name, parameters, expire, http_method)
            bucket_url = f"{os.environ.get('S3_ENDPOINT_URL')}/{os.environ.get('S3_BUCKET_NAME')}/"
            return url.replace(bucket_url, "/media/")
        except Exception:
            return "#"


def create_bucket(bucket_name: str) -> None:
    """Create an S3 bucket."""
    get_s3_client().create_bucket(Bucket=bucket_name)


def list_bucket_files(bucket_name: str) -> list[str]:
    """List all files in an S3 bucket."""
    return [obj["Key"] for obj in get_s3_client().list_objects_v2(Bucket=bucket_name).get("Contents", [])]


def empty_bucket(bucket_name: str) -> None:
    """Empty an S3 bucket."""
    for obj in get_s3_client().list_objects_v2(Bucket=bucket_name).get("Contents", []):
        get_s3_client().delete_object(Bucket=bucket_name, Key=obj["Key"])


def get_s3_client():
    """Return an S3 client."""
    return boto3.client(
        service_name="s3",
        endpoint_url=os.environ.get("S3_ENDPOINT_URL"),
        aws_access_key_id=os.environ.get("S3_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("S3_SECRET_KEY"),
    )


def delete_s3_object(object_key: str) -> None:
    """Delete an object from S3."""
    if settings.ENV != "production":
        return

    get_s3_client().delete_object(
        Bucket=os.environ.get("S3_BUCKET_NAME"),
        Key=object_key,
    )


def get_s3_presigned_url(object_key: str, expires_in: int = 60) -> str:
    """Return a presigned URL for an object in S3."""
    return get_s3_client().generate_presigned_url(
        ClientMethod="get_object",
        ExpiresIn=expires_in,
        Params={
            "Bucket": os.environ.get("S3_BUCKET_NAME"),
            "Key": object_key,
        },
    )


def get_s3_response(object_key: str) -> requests.Response:
    """Return a response from S3."""
    res = requests.get(url=get_s3_presigned_url(object_key, 10), stream=True, timeout=10)
    res.raise_for_status()
    return res
