import os
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError
import structlog


logger = structlog.get_logger()


class ECRClient:
    def __init__(self, region: Optional[str] = None):
        self.region = region or os.getenv("AWS_REGION", "ap-southeast-1")
        cfg = BotoConfig(retries={"max_attempts": 3, "mode": "standard"}, read_timeout=10, connect_timeout=10)
        self.client = boto3.client("ecr", region_name=self.region, config=cfg)

    def get_latest_digest(self, image_uri: str) -> Optional[str]:
        attempts = 0
        last_err = None
        while attempts < 3:
            attempts += 1
            try:
                registry_and_repo, tag = image_uri.rsplit(":", 1)
                if tag != "latest":
                    logger.warning("non_latest_tag", image=image_uri)
                registry_parts = registry_and_repo.split(".dkr.ecr.")
                registry_id = registry_parts[0]
                repository = registry_and_repo.split(".amazonaws.com/")[1]

                resp = self.client.describe_images(
                    registryId=registry_id,
                    repositoryName=repository,
                    imageIds=[{"imageTag": "latest"}],
                )
                images = resp.get("imageDetails", [])
                if not images:
                    logger.warning("no_images_found", repository=repository)
                    return None
                images.sort(key=lambda x: x.get("imagePushedAt", 0), reverse=True)
                digest = images[0].get("imageDigest")
                if digest:
                    return digest
                return None
            except (ClientError, BotoCoreError) as e:
                last_err = e
                logger.warning("ecr_retry", attempt=attempts, error=str(e))
            except Exception as e:
                last_err = e
                logger.warning("ecr_retry_unexpected", attempt=attempts, error=str(e))
        if last_err:
            logger.error("ecr_failed_after_retries", error=str(last_err), image=image_uri)
        return None