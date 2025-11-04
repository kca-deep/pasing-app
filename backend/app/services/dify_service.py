"""
Dify API client service.
Handles communication with Dify Knowledge Base API.
"""
import logging
import httpx
from typing import List, Optional
from fastapi import HTTPException

from app.models import DifyDataset, DifyUploadResponse, IndexingStatusResponse

logger = logging.getLogger(__name__)


class DifyClient:
    """
    Client for interacting with Dify API.
    Handles dataset management, document uploads, and indexing status checks.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.dify.ai"):
        """
        Initialize Dify API client.

        Args:
            api_key: Dify API key
            base_url: Dify API base URL

        Raises:
            ValueError: If API key is empty or invalid
        """
        # Validate API key
        if not api_key or not api_key.strip():
            raise ValueError("Dify API key cannot be empty")

        self.api_key = api_key.strip()

        # Clean up base_url: remove trailing slash and /v1 suffix
        # (we'll add /v1 prefix to endpoints ourselves)
        cleaned_url = base_url.rstrip("/")
        if cleaned_url.endswith("/v1"):
            cleaned_url = cleaned_url[:-3]  # Remove /v1 suffix

        self.base_url = cleaned_url
        self.timeout = 30.0  # 30 seconds timeout

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=self.timeout
        )

        if base_url != self.base_url:
            logger.info(f"📦 DifyClient initialized: {base_url} -> {self.base_url}")
        else:
            logger.info(f"📦 DifyClient initialized with base_url={self.base_url}")

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def test_connection(self) -> bool:
        """
        Test connection to Dify API by listing datasets.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            logger.info("🔍 Testing Dify API connection...")
            response = await self.client.get(f"{self.base_url}/v1/datasets?page=1&limit=1")
            response.raise_for_status()
            logger.info("✅ Dify API connection successful")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Dify API connection failed: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"❌ Dify API connection error: {str(e)}", exc_info=True)
            return False

    async def list_datasets(self, page: int = 1, limit: int = 20) -> List[DifyDataset]:
        """
        List all datasets in Dify Knowledge Base.

        Args:
            page: Page number (1-indexed)
            limit: Number of datasets per page

        Returns:
            List of DifyDataset objects

        Raises:
            HTTPException: If API call fails
        """
        try:
            url = f"{self.base_url}/v1/datasets"
            logger.info(f"📋 Listing Dify datasets from {url} (page={page}, limit={limit})")
            response = await self.client.get(
                url,
                params={"page": page, "limit": limit}
            )
            logger.info(f"📊 Dify API response status: {response.status_code}")
            response.raise_for_status()

            data = response.json()
            datasets = []

            for item in data.get("data", []):
                dataset = DifyDataset(
                    id=item["id"],
                    name=item["name"],
                    description=item.get("description"),
                    document_count=item.get("document_count", 0),
                    word_count=item.get("word_count", 0),
                    created_at=item.get("created_at", 0)
                )
                datasets.append(dataset)

            logger.info(f"✅ Retrieved {len(datasets)} datasets")
            return datasets

        except httpx.HTTPStatusError as e:
            error_text = e.response.text[:500]  # Limit error text length
            logger.error(f"❌ Dify API HTTP error: {e.response.status_code}")
            logger.error(f"   Request URL: {e.request.url}")
            logger.error(f"   Response: {error_text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Dify API error ({e.response.status_code}): {error_text}"
            )
        except Exception as e:
            logger.error(f"❌ Error listing datasets: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

    async def create_document_by_text(
        self,
        dataset_id: str,
        name: str,
        text: str,
        indexing_technique: str = "high_quality"
    ) -> DifyUploadResponse:
        """
        Create a document in Dify Knowledge Base using text content.

        Args:
            dataset_id: Dataset ID
            name: Document name
            text: Document text content
            indexing_technique: Indexing technique ("high_quality" or "economy")

        Returns:
            DifyUploadResponse with document ID and batch ID

        Raises:
            HTTPException: If API call fails
        """
        try:
            logger.info(f"📤 Uploading document '{name}' to dataset {dataset_id}")
            response = await self.client.post(
                f"{self.base_url}/v1/datasets/{dataset_id}/document/create_by_text",
                json={
                    "name": name,
                    "text": text,
                    "indexing_technique": indexing_technique,
                    "process_rule": {
                        "mode": "automatic"
                    }
                }
            )
            response.raise_for_status()

            data = response.json()
            document_data = data.get("document", {})
            batch = data.get("batch", "")

            upload_response = DifyUploadResponse(
                document_id=document_data.get("id", ""),
                batch=batch,
                indexing_status=document_data.get("indexing_status", "waiting"),
                success=True
            )

            logger.info(f"✅ Document uploaded successfully (batch={batch})")
            return upload_response

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Failed to upload document: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Dify API error: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"❌ Error uploading document: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

    async def check_indexing_status(
        self,
        dataset_id: str,
        batch_id: str
    ) -> IndexingStatusResponse:
        """
        Check indexing status of a document batch.

        Args:
            dataset_id: Dataset ID
            batch_id: Batch ID from upload response

        Returns:
            IndexingStatusResponse with indexing status and progress

        Raises:
            HTTPException: If API call fails
        """
        try:
            logger.info(f"🔍 Checking indexing status for batch {batch_id}")
            response = await self.client.get(
                f"{self.base_url}/v1/datasets/{dataset_id}/documents/{batch_id}/indexing-status"
            )
            response.raise_for_status()

            data = response.json()

            status_response = IndexingStatusResponse(
                id=data.get("id", ""),
                indexing_status=data.get("indexing_status", "waiting"),
                completed_segments=data.get("completed_segments", 0),
                total_segments=data.get("total_segments", 0)
            )

            logger.info(f"✅ Indexing status: {status_response.indexing_status} "
                       f"({status_response.completed_segments}/{status_response.total_segments})")
            return status_response

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Failed to check indexing status: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Dify API error: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"❌ Error checking indexing status: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
