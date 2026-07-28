"""Embed and upload the synthetic Capital Markets corpus into Azure AI Search.

Populates BOTH the native-ACL fields (GroupIds) and the GA trimming field
(group_ids) with the same synthetic Entra group GUIDs.

Run:  python -m deploy.seed_synthetic_data
"""

from __future__ import annotations

import hashlib
import os
from typing import List

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

from deploy.synthetic_data import SYNTHETIC_DOCS

ENDPOINT = os.environ["SEARCH_ENDPOINT"]
INDEX_NAME = os.environ.get("SEARCH_INDEX_NAME", "capmarkets-research")
API_VERSION = os.environ.get("SEARCH_API_VERSION", "2026-05-01-preview")
DIMS = int(os.environ.get("AOAI_EMBED_DIMS", "1536"))


def _embed(text: str) -> List[float]:
    """Embed via Azure OpenAI if configured, else a deterministic fallback."""
    if os.environ.get("AOAI_ENDPOINT"):
        from azure.identity import get_bearer_token_provider
        from openai import AzureOpenAI

        provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )
        client = AzureOpenAI(
            azure_endpoint=os.environ["AOAI_ENDPOINT"],
            azure_ad_token_provider=provider,
            api_version=os.environ.get("AOAI_API_VERSION", "2024-12-01-preview"),
        )
        deployment = os.environ.get("AOAI_EMBED_DEPLOYMENT", "text-embedding-3-small")
        return client.embeddings.create(model=deployment, input=text).data[0].embedding

    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [((digest[i % len(digest)] / 255.0) * 2.0 - 1.0) for i in range(DIMS)]


def main() -> None:
    client = SearchClient(
        endpoint=ENDPOINT,
        index_name=INDEX_NAME,
        credential=DefaultAzureCredential(),
        api_version=API_VERSION,
    )
    docs = []
    for d in SYNTHETIC_DOCS:
        groups = list(d["group_ids"])  # type: ignore[arg-type]
        users = list(d.get("user_ids", []))  # type: ignore[arg-type]
        docs.append(
            {
                "id": d["id"],
                "title": d["title"],
                "content": d["content"],
                "classification": d["classification"],
                "contentVector": _embed(str(d["content"])),
                # Native ACL (preview): groups and users in their own permission fields.
                "GroupIds": groups,
                "UserIds": users,
                # GA security-trimming field: a flat list of all entitled principals.
                "group_ids": groups + users,
            }
        )
    result = client.upload_documents(documents=docs)
    print(f"Uploaded {len(result)} documents to '{INDEX_NAME}'.")


if __name__ == "__main__":
    main()
