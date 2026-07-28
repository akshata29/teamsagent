"""Create the `capmarkets-research` Azure AI Search index.

Includes both document-level security mechanisms:
* Native ACL (preview): ``permissionFilterOption`` + ``GroupIds``/``UserIds`` fields.
* GA security trimming: a plain filterable ``group_ids`` field.

Run:  python -m deploy.create_index
"""

from __future__ import annotations

import os

from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

ENDPOINT = os.environ["SEARCH_ENDPOINT"]
INDEX_NAME = os.environ.get("SEARCH_INDEX_NAME", "capmarkets-research")
API_VERSION = os.environ.get("SEARCH_API_VERSION", "2026-05-01-preview")
DIMS = int(os.environ.get("AOAI_EMBED_DIMS", "1536"))


def build_index() -> dict:
    """Build the index definition as a raw dict.

    A raw dict body is used for the permission-filter fields so this script works
    across the preview SDK surface (the typed ``permission_filter`` symbols moved
    between azure-search-documents releases).
    """
    fields = [
        {"name": "id", "type": "Edm.String", "key": True},
        {"name": "title", "type": "Edm.String", "searchable": True, "retrievable": True},
        {"name": "content", "type": "Edm.String", "searchable": True, "retrievable": True},
        {"name": "classification", "type": "Edm.String", "filterable": True, "retrievable": True},
        {
            "name": "contentVector",
            "type": "Collection(Edm.Single)",
            "dimensions": DIMS,
            "vectorSearchProfile": "vprofile",
            "searchable": True,
        },
        # Native ACL (preview) permission-filter fields
        {
            "name": "GroupIds",
            "type": "Collection(Edm.String)",
            "permissionFilter": "groupIds",
            "filterable": True,
        },
        {
            "name": "UserIds",
            "type": "Collection(Edm.String)",
            "permissionFilter": "userIds",
            "filterable": True,
        },
        # GA security-trimming field
        {
            "name": "group_ids",
            "type": "Collection(Edm.String)",
            "filterable": True,
            "retrievable": False,
        },
    ]
    return {
        "name": INDEX_NAME,
        "fields": fields,
        "permissionFilterOption": "enabled",
        "vectorSearch": {
            "profiles": [{"name": "vprofile", "algorithm": "hnsw"}],
            "algorithms": [{"name": "hnsw", "kind": "hnsw"}],
        },
    }


def main() -> None:
    client = SearchIndexClient(
        endpoint=ENDPOINT,
        credential=DefaultAzureCredential(),
        api_version=API_VERSION,
    )
    index = build_index()
    # create_or_update_index accepts a mapping body for preview features.
    client.create_or_update_index(index)  # type: ignore[arg-type]
    print(f"Index '{INDEX_NAME}' created/updated on {ENDPOINT} ({API_VERSION}).")


if __name__ == "__main__":
    main()
