"""Externe Adapter (Microsoft Graph, …)."""

from backend.infrastructure.adapters.outlook.graph import (
    OutlookGraphClient,
    map_graph_message,
)
from backend.infrastructure.adapters.outlook.ingestion import (
    OutlookIngestionAdapter,
    OutlookIngestionRunner,
)

__all__ = [
    "OutlookGraphClient",
    "OutlookIngestionAdapter",
    "OutlookIngestionRunner",
    "map_graph_message",
]
