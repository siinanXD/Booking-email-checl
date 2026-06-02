"""Externe Adapter (Microsoft Graph, …)."""

from adapters.outlook_graph import OutlookGraphClient, map_graph_message
from adapters.outlook_ingestion import OutlookIngestionAdapter, OutlookIngestionRunner

__all__ = [
    "OutlookGraphClient",
    "OutlookIngestionAdapter",
    "OutlookIngestionRunner",
    "map_graph_message",
]
