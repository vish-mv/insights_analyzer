from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.identity import InteractiveBrowserCredential  # Import InteractiveBrowserCredential
from app.config import get_settings
from functools import lru_cache


@lru_cache()
def get_kusto_client() -> KustoClient:
    settings = get_settings()

    # Use InteractiveBrowserCredential for user login
    credential = InteractiveBrowserCredential()

    # Create the connection string builder using the interactive browser credential
    kcsb = KustoConnectionStringBuilder.with_azure_token_credential(
        settings.KUSTO_CLUSTER_URL,
        credential
    )
    return KustoClient(kcsb)
