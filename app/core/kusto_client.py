from azure.kusto.data import KustoConnectionStringBuilder, KustoClient
from azure.kusto.data.helpers import dataframe_from_result_table
import os

from app.config import get_settings
from functools import lru_cache


@lru_cache()
def get_kusto_client() -> KustoClient:
    settings = get_settings()

    # Use InteractiveBrowserCredential for user login
    credential = KustoConnectionStringBuilder.with_aad_application_key_authentication(
            settings.KUSTO_CLUSTER_URL, settings.KUSTO_CLIENT_ID,settings.KUSTO_CLIENT_SECRET,settings.KUSTO_TENANT_ID
        )

    
    return KustoClient(credential)
