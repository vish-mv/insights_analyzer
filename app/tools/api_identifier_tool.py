from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException

def get_api_identifier_summary(organization_id: str):
    try:
        client = get_kusto_client()
        settings = get_settings()

        query = f"""
        analytics_response_code_summary
        | where customerId == '{organization_id}'
        | summarize by apiId, apiName
        """

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]

        data = []
        for row in results:
            data.append({
                "apiId": row["apiId"],
                "apiName": row["apiName"]
            })

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))