from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from datetime import datetime

def get_latency_data(api_id: str, start_time: datetime, end_time: datetime):
    try:
        client = get_kusto_client()
        settings = get_settings()
        organization_id = settings.ORGANIZATION_ID

        # Construct the base query
        query = f"""
        let startTime = datetime({start_time.isoformat()});
        let endTime = datetime({end_time.isoformat()});
        analytics_target_response_summary
        """

        # Add API ID condition if it's not None
        if api_id is not None:
            query += f"where apiId == '{api_id}' and "
        
        query += "| where customerId == '{organization_id}' and AGG_WINDOW_START_TIME between (startTime .. endTime)"

        # Continue constructing the query
        query += """
        | project AGG_WINDOW_START_TIME, apiId, customerId, responseLatencyMedian, backendLatencyMedian
        """

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]

        data = []
        for row in results:
            data.append({
                "AGG_WINDOW_START_TIME": row["AGG_WINDOW_START_TIME"],
                "apiId": row["apiId"],
                "customerId": row["customerId"],
                "responseLatencyMedian": row["responseLatencyMedian"],
                "backendLatencyMedian": row["backendLatencyMedian"]
            })

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))