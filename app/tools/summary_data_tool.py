from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from datetime import datetime

def get_summary_data(api_id: str, start_time: datetime, end_time: datetime):
    try:
        client = get_kusto_client()
        settings = get_settings()
        organization_id = settings.ORGANIZATION_ID

        # Construct the base query
        query = f"""
        let startTime = datetime({start_time.isoformat()});
        let endTime = datetime({end_time.isoformat()});
        """

        # Add traffic data query
        query += "let trafficData = analytics_response_code_summary | "
        if api_id is not None:
            query += f"where apiId == '{api_id}' and "
        query += "AGG_WINDOW_START_TIME between (startTime .. endTime) | summarize totalHits = sum(hitCount), errorHits = sumif(hitCount, responseCode >= 400) by apiId;"

        # Add latency data query
        query += "let latencyData = analytics_target_response_summary | "
        if api_id is not None:
            query += f"where apiId == '{api_id}' and "
        query += "AGG_WINDOW_START_TIME between (startTime .. endTime) | summarize totalLatency = sum(responseLatencyMedian + backendLatencyMedian) by apiId;"

        # Final query
        query += "trafficData | join kind=inner (latencyData) on apiId | project apiId, totalHits, errorHits, totalLatency"

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]

        if not results:
            return {"apiId": api_id, "totalHits": 0, "errorHits": 0, "totalLatency": 0}

        row = results[0]
        summary = {
            "apiId": row["apiId"],
            "totalHits": row["totalHits"],
            "errorHits": row["errorHits"],
            "totalLatency": row["totalLatency"]
        }

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))