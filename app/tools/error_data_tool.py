from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from datetime import datetime

def get_error_data(api_id: str, start_time: datetime, end_time: datetime):
    try:
        client = get_kusto_client()
        settings = get_settings()

        query = f"""
        let startTime = datetime({start_time.isoformat()});
        let endTime = datetime({end_time.isoformat()});
        analytics_response_code_summary
        | where apiId == '{api_id}' and AGG_WINDOW_START_TIME between (startTime .. endTime)
        | join kind=inner (
            analytics_proxy_error_summary
            | where AGG_WINDOW_START_TIME between (startTime .. endTime)
        ) on AGG_WINDOW_START_TIME
        | project AGG_WINDOW_START_TIME, apiId, hitCount, responseCode, errorType, errorCode
        """

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]

        data = []
        for row in results:
            data.append({
                "AGG_WINDOW_START_TIME": row["AGG_WINDOW_START_TIME"],
                "apiId": row["apiId"],
                "hitCount": row["hitCount"],
                "responseCode": row["responseCode"],
                "errorType": row["errorType"],
                "errorCode": row["errorCode"]
            })

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))