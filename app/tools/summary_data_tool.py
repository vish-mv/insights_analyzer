from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_summary_data(api_id: str, start_time: datetime, end_time: datetime):
    try:
        logging.info("Starting get_summary_data function")
        client = get_kusto_client()
        settings = get_settings()
        organization_id = settings.ORGANIZATION_ID
        logging.info("Retrieved settings and Kusto client")

        # Construct the base query
        query = f"""
        let startTime = datetime({start_time});
        let endTime = datetime({end_time});
        """
        logging.info(f"Constructed base query: {query}")

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
        logging.info(f"Final query: {query}")

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]
        logging.info("Received response from Kusto client")

        if not results:
            logging.info("No results found, returning default summary")
            return {"apiId": api_id, "totalHits": 0, "errorHits": 0, "totalLatency": 0}

        row = results[0]
        summary = {
            "apiId": row["apiId"],
            "totalHits": row["totalHits"],
            "errorHits": row["errorHits"],
            "totalLatency": row["totalLatency"]
        }
        logging.info(f"Extracted summary: {summary}")

        return summary

    except Exception as e:
        logging.error(f"An error occurred in get_summary_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))