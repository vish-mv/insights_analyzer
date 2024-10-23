from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_latency_data(api_id: str, start_time: datetime, end_time: datetime):
    try:
        logging.info("Starting get_latency_data function")
        client = get_kusto_client()
        settings = get_settings()
        organization_id = settings.ORGANIZATION_ID
        logging.info("Retrieved settings and Kusto client")

        # Construct the base query
        query = f"""
        let startTime = datetime({start_time});
        let endTime = datetime({end_time});
        analytics_target_response_summary
        """
        logging.info(f"Constructed query: {query}")

        # Add API ID condition if it's not None
        if api_id is not None:
            query += f"where apiId == '{api_id}' and "
        
        query += "| where customerId == '{organization_id}' and AGG_WINDOW_START_TIME between (startTime .. endTime)"
        query += """
        | project AGG_WINDOW_START_TIME, apiId, customerId, responseLatencyMedian, backendLatencyMedian
        """
        logging.info(f"Final query: {query}")

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]
        logging.info("Received response from Kusto client")

        data = []
        for row in results:
            data.append({
                "AGG_WINDOW_START_TIME": row["AGG_WINDOW_START_TIME"],
                "apiId": row["apiId"],
                "customerId": row["customerId"],
                "responseLatencyMedian": row["responseLatencyMedian"],
                "backendLatencyMedian": row["backendLatencyMedian"]
            })
        logging.info(f"Extracted data: {data}")

        return data

    except Exception as e:
        logging.error(f"An error occurred in get_latency_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))