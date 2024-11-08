from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_latency_data(apiName: str, start_time: datetime, end_time: datetime):
    try:
        logging.info("Starting get_latency_data function")
        client = get_kusto_client()
        settings = get_settings()
        organization_id = settings.ORGANIZATION_ID
        environment_id =  settings.ENVIRONMENT_ID
        logging.info(f"Retrieved settings and Kusto client. Parameters: apiName={apiName}")

        
        # Construct the query
        query = f"""
        let startTime = datetime({start_time});
        let endTime = datetime({end_time});
        analytics_target_response_summary
        | where customerId == '{organization_id}' and deploymentId == '{environment_id}'
        """

        if apiName != 'NoData':
            query += f"| where apiName == '{apiName}'"

        query += f"""        
        | summarize p95_latency = percentile(responseLatencyPercentile, 95) by AGG_WINDOW_START_TIME, apiName, hitCount
        """
        
        logging.info(f"Executing query: {query}")

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]
        logging.info(f"Received {len(results)} rows from Kusto client")

        data = []
        for row in results:
            data.append({
                "AGG_WINDOW_START_TIME": row["AGG_WINDOW_START_TIME"],
                "apiName": row["apiName"],
                "latency": row["p95_latency"],
                "hitCount": row["hitCount"]
            })

        logging.info(f"Processed {len(data)} data points")
        return data

    except Exception as e:
        logging.error(f"An error occurred in get_latency_data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))