from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_latency_data(api_id: str, start_time: datetime, end_time: datetime, env_name: str):
    try:
        logging.info("Starting get_latency_data function")
        client = get_kusto_client()
        settings = get_settings()
        organization_id = settings.ORGANIZATION_ID
        logging.info(f"Retrieved settings and Kusto client. Parameters: api_id={api_id}, env_name={env_name}")

        
        # Construct the query
        query = f"""
        let startTime = datetime({start_time});
        let endTime = datetime({end_time});
        let envMapping = analytics_response_code_summary
        | where customerId == '{organization_id}'
        """

        if api_id != 'NoData':
            query += f"| where apiId == '{api_id}'"

        query += f"""
        | where keyType == '{env_name}'
        | distinct deploymentId, keyType, apiId;
        analytics_target_response_summary
        | where customerId == '{organization_id}'
        | where AGG_WINDOW_START_TIME between (startTime .. endTime)
        """

        if api_id != 'NoData':
            query += f"| where apiId == '{api_id}'"

        query += f"""
        | join kind=inner envMapping on deploymentId
        | project 
            AGG_WINDOW_START_TIME,
            apiId,
            customerId,
            responseLatencyMedian,
            backendLatencyMedian,
            deploymentId,
            keyType
        | order by AGG_WINDOW_START_TIME asc
        """
        
        logging.info(f"Executing query: {query}")

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]
        logging.info(f"Received {len(results)} rows from Kusto client")

        data = []
        for row in results:
            data.append({
                "AGG_WINDOW_START_TIME": row["AGG_WINDOW_START_TIME"],
                "apiId": row["apiId"],
                "customerId": row["customerId"],
                "responseLatencyMedian": row["responseLatencyMedian"],
                "backendLatencyMedian": row["backendLatencyMedian"],
                "deploymentId": row["deploymentId"],
            })

        logging.info(f"Processed {len(data)} data points")
        return data

    except Exception as e:
        logging.error(f"An error occurred in get_latency_data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))