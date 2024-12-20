from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_traffic_data(apiName: str, start_time: datetime, end_time: datetime):
    try:
        logging.info("Starting get_traffic_data function")
        client = get_kusto_client()
        settings = get_settings()
        organization_id = settings.ORGANIZATION_ID
        environment_id =  settings.ENVIRONMENT_ID
        logging.info("Retrieved settings and Kusto client")

        # Construct the base query
        query = f"""
        let startTime = datetime({start_time});
        let endTime = datetime({end_time});
        analytics_response_code_summary
        """
        logging.info(f"Constructed base query: {query}")

        # Add API ID condition if it's not 'NoData'
        if apiName != 'NoData':
            query += f"| where apiName == '{apiName}' and "
        else:
            query+="|where"
        
        # Always include the customerId condition
        query += f" customerId == '{organization_id}' and AGG_WINDOW_START_TIME between (startTime .. endTime) and deploymentId == '{environment_id}'"
        query += """
        | summarize totalHits = sum(hitCount) by AGG_WINDOW_START_TIME, proxyResponseCode, apiName, deploymentId
        | project AGG_WINDOW_START_TIME, totalHits, proxyResponseCode, apiName, deploymentId
        """
        logging.info(f"Final query: {query}")

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]
        logging.info("Received response from Kusto client")

        data = []
        for row in results:
            data.append({
                "AGG_WINDOW_START_TIME": row["AGG_WINDOW_START_TIME"],
                "apiName": row["apiName"],
                "totalHits": row["totalHits"],
                "proxyResponseCode": row["proxyResponseCode"]
            })
        logging.info(f"Extracted data:----------------------------- {data}")
        logging.info(f"Extracted data end ----------------------------------------------------------------------------------")

        return data

    except Exception as e:
        logging.error(f"An error occurred in get_traffic_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))