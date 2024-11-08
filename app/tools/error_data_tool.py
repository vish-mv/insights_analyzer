from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_error_data(apiName: str, start_time: datetime, end_time: datetime):
    try:
        logging.info("Starting get_error_data function")
        client = get_kusto_client()
        settings = get_settings()
        organization_id = settings.ORGANIZATION_ID
        environment_id =  settings.ENVIRONMENT_ID
        logging.info("Retrieved settings and Kusto client")

        # Construct the base query
        query = f"""
        let startTime = datetime({start_time});
        let endTime = datetime({end_time});
        analytics_proxy_error_summary
        """
        # Add API ID condition if it's not None
        if apiName != 'NoData':
            query += f"| where apiName == '{apiName}' and "
        else:
            query+="|where"
        
        query += f" customerId == '{organization_id}' and AGG_WINDOW_START_TIME between (startTime .. endTime) and deploymentId == '{environment_id}'"
        query += """
        | project AGG_WINDOW_START_TIME, apiName, hitCount, errorType, errorMessage
        """
        logging.info(f"Final query: {query}")

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]
        logging.info("Received response from Kusto client")
        logging.info(results)
        data = []
        
        if not results:
            data.append("NoData")
        else:
            for row in results:
                data.append({
                    "AGG_WINDOW_START_TIME": row["AGG_WINDOW_START_TIME"],
                    "apiName": row["apiName"],
                    "hitCount": row["hitCount"],
                    "errorType": row["errorType"],
                    "errorMessage": row["errorMessage"],
                })
        logging.info(f"Extracted data: {data}")

        return data

    except Exception as e:
        logging.error(f"An error occurred in get_error_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))