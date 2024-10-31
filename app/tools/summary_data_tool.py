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
        
        let trafficData = analytics_response_code_summary
        | where customerId == '{organization_id}' and AGG_WINDOW_START_TIME between (startTime .. endTime)
        """
        
        # Add API ID condition if it's not 'NoData'
        if api_id != 'NoData':
            query += f" and apiId == '{api_id}'"
        
        query += f"""
        | summarize totalHits = sum(hitCount) by apiId;
        
        let errorData = analytics_proxy_error_summary
        | where customerId == '{organization_id}' and AGG_WINDOW_START_TIME between (startTime .. endTime)
        """
        
        # Add API ID condition if it's not 'NoData'
        if api_id != 'NoData':
            query += f" and apiId == '{api_id}'"
        
        query += f"""
        | summarize errorHits = sum(hitCount) by apiId;
        
        let latencyData = analytics_target_response_summary
        | where customerId == '{organization_id}' and AGG_WINDOW_START_TIME between (startTime .. endTime)
        """
        
        # Add API ID condition if it's not 'NoData'
        if api_id != 'NoData':
            query += f" and apiId == '{api_id}'"
        
        query += """
        | summarize totalLatency = sum(responseLatencyMedian + backendLatencyMedian) by apiId;
        
        trafficData
        | join kind=inner (errorData) on apiId
        | join kind=inner (latencyData) on apiId
        | project apiId, totalHits, errorHits, totalLatency
        """
        
        logging.info(f"Final query: {query}")

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]
        logging.info("Received response from Kusto client")
        logging.info(results)
        if (not results or 
            not hasattr(results, 'data') or 
            not results.data or 
            (isinstance(results.data, list) and len(results.data) == 0)):            
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