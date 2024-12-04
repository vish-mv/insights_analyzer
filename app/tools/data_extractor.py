from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from openai import OpenAI
from pydantic import BaseModel
import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataExtractionRequest(BaseModel):
    user_query: str

def extract_data(request: DataExtractionRequest):
    try:
        settings = get_settings()
        organization_id = settings.ORGANIZATION_ID
        environment_id =  settings.ENVIRONMENT_ID
        logging.info(f"Starting data extraction for org: {organization_id}")
        
        # Initialize clients and settings
        kusto_client = get_kusto_client()
        settings = get_settings()
        
        #  Get environments and APIs data from Kusto
        # environments_query = f"""
        # analytics_response_code_summary
        # | where customerId == '{organization_id}'
        # | distinct keyType
        # | order by keyType asc
        # """
        
        apis_query = f"""
        analytics_response_code_summary
        | where customerId == '{organization_id}' and deploymentId == '{environment_id}'
        | summarize by apiId, apiName
        """
        
        # Execute queries
        # env_response = kusto_client.execute(settings.KUSTO_DATABASE_NAME, environments_query)
        api_response = kusto_client.execute(settings.KUSTO_DATABASE_NAME, apis_query)
        
        # Process results
        # environments = [row["keyType"] for row in env_response.primary_results[0]]
        apis = [{"apiId": row["apiId"], "apiName": row["apiName"]} 
               for row in api_response.primary_results[0]]
        
        current_time = datetime.datetime.now()
        
        # Single LLM call to extract all information
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.OPEN_AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a JSON generator that extracts information from user queries.
                    You must respond with a valid JSON object containing two keys: timeRange, and api.
                    
                    Rules:
                    - For timeRange: If not specified, use yesterday to today. Always ensure at least 24 hours difference. If theres a prediction requested given at least give one month range past.
                    - For api: Select the most relevant API from the provided list, or use "NoData" if none matches.
                    
                    Response format must be exactly:
                    {
                        "timeRange": {
                            "start_time": "YYYY-MM-DD",
                            "end_time": "YYYY-MM-DD"
                        },
                        "api": {
                            "apiName": "string",
                            "apiId": "string"
                        }
                    }"""
                },
                {
                    "role": "user",
                    "content": (
                        f"User Query: '{request.user_query}'\n"
                        f"Available APIs: {apis}\n"
                        f"Current Time: {current_time}"
                    )
                }
            ],
            max_tokens=1000,
            response_format={ "type": "json_object" }
        )
        
        # Parse the JSON response
        extracted_data = json.loads(response.choices[0].message.content)
        
        # Add the API list to the response
        extracted_data["api"]["apiList"] = apis
        # logging.info(f"Extracted environment: {extracted_data['environment']}")
        logging.info(f"Extracted time range: {extracted_data['timeRange']}")
        logging.info(f"Extracted API details: {extracted_data['api']}")
        logging.info("Data extraction completed successfully")
        return extracted_data

    except Exception as e:
        logging.error(f"An error occurred in data extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))