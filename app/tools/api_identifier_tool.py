from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from openai import OpenAI
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_api_identifier_summary(organization_id: str, user_query: str):
    try:
        logging.info("Starting get_api_identifier_summary function")

        client = get_kusto_client()
        settings = get_settings()
        logging.info("Retrieved settings and Kusto client")

        # Get all APIs
        query = f"""
        analytics_response_code_summary
        | where customerId == '{organization_id}'
        | summarize by apiId, apiName
        """
        logging.info(f"Executing Kusto query: {query}")

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]
        logging.info("Received response from Kusto client")

        apis = []
        for row in results:
            apis.append({
                "apiId": row["apiId"],
                "apiName": row["apiName"]
            })
        logging.info(f"Retrieved APIs: {apis}")

        # Use OpenAI to determine the most matching API
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logging.info("Initialized OpenAI client")

        response = client.chat.completions.create(
            model=settings.MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Given the user query: '{user_query}', "
                        f"which of the following APIs is the most relevant? {apis}. "
                        "Please respond with the most matching API and API ID, or 'None' for both if no API is relevant."
                        "Response should be two apiName,apiId only. (Example Response: Book list api,335263522733)"
                    )
                }
            ],
            max_tokens=1000
        )
        logging.info("Received response from OpenAI")

        # Extract the content from the response
        response_content = response.choices[0].message.content.strip()
        logging.info(f"Response content: {response_content}")

        # Parse the response to extract the most matching API and API ID
        api_name, api_id = response_content.split(',')
        logging.info(f"Extracted API name: {api_name}, API ID: {api_id}")

        return {"apiName": api_name, "apiId": api_id}

    except Exception as e:
        logging.error(f"An error occurred in get_api_identifier_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))