from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from openai import OpenAI
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_environment_summary(organization_id: str, user_query: str):
    try:
        logging.info("Starting get_environment_summary function")

        client = get_kusto_client()
        settings = get_settings()
        logging.info("Retrieved settings and Kusto client")

        # Get all environments
        query = f"""
        analytics_response_code_summary
        | where customerId == '{organization_id}'
        | distinct keyType
        | order by keyType asc
        """
        logging.info(f"Executing Kusto query: {query}")

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]
        logging.info("Received response from Kusto client")

        environments = [row["keyType"] for row in results]
        logging.info(f"Retrieved environments: {environments}")

        # Use OpenAI to determine the most matching environment
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logging.info("Initialized OpenAI client")

        response = client.chat.completions.create(
            model=settings.OPEN_AI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Given the user query: '{user_query}', "
                        f"which of the following environments is the most relevant? {environments}. "
                        "If user mentions production/prod/live environment, prefer 'PRODUCTION'. "
                        "If user mentions development/dev environment, prefer 'SANDBOX'. "
                        "Please respond with just the environment name, or 'PRODUCTION' if no environment is clearly specified. "
                        "Response should be only the environment name. (Example Response: PRODUCTION)"
                    )
                }
            ],
            max_tokens=100
        )
        logging.info("Received response from OpenAI")

        # Extract the content from the response
        selected_environment = response.choices[0].message.content.strip()
        logging.info(f"Selected environment: {selected_environment}")

        return {
            "selectedEnvironment": selected_environment,
        }

    except Exception as e:
        logging.error(f"An error occurred in get_environment_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))