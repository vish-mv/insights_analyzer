from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from fastapi import HTTPException
from openai import OpenAI

def get_api_identifier_summary(organization_id: str, user_query: str):
    try:
        client = get_kusto_client()
        settings = get_settings()
        organization_id = settings.ORGANIZATION_ID

        # Get all APIs
        query = f"""
        analytics_response_code_summary
        | where customerId == '{organization_id}'
        | summarize by apiId, apiName
        """

        response = client.execute(settings.KUSTO_DATABASE_NAME, query)
        results = response.primary_results[0]

        apis = []
        for row in results:
            apis.append({
                "apiId": row["apiId"],
                "apiName": row["apiName"]
            })

        # Use OpenAI to determine the most matching API
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completion.create(
            model=settings.MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Given the user query: '{user_query}', "
                        f"which of the following APIs is the most relevant? {apis}. "
                        "Please respond with the most matching API and API ID, or 'None'for both if no API is relevant."
                        "Respond should be two apiName,apiId only. (Example Response: Book list api,335263522733)"
                    )
                }
            ],
            max_tokens=1000
        )

        # Extract the content from the response
        response_content = response.choices[0].message['content'].strip()

        # Parse the response to extract the most matching API and API ID
        # This depends on how the response is formatted
        api_name, api_id = response_content.split(', ')

        return {"apiName": api_name, "apiId": api_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))