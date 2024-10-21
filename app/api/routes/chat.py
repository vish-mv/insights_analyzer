from fastapi import APIRouter, HTTPException
from app.api.routes.tools import select_tools
from app.tools import api_identifier_tool, error_data_tool, traffic_data_tool, summary_data_tool, latency_data_tool
import openai
from app.config import get_settings

router = APIRouter()

@router.post("/chat")
async def chat(user_query: str):
    try:
        # Step 1: Determine which tools to use
        tools_response = await select_tools(user_query)
        selected_tools = tools_response["selected_tools"]

        # Step 2: Execute the selected tools
        data = []
        for tool in selected_tools:
            if tool == "API Identifier Tool":
                # Example execution, replace with actual parameters
                result = api_identifier_tool.get_api_identifier_summary("example_organization_id")
            elif tool == "Error Data Tool":
                # Example execution, replace with actual parameters
                result = error_data_tool.get_error_data("example_api_id", "2023-01-01", "2023-01-31")
            elif tool == "Traffic Data Tool":
                # Example execution, replace with actual parameters
                result = traffic_data_tool.get_traffic_data("example_api_id", "2023-01-01", "2023-01-31")
            elif tool == "Summary Data Tool":
                # Example execution, replace with actual parameters
                result = summary_data_tool.get_summary_data("example_api_id", "2023-01-01", "2023-01-31")
            elif tool == "Latency Data Tool":
                # Example execution, replace with actual parameters
                result = latency_data_tool.get_latency_data("example_api_id", "example_customer_id", "2023-01-01", "2023-01-31")
            else:
                continue

            data.append(result)

        # Step 3: Use ChatGPT API to generate a response
        settings = get_settings()
        openai.api_key = settings.OPENAI_API_KEY

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"User query: '{user_query}'. Data: {data}. Provide a response based on this information.",
            max_tokens=150
        )

        chat_response = response.choices[0].text.strip()
        return {"response": chat_response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))