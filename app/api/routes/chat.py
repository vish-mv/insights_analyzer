from fastapi import APIRouter, HTTPException
from app.api.routes.tools import select_tools
from app.tools import api_identifier_tool, error_data_tool, traffic_data_tool, summary_data_tool, latency_data_tool
from openai import OpenAI
from app.config import get_settings
from app.tools.time_tool import get_time_data 

router = APIRouter()

@router.post("/chat")
async def chat(user_query: str):
    try:
        # Step 1: Determine which tools to use
        time_data = get_time_data(user_query)
        start_time = time_data["start_time"]
        end_time = time_data["end_time"]

        # Step 2: Determine the API ID and name
        api_summary = api_identifier_tool.get_api_identifier_summary("example_organization_id", user_query)
        api_id = api_summary["apiId"]
        api_name = api_summary["apiName"]

        tools_response = await select_tools(user_query)
        selected_tools = tools_response["selected_tools"]

        # Step 3: Execute the selected tools
        data = []
        for tool in selected_tools:
            if tool == "API Identifier Tool":
                # Example execution, replace with actual parameters
                result = api_identifier_tool.get_api_identifier_summary("example_organization_id")
            elif tool == "Error Data Tool":
                # Example execution, replace with actual parameters
                result = error_data_tool.get_error_data(api_id, start_time, end_time)
            elif tool == "Traffic Data Tool":
                # Example execution, replace with actual parameters
                result = traffic_data_tool.get_traffic_data(api_id, start_time, end_time)
            elif tool == "Summary Data Tool":
                # Example execution, replace with actual parameters
                result = summary_data_tool.get_summary_data(api_id, start_time, end_time)
            elif tool == "Latency Data Tool":
                # Example execution, replace with actual parameters
                result = latency_data_tool.get_latency_data(api_id, "example_customer_id", start_time, end_time)
            else:
                continue

            data.append(result)

        # Step 3: Use ChatGPT API to generate a response
        settings = get_settings()
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.MODEL,
            messages=[{"role": "user", "content": f"User query: '{user_query}'. Data: {data}. Provide a response based on this information."}],
            max_tokens=10000
        )

        chat_response = response.choices[0].message.content
        return {"response": chat_response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))