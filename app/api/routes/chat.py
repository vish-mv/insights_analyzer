from fastapi import APIRouter, HTTPException
from app.api.routes.tools import select_tools, ToolRequest  # Import ToolRequest
from app.tools import api_identifier_tool, error_data_tool, traffic_data_tool, summary_data_tool, latency_data_tool
from openai import OpenAI
from app.config import get_settings
from app.tools.time_tool import get_time_data, TimeRequest
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter()

class ChatRequest(BaseModel):
    user_query: str

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        settings = get_settings()
        logging.info("Received chat request")

        user_query = request.user_query
        logging.info(f"User query: {user_query}")

        time_data = get_time_data(TimeRequest(user_query=user_query))
        start_time = time_data["start_time"]
        end_time = time_data["end_time"]
        logging.info(f"Extracted time data - Start: {start_time}, End: {end_time}")

        api_summary = api_identifier_tool.get_api_identifier_summary(settings.ORGANIZATION_ID, user_query)
        api_id = api_summary["apiId"]
        api_name = api_summary["apiName"]
        logging.info(f"Identified API - ID: {api_id}, Name: {api_name}")

        tools_response = await select_tools(ToolRequest(user_query=user_query))
        selected_tools = tools_response["selected_tools"]
        logging.info(f"Selected tools: {selected_tools}")

        data = []
        for tool in selected_tools:
            logging.info(f"Executing tool: {tool}")
            if tool == "Error Data Tool":
                result = error_data_tool.get_error_data(api_id, start_time, end_time)
            elif tool == "Traffic Data Tool":
                result = traffic_data_tool.get_traffic_data(api_id, start_time, end_time)
            elif tool == "Summary Data Tool":
                result = summary_data_tool.get_summary_data(api_id, start_time, end_time)
            elif tool == "Latency Data Tool":
                result = latency_data_tool.get_latency_data(api_id, start_time, end_time)
            else:
                logging.warning(f"Unknown tool: {tool}")
                continue

            logging.info(f"Result from {tool}: {result}")
            data.append(result)

        logging.info("Generating response using ChatGPT API")
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.MODEL,
            messages=[{"role": "user", "content": f"User query: '{user_query}'. Data: {data}. Provide a response based on this information."}],
            max_tokens=10000
        )

        chat_response = response.choices[0].message.content
        logging.info(f"ChatGPT response: {chat_response}")
        return {"response": chat_response}

    except Exception as e:
        logging.error(f"An error occurred in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))