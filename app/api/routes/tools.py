from fastapi import APIRouter, HTTPException
from openai import OpenAI
import json
from app.config import get_settings
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter()

# Load tool details from file
with open("app/tools/tool_details.json", "r") as file:
    tool_details = json.load(file)

class ToolRequest(BaseModel):
    user_query: str

# Update the select_tools function to better handle multiple tool selection
@router.post("/tools")
async def select_tools(request: ToolRequest):
    try:
        logging.info("Starting select_tools function")
        logging.info(f"User query: {request.user_query}")

        settings = get_settings()
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logging.info("Initialized OpenAI client")

        response = client.chat.completions.create(
            model=settings.OPEN_AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are an assistant that selects specific tools to grab data from a database.
                    You can select multiple tools if the query requires data from different sources.
                    Consider relationships between different types of data when making selections.
                    For example, if comparing errors with latency, select both Error Data Tool and Latency Data Tool.
                    If User requesting performance or overall performance the it should be all tools"""
                },
                {
                    "role": "user",
                    "content": (
                        f"Given the user query: '{request.user_query}', "
                        f"which of the following tools should be used? {tool_details}. "
                        "Please respond with a comma-separated list of tool names only."
                    )
                }
            ],
            max_tokens=2000
        )
        
        # Rest of the function remains the same        logging.info("Received response from OpenAI")

        response_content = response.choices[0].message.content.strip()
        logging.info(f"Response content: {response_content}")

        tool_names = [tool.strip() for tool in response_content.split(',')]
        logging.info(f"Selected tools: {tool_names}")

        return {"selected_tools": tool_names}

    except Exception as e:
        logging.error(f"An error occurred in select_tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))