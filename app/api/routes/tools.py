from fastapi import APIRouter, HTTPException
from openai import OpenAI
import json
from app.config import get_settings
from pydantic import BaseModel

router = APIRouter()

# Load tool details from file
with open("app/tools/tool_details.json", "r") as file:
    tool_details = json.load(file)

# Define a Pydantic model for the request body
class ToolRequest(BaseModel):
    user_query: str

@router.post("/tools")
async def select_tools(request: ToolRequest):
    try:
        # Retrieve OpenAI API key from settings
        settings = get_settings()
        client = OpenAI(api_key=settings.OPENAI_API_KEY)   # Set the API key

        # Use the correct method to determine which tools to use
        response = client.chat.completions.create(
            model=settings.MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                f"Given the user query: '{request.user_query}', "
                f"which of the following tools should be used? {tool_details}. "
                "Please respond with a comma-separated list of tool names only."
            )
                }],
            max_tokens=1000
        )
        
        # Extract the content from the response
        response_content = response.choices[0].message.content.strip()

        # Parse the response as a comma-separated list of tool names
        tool_names = [tool.strip() for tool in response_content.split(',')]

        return {"selected_tools": tool_names}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))