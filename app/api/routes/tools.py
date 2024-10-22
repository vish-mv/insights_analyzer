from fastapi import APIRouter, HTTPException
from openai import OpenAI
import json
from app.config import get_settings

router = APIRouter()

# Load tool details from file
with open("app/tools/tool_details.json", "r") as file:
    tool_details = json.load(file)

@router.post("/tools")
async def select_tools(user_query: str):
    try:
        # Retrieve OpenAI API key from settings
        settings = get_settings()
        client = OpenAI(settings.OPENAI_API_KEY)

        # Use ChatGPT API to determine which tools to use
        response = client.chat.completions.create(
            model=settings.MODEL,
            messages=[{"role": "user", "content": f"Given the user query: '{user_query}', which of the following tools should be used? {tool_details}"}],
            max_tokens=1000
        )
        selected_tools = response.choices[0].text.strip()
        return {"selected_tools": selected_tools}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))