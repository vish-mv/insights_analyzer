from fastapi import APIRouter, HTTPException
import openai
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
        openai.api_key = settings.OPENAI_API_KEY

        # Use ChatGPT API to determine which tools to use
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Given the user query: '{user_query}', which of the following tools should be used? {tool_details}",
            max_tokens=150
        )

        selected_tools = response.choices[0].text.strip()
        return {"selected_tools": selected_tools}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))