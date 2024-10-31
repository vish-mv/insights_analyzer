from openai import OpenAI
from app.config import get_settings
from fastapi import HTTPException
from pydantic import BaseModel
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TimeRequest(BaseModel):
    user_query: str

def get_time_data(request: TimeRequest):
    try:
        logging.info("Starting get_time_data function")

        # Retrieve OpenAI API key from settings
        settings = get_settings()
        logging.info("Retrieved settings")

        client = OpenAI(api_key=settings.OPENAI_API_KEY)  # Set the API key
        logging.info("Initialized OpenAI client")

        current_time = datetime.datetime.now()
        logging.info(f"Current time: {current_time}")

        # Use the correct method to determine the start and end times
        response = client.chat.completions.create(
            model=settings.OPEN_AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are an assistant that extracts time from a given query.
                    User will provide you current date time according to that you need to give Start Date and end date.
                    Your answer should only contain two dates separated with a comma. (Example answer: 2024-01-31,2024-10-20)
                    And if the user's query doesn't have any info, start date will be yesterday. End date will be today."""
                },
                {
                    "role": "user",
                    "content": (
                        f"Given the user query: '{request.user_query}', "
                        "please extract the start and end times."
                        f"Current time is '{current_time}'"
                    )
                }
            ],
            max_tokens=100
        )
        logging.info("Received response from OpenAI")

        # Extract the content from the response
        response_content = response.choices[0].message.content.strip()
        logging.info(f"Response content: {response_content}")

        # Parse the response to extract the start and end times
        start_time, end_time = response_content.split(',')
        logging.info(f"Extracted start time: {start_time}, end time: {end_time}")

        return {"start_time": start_time, "end_time": end_time}

    except Exception as e:
        logging.error(f"An error occurred in get_time_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))