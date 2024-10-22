from openai import OpenAI
from app.config import get_settings
from fastapi import HTTPException
from pydantic import BaseModel
import datetime

class TimeRequest(BaseModel):
    user_query: str

def get_time_data(request: TimeRequest):
    try:
        # Retrieve OpenAI API key from settings
        settings = get_settings()
        client =OpenAI(settings.OPENAI_API_KEY)  # Set the API key
        current_time = datetime.datetime.now()

        # Use the correct method to determine the start and end times
        response = client.chhatCompletion.create(
            model=settings.MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a assistant that extract time from a given query
                    User will provide you current date time according to that you need to give Start Date and end date
                    Your answer should only contain two dates seperated with a comma. ((Example answer: 2024-01-31,2024-10-20))
                    And If users query doesn't have any info start date will be yesterday. End date will be Today"""
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
        
        # Extract the content from the response
        response_content = response.choices[0].message['content'].strip()

        # Parse the response to extract the start and end times
        # This depends on how the response is formatted
        start_time, end_time = response_content.split(',')

        return {start_time,end_time}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))