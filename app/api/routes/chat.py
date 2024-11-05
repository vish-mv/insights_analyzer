from fastapi import APIRouter, HTTPException
from app.api.routes.tools import select_tools, ToolRequest
from app.tools import api_identifier_tool, error_data_tool, traffic_data_tool, latency_data_tool, env_extractor
from openai import OpenAI
from app.config import get_settings
from app.tools.time_tool import get_time_data, TimeRequest
from pydantic import BaseModel
import logging
import json
import subprocess
import os
import sys
import datetime
from anthropic import Anthropic

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter()

class ChatRequest(BaseModel):
    user_query: str

def load_schema(tool_name: str):
    schema_path = os.path.join(os.path.dirname(__file__), "../../schemas", f"{tool_name}_schema.json")
    schema_path = os.path.normpath(schema_path)
    try:
        with open(schema_path, "r") as schema_file:
            return json.load(schema_file)
    except FileNotFoundError:
        logging.error(f"Schema file not found: {schema_path}")
        raise HTTPException(status_code=500, detail=f"Schema file not found: {schema_path}")

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        settings = get_settings()
        logging.info("Received chat request")

        user_query = request.user_query
        logging.info(f"User query: {user_query}")

        # Get time data
        time_data = get_time_data(TimeRequest(user_query=user_query))
        start_time = time_data["start_time"]
        end_time = time_data["end_time"]
        logging.info(f"Extracted time data - Start: {start_time}, End: {end_time}")

        # Get API information
        api_summary = api_identifier_tool.get_api_identifier_summary(settings.ORGANIZATION_ID, user_query)
        api_id = api_summary["apiId"]
        api_name = api_summary["apiName"]
        api_lst = api_summary["apiList"]
        logging.info(f"Identified API - ID: {api_id}, Name: {api_name}")

        env_summery = env_extractor.get_environment_summary(settings.ORGANIZATION_ID,user_query)
        env_name = env_summery["selectedEnvironment"]


        # Get selected tools
        tools_response = await select_tools(ToolRequest(user_query=user_query))
        selected_tools = tools_response["selected_tools"]
        logging.info(f"Selected tools: {selected_tools}")

        # Collect data from all tools with proper structure
        tool_data = {}
        tool_schemas = {}
        
        for tool in selected_tools:
            logging.info(f"Executing tool: {tool}")
            tool_key = tool.lower().replace(" ", "_")
            
            # Get the actual data
            if tool == "Error Data Tool":
                result = error_data_tool.get_error_data(api_id, start_time, end_time, env_name)
            elif tool == "Traffic Data Tool":
                result = traffic_data_tool.get_traffic_data(api_id, start_time, end_time, env_name)                
            elif tool == "Latency Data Tool":
                result = latency_data_tool.get_latency_data(api_id, start_time, end_time ,env_name)
            else:
                logging.warning(f"Unknown tool: {tool}")
                return {
                    "response": f"Sorry, I cannot process this request. Please insert a query about Insights such as Error Data, Traffic Data, Latency Data and etc.",
                    "chart": None
                }
            if not result or len(result) == 0:
                logging.info(f"No data returned from {tool} for the specified time period")
                return {
                    "response": f"Sorry, I couldn't find any data for the specified time period ({start_time} to {end_time}) for your query. Please try adjusting your time range or check if data exists for this.",
                    "chart": None
                }
            # Convert datetime objects to strings
            for item in result:
                for key, value in item.items():
                    if isinstance(value, datetime.datetime):
                        item[key] = value.isoformat()

            # Store the data and schema
            tool_data[tool_key] = [result]  # Wrap in list to match expected structure
            tool_schemas[tool_key] = load_schema(tool_key)
            logging.info(f"Collected data and schema for {tool}")

        # Generate analysis code using Anthropic
        logging.info("Requesting Claude to generate Python code for data analysis")
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        code_response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            system="""You are a Python code generator. Generate a Python function called data_analyzer that analyzes multiple datasets.""",
            messages=[
                {
                    "role": "user",
                    "content": f"""Generate a Python function that safely analyzes this data structure:
                    Data schemas: {json.dumps(tool_schemas)}
                    User query: {user_query}
                    Additional Info: In user query there maybe environment details. You dont have to analyze them in the code they are handled in the program. COde will recieve filtered darta.
                    
                    Important requirements:
                    1. Data comes in this nested structure: data['tool_name'][0] contains the array of records
                    2. Each record has 'AGG_WINDOW_START_TIME' that needs to be converted to datetime
                    3. Must handle empty or missing data gracefully
                    4. Instead of saving charts to files, convert them to base64 strings
                    5. Return format must be:
                        {{
                            "error": null or error message,
                            "insights": [list of strings],
                            "chart": base64_encoded_string or null,
                            "data": {{}}
                        }}
                    
                    Here's a template to start with:
                    
                    ```python
                    def data_analyzer(data):
                        try:
                            insights = []
                            chart_data = None
                            
                            # Validate input data
                            if not data or not isinstance(data, dict):
                                return {{"error": "Invalid input data", "insights": [], "chart": None, "data": {{}}}}
                            
                            # Initialize DataFrames dictionary
                            dfs = {{}}
                            
                            # Safely create DataFrames for each tool
                            for tool_name, tool_data in data.items():
                                try:
                                    if (tool_data and 
                                        isinstance(tool_data, list) and 
                                        len(tool_data) > 0 and 
                                        isinstance(tool_data[0], list) and
                                        len(tool_data[0]) > 0):
                                        
                                        # Create DataFrame from the inner list
                                        df = pd.DataFrame(tool_data[0])
                                        
                                        # Convert timestamp column
                                        df['AGG_WINDOW_START_TIME'] = pd.to_datetime(df['AGG_WINDOW_START_TIME'])
                                        df.set_index('AGG_WINDOW_START_TIME', inplace=True)
                                        
                                        dfs[tool_name] = df
                                        insights.append(f"Processed {{len(df)}} records from {{tool_name}}")
                                    else:
                                        insights.append(f"No valid data found for {{tool_name}}")
                                except Exception as e:
                                    insights.append(f"Error processing {{tool_name}}: {{str(e)}}")

                            # If visualization is needed, convert to base64
                            if len(dfs) > 0:  # Only create chart if we have data
                                try:
                                    plt.figure(figsize=(12, 6))
                                    # Your plotting code here...
                                    
                                    # Convert plot to base64
                                    import io
                                    import base64
                                    buf = io.BytesIO()
                                    plt.savefig(buf, format='png', bbox_inches='tight')
                                    buf.seek(0)
                                    chart_data = base64.b64encode(buf.getvalue()).decode('utf-8')
                                    plt.close()
                                except Exception as e:
                                    insights.append(f"Chart generation failed: {{str(e)}}")
                            
                            return {{
                                "error": None,
                                "insights": insights,
                                "chart": chart_data,
                                "data": {{}}  # Add your analysis data here
                            }}
                            
                        except Exception as e:
                            return {{
                                "error": f"Analysis failed: {{str(e)}}",
                                "insights": [],
                                "chart": None,
                                "data": {{}}
                            }}
                    ```
                    
                    Complete this function to analyze the data according to the user query. Make sure to:
                    1. Handle all potential errors
                    2. Generate meaningful insights
                    3. Create visualizations when appropriate
                    4. Return all numerical values as basic Python types (not numpy/pandas types)
                    """
                }
            ],
            max_tokens=8000
        )

        generated_code = code_response.content
        logging.info(f"Generated Python code: {generated_code}")

        # Extract code from Claude's response
        code = ""
        if isinstance(generated_code, list):
            for block in generated_code:
                if hasattr(block, 'text'):
                    text = block.text
                    if '```python' in text:
                        code = text.split('```python')[1].split('```')[0].strip()
                        break
        elif isinstance(generated_code, str):
            if '```python' in generated_code:
                code = generated_code.split('```python')[1].split('```')[0].strip()

        if not code:
            raise HTTPException(status_code=500, detail="Failed to extract code from Claude's response")

        logging.info(f"Cleaned Python code: {code}")

        # Prepare execution code
        execution_code = f"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pytz
import json
import io
import base64

def convert_to_serializable(obj):
    if isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {{type(obj)}} is not JSON serializable")

{code}

if __name__ == "__main__":
    try:
        # Load data
        data = json.loads('''{json.dumps(tool_data)}''')
        
        # Run analysis
        result = data_analyzer(data)
        
        # Ensure result is serializable
        print(json.dumps(result, default=convert_to_serializable, indent=2))
    except Exception as e:
        print(json.dumps({{
            "error": f"Execution failed: {{str(e)}}",
            "insights": [],
            "chart": None,
            "data": {{}}
        }}, indent=2))
"""

        # Save and execute the code
        with open("analyze_data.py", "w", encoding='utf-8') as code_file:
            code_file.write(execution_code)

        logging.info("Executing the generated Python code")
        analysis_result = subprocess.run(
            [sys.executable, "analyze_data.py"],
            capture_output=True,
            text=True
        )

        # Handle execution results
        logging.info(f"Subprocess stdout: {analysis_result.stdout}")
        if analysis_result.stderr:
            logging.error(f"Subprocess stderr: {analysis_result.stderr}")

        if analysis_result.returncode != 0:
            error_msg = f"Subprocess failed with return code {analysis_result.returncode}. Error: {analysis_result.stderr}"
            logging.error(error_msg)
            raise Exception(error_msg)

        analysis_result = json.loads(analysis_result.stdout)
        
        # Extract chart data and remove it from results sent to ChatGPT
        chart_data = analysis_result.pop("chart", None)
        
        # Generate final response using OpenAI with chart-free analysis
        logging.info("Generating final response using OpenAI")
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        final_response = openai_client.chat.completions.create(
            model=settings.OPEN_AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful assistant that provides detailed and clear summaries based on the user's query and the data provided.
                    Compare API IDs with the provided API list to use proper API names in your response.
                    Focus on insights from the combined analysis of multiple data sources.
                    You'll be provided with a environment name this alalysis result is based on  that purticular environment. (include it in answer for a better answer).
                    If the Analysis result is empty you should return No Data available for answer this question
                    Do not tell users how to do it just say you dont know beacuse no data politely
                    If the recieved environment name is SANDBOX you should return it to user as DEVELOPMENT not sandbox"""
                },
                {
                    "role": "user",
                    "content": f"User query: '{user_query}'. Analysis result: {json.dumps(analysis_result)}. API List: {api_lst}. Environment: {env_name}"
                }
            ],
            max_tokens=10000
        )



        chat_response = final_response.choices[0].message.content
        logging.info(f"ChatGPT response: {chat_response}")
        
        # Combine chat response with the previously extracted chart data
        response = {
            "response": chat_response,
            "chart": chart_data  # Add back the chart data for frontend
        }
        
        return response

    except Exception as e:
        logging.error(f"An error occurred in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))