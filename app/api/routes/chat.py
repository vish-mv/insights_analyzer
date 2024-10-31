from fastapi import APIRouter, HTTPException
from app.api.routes.tools import select_tools, ToolRequest
from app.tools import api_identifier_tool, error_data_tool, traffic_data_tool, summary_data_tool, latency_data_tool
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

        time_data = get_time_data(TimeRequest(user_query=user_query))
        start_time = time_data["start_time"]
        end_time = time_data["end_time"]
        logging.info(f"Extracted time data - Start: {start_time}, End: {end_time}")

        api_summary = api_identifier_tool.get_api_identifier_summary(settings.ORGANIZATION_ID, user_query)
        api_id = api_summary["apiId"]
        api_name = api_summary["apiName"]
        api_lst = api_summary["apiList"]
        logging.info(f"Identified API - ID: {api_id}, Name: {api_name}")

        summary_result = summary_data_tool.get_summary_data(api_id, start_time, end_time)

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
            elif tool == "Latency Data Tool":
                result = latency_data_tool.get_latency_data(api_id, start_time, end_time)
            else:
                logging.warning(f"Unknown tool: {tool}")
                continue

            #Convert datetime objects to strings
            for item in result:
                for key, value in item.items():
                    if isinstance(value, datetime.datetime):
                        item[key] = value.isoformat()

            logging.info(f"Result from {tool}: {result}")
            data.append(result)

        # Load the schema for the selected tools
        schemas = {tool: load_schema(tool.lower().replace(" ", "_")) for tool in selected_tools}

        # Request Claude to generate Python code for data analysis
        logging.info("Requesting ChatGPT to generate Python code for data analysis")
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        code_response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            system="""You are a Python code generator. Generate a Python function to analyze the following data schemas. 
                    You will be provided by a query also by user. To answer that query need to generate a python code to analyze data.
                    The function should accept data as an argument and return the analysis result. Your result should only contains 
                    the python code for analysis. (Even No example usages ). Function of the oython code is always hould be 
                    data_analyzer(data) data will be the {data} we passed to execute this. 
                    While generating the code here are some instructions
                    1. If user has some api id name in the query it handled by the data passed code will get filtered data no need to filter in code
                    2. if time data in datetime64[ns, UTC] do not compare it with naive datetime object
                    3. DO not directly try to Objects like DataFrame (Pandas) to Json that will occur serializable errors 
                    """,
            messages=[
                {
                    "role": "user",
                    "content": f"""Data schemas: {json.dumps(schemas)}. Generate a Python full complete function to analyze data similar to this schema according to the below query.
                    User query is : {user_query} 
                    This generated code need o=to accept data like this and need to analyze them according to the query and give output.
                    Data are that passed to the code are in the given schema and passed real data will have data of each api calls made between two time points.
                    You can use python modules like pandas, numpy, etc. While ethis code executing data can be occur serializable issues and errros
                    Because some of data are date time as you can see. Make Sure code handles them and convert data if required.
                    Remember this is a template of what kind of data the python code is going to receive atual data's values will be changed.
                    Some common error that can occur listed down 
                    1.An error occurred while processing the data: Invalid comparison between dtype=datetime64[ns, UTC] and datetime
                    2.TypeError: Object of type DataFrame is not JSON serializable
                    3. error : "'datetime.datetime' object has no attribute 'tz_localize'"
                    4. error: "Invalid comparison between dtype=datetime64[ns, UTC] and datetime"
                    5. Invalid comparison between dtype=datetime64[ns, UTC] and Timestamp
                    Make sure to handle these no convertions if needed
                    If this user_query requested a plot or a chart, code should optionally need to generate that as well and save it as chart.png. 
                    """
                }
            ],
            max_tokens=8000
        )

        generated_code = code_response.content
        logging.info(f"Generated Python code: {generated_code}")
        if isinstance(generated_code, list):
            for block in generated_code:
                if hasattr(block, 'text') and block.text.startswith('```'):
                    # Extract code between triple backticks
                    code = block.text.split('```')[1]
                    # Remove the language identifier (e.g., 'python\n')
                    code = code.split('\n', 1)[1]
    
    # If the response is a string already containing markdown
        elif isinstance(generated_code, str):
            if '```' in generated_code:
                # Extract code between triple backticks
                code = generated_code.split('```')[1]
                # Remove the language identifier (e.g., 'python\n')
                code = code.split('\n', 1)[1]
                
        logging.info(f"Clened Python code: {code}")
        python_executable = sys.executable


        # Add a call to the generated function and print the result
        
        # Add a call to the generated function and print the result
        structured_data = {tool: data for tool in selected_tools}
        execution_code = f"""
{code}

if __name__ == "__main__":
    import json
    data = json.loads('''{json.dumps(structured_data)}''')
    result = data_analyzer(data)
    print(json.dumps(result, indent=2))
"""
        logging.info(os.path)
        if os.path.exists("chart.png"):
            logging.info("chart.png found in root directory, deleting it.")
            os.remove("chart.png")
        else:
            logging.info("chart.png not found in root directory.")
            
        # Save the execution code to a file
        with open("analyze_data.py", "w") as code_file:
            code_file.write(execution_code)

        # Execute the generated code with the actual data
        logging.info(f"Executing the generated Python code with interpreter: {python_executable}")
        analysis_result = subprocess.run(
            [python_executable, "analyze_data.py"],
            capture_output=True,
            text=True
        )

        # Log the subprocess output and errors
        logging.info(f"Subprocess stdout: {analysis_result.stdout}")
        if analysis_result.stderr:
            logging.error(f"Subprocess stderr: {analysis_result.stderr}")

        # Check if the subprocess execution was successful
        if analysis_result.returncode != 0:
            error_msg = f"Subprocess failed with return code {analysis_result.returncode}. Error: {analysis_result.stderr}"
            logging.error(error_msg)
            raise Exception(error_msg)

        # Use the analysis result in the final ChatGPT response
        logging.info("Generating final response using ChatGPT API")
        openAiClient= OpenAI(api_key=settings.OPENAI_API_KEY)
        final_response = openAiClient.chat.completions.create(
            model=settings.OPEN_AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful assistant that provides detailed and clear summaries based on the user's query and the data provided. You will be attached api ids and api names list by user
                    if the query requested names of apis or anything like that youll have to compare api in the data with the api id in the lst and give the api name then usr can understand better
                    Maybe user query have some chart plots requests yu dont need to do that those handled sperately"""
                },
                {
                    "role": "user",
                    "content": f"User query: '{user_query}'. Analysis result: {analysis_result.stdout}. API List: {api_lst}"
                }
            ],
            max_tokens=10000
        )

        chat_response = final_response.choices[0].message.content
        logging.info(f"ChatGPT response: {chat_response}")
        
        if os.path.exists("chart.png"):
            logging.info("chart.png found in root directory, attaching it to the response.")
            with open("chart.png", "rb") as image_file:
                image_data = image_file.read()
            response = {"response": chat_response, "chart": image_data.hex()}
        else:
            response = {"response": chat_response}
        
        return response

    except Exception as e:
        logging.error(f"An error occurred in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))