from fastapi import APIRouter, HTTPException
from app.api.models.query import QueryRequest, QueryResponse
from app.core.kusto_client import get_kusto_client
from app.config import get_settings
from datetime import datetime

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    try:
        client = get_kusto_client()
        settings = get_settings()

        start_time = datetime.now()
        response = client.execute(settings.KUSTO_DATABASE_NAME, request.query)
        execution_time = (datetime.now() - start_time).total_seconds()

        results = response.primary_results[0]
        columns = [col.column_name for col in results.columns]

        data = []
        for row in results:
            row_dict = {}
            for i, value in enumerate(row):
                row_dict[columns[i]] = value
            data.append(row_dict)

        return {
            "columns": columns,
            "data": data,
            "row_count": len(data),
            "execution_time": execution_time
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables")
async def get_tables():
    try:
        client = get_kusto_client()
        settings = get_settings()

        query = ".show tables"
        response = client.execute(settings.KUSTO_DATABASE_NAME, query)

        tables = [row["TableName"] for row in response.primary_results[0]]
        return {"tables": tables}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))