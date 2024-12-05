from fastapi import APIRouter, status

router = APIRouter()  # Remove the tags configuration

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "message": "Application is running"
    }