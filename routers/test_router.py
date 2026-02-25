from fastapi import APIRouter

router = APIRouter(prefix="/v1/test", tags=["테스트"])


@router.get("/ping")
async def ping():
    return {"message": "pong"}
