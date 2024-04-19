from fastapi import APIRouter
from fastapi import Request
from starlette import status
from starlette.responses import RedirectResponse

router = APIRouter(
    responses={404: {"description": "Not found"}}
)

@router.get('/')
async def loginpage(request: Request) :
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
