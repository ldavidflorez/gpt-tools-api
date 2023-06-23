import logger.app_logger as app_logger
from logger.app_logger_formatter import CustomFormatter
from fastapi import FastAPI
from http import HTTPStatus
import models.models as models
from database.database import engine
from routers import auth, user, service, tracker, gpt
from starlette.requests import Request
from starlette.responses import Response
from starlette.responses import JSONResponse
from starlette.background import BackgroundTask

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GPT-3 Tools API",
    description="GPT-3 Tools API",
    version="1.0.0"
)

formatter = CustomFormatter("%(asctime)s")
logger = app_logger.get_logger(__name__, formatter)
status_reasons = {x.value: x.name for x in list(HTTPStatus)}


async def cors_handler(request: Request, call_next):
    response: Response = await call_next(request)

    if request.method == "OPTIONS":
        response.status_code = 200

    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Origin"] = "https://aiwriter.sagioscode.com,https://gpt-tools-view.onrender.com"
    response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"

    return response


async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")

        excep_name = e.__class__.__name__

        if excep_name == "IntegrityError":
            return JSONResponse({"detail": "User already exists"}, status_code=409)

        return JSONResponse({"detail": "Internal server error"}, status_code=500)


def get_extra_info(request: Request, response: Response):
    return {"req": {
        "url": request.url.path,
        "headers": {"host": request.headers["host"],
                    "user-agent": request.headers["user-agent"],
                    "accept": request.headers["accept"]},
        "method": request.method,
        "httpVersion": request.scope["http_version"],
        "originalUrl": request.url.path
    },
        "res": {"statusCode": response.status_code, "body": {"statusCode": response.status_code,
                                                             "status": status_reasons.get(response.status_code)}}}


def write_log_data(request, response):
    logger.info(request.method + " " + request.url.path,
                extra={"extra_info": get_extra_info(request, response)})


async def log_request(request: Request, call_next):
    response = await call_next(request)
    response.background = BackgroundTask(write_log_data, request, response)
    return response


app.middleware("http")(cors_handler)
app.middleware("http")(catch_exceptions_middleware)
app.middleware("http")(log_request)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(service.router)
app.include_router(tracker.router)
app.include_router(gpt.router)


@app.get("/ping")
async def ping():
    return {"detail": "pong"}
