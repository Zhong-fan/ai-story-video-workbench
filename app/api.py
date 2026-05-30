from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import time
import uuid

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api_routes import register_routes
from .api_support import mount_spa
from .batch_generation_worker import start_batch_generation_worker, stop_batch_generation_worker
from .config import load_settings
from .db import init_db

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def create_app() -> FastAPI:
    _configure_logging()
    settings = load_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info("后端启动：开始初始化数据库和后台任务")
        init_db()
        start_batch_generation_worker(settings)
        logger.info("后端启动完成：host=%s port=%s llm_mode=%s", settings.app_host, settings.app_port, settings.llm_mode)
        try:
            yield
        finally:
            logger.info("后端关闭：正在停止后台任务")
            stop_batch_generation_worker()

    app = FastAPI(
        title="ChenFlow Workbench",
        version="1.0.0",
        description="面向创作者的中文小说生成与整理工作台。",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = uuid.uuid4().hex[:8]
        started_at = time.perf_counter()
        client = request.client.host if request.client else "-"
        logger.info("后端请求开始：id=%s method=%s path=%s client=%s", request_id, request.method, request.url.path, client)
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = round((time.perf_counter() - started_at) * 1000)
            logger.exception("后端请求异常：id=%s method=%s path=%s elapsed_ms=%s", request_id, request.method, request.url.path, elapsed_ms)
            raise
        elapsed_ms = round((time.perf_counter() - started_at) * 1000)
        logger.info(
            "后端请求完成：id=%s method=%s path=%s status=%s elapsed_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response

    router = APIRouter()
    register_routes(router, settings=settings)
    app.include_router(router)
    mount_spa(app, settings)
    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = load_settings()
    uvicorn.run("app.api:app", host=settings.app_host, port=settings.app_port, reload=False)


if __name__ == "__main__":
    main()
